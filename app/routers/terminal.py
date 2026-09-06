import asyncio
import json
import paramiko
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import SessionLocal
from app.models import Server, User
from app.auth import SECRET_KEY, ALGORITHM
from app.ssh_manager import SSHManager

router = APIRouter(tags=["Terminal"])

def get_user_from_token(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        return db.query(User).filter(User.username == username).first()
    except JWTError:
        return None

@router.websocket("/ws/terminal/{server_id}")
async def websocket_terminal(websocket: WebSocket, server_id: int, token: str = Query(...)):
    await websocket.accept()

    db = SessionLocal()
    try:
        user = get_user_from_token(token, db)
        if not user:
            await websocket.send_text("\r\n\x1b[31m[Fehler] Ungültiges Authentifizierungstoken.\x1b[0m\r\n")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            await websocket.send_text("\r\n\x1b[31m[Fehler] Server nicht gefunden.\x1b[0m\r\n")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.send_text(f"\r\n\x1b[35m[SSH] Verbinde mit {server.name} ({server.hostname})...\x1b[0m\r\n")

        try:
            ssh_client = SSHManager.get_ssh_client(server, timeout=10)
            chan = ssh_client.invoke_shell(term='xterm-256color', cols=100, rows=30)
            chan.settimeout(0.1)
        except Exception as e:
            await websocket.send_text(f"\r\n\x1b[31m[Fehler] SSH-Verbindung fehlgeschlagen: {str(e)}\x1b[0m\r\n")
            await websocket.close()
            return

        await websocket.send_text("\x1b[32m[SSH] Verbindung erfolgreich hergestellt!\x1b[0m\r\n\r\n")

        stop_event = asyncio.Event()

        # Task to read SSH output and send to WebSocket
        async def ssh_to_ws():
            loop = asyncio.get_event_loop()
            while not stop_event.is_set():
                try:
                    if chan.recv_ready():
                        data = await loop.run_in_executor(None, chan.recv, 4096)
                        if not data:
                            break
                        await websocket.send_text(data.decode('utf-8', errors='ignore'))
                    else:
                        await asyncio.sleep(0.02)
                except Exception:
                    await asyncio.sleep(0.05)

        # Task to read WebSocket input and send to SSH
        async def ws_to_ssh():
            loop = asyncio.get_event_loop()
            while not stop_event.is_set():
                try:
                    data = await websocket.receive_text()
                    if not data:
                        continue
                    
                    # Handle JSON control frames (e.g. terminal resize)
                    if data.startswith('{') and data.endswith('}'):
                        try:
                            msg = json.loads(data)
                            if msg.get('type') == 'resize':
                                cols = msg.get('cols', 100)
                                rows = msg.get('rows', 30)
                                chan.resize_pty(width=cols, height=rows)
                                continue
                        except Exception:
                            pass
                    
                    # Send standard keystrokes/data to SSH channel
                    await loop.run_in_executor(None, chan.send, data)
                except WebSocketDisconnect:
                    stop_event.set()
                    break
                except Exception:
                    stop_event.set()
                    break

        ssh_task = asyncio.create_task(ssh_to_ws())
        ws_task = asyncio.create_task(ws_to_ssh())

        done, pending = await asyncio.wait(
            [ssh_task, ws_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        stop_event.set()
        for t in pending:
            t.cancel()

        try:
            chan.close()
            ssh_client.close()
        except Exception:
            pass

    finally:
        db.close()
