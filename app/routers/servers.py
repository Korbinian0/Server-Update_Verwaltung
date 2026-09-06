from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Server, User
from app.schemas import ServerCreate, ServerUpdate, ServerResponse
from app.auth import get_current_user
from app.ssh_manager import SSHManager

router = APIRouter(prefix="/api/servers", tags=["Servers"])

@router.get("", response_model=List[ServerResponse])
def list_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Server).order_by(Server.id.desc()).all()

@router.post("", response_model=ServerResponse)
def create_server(
    server_in: ServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = Server(**server_in.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    return server

@router.get("/{server_id}", response_model=ServerResponse)
def get_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")
    return server

@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    server_in: ServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")

    update_data = server_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)

    db.commit()
    db.refresh(server)
    return server

@router.delete("/{server_id}")
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")
    
    db.delete(server)
    db.commit()
    return {"message": "Server erfolgreich gelöscht"}

@router.post("/{server_id}/test-connection")
def test_connection(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")

    success, message = SSHManager.test_connection(server)
    if not success:
        return {"success": False, "message": message}
    return {"success": True, "message": message}
