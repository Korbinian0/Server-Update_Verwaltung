from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Server, User, UpdateLog
from app.schemas import LogResponse
from app.auth import get_current_user
from app.update_manager import UpdateManager

router = APIRouter(prefix="/api/updates", tags=["Updates"])

@router.post("/{server_id}/check")
def check_server_updates(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")

    res = UpdateManager.check_updates(db, server)
    return res

@router.post("/check-all")
def check_all_updates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    servers = db.query(Server).all()
    results = []
    for s in servers:
        res = UpdateManager.check_updates(db, s)
        results.append({"server_id": s.id, "name": s.name, "result": res})
    return {"status": "complete", "results": results}

@router.post("/{server_id}/run")
def run_server_updates(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")

    res = UpdateManager.run_updates(db, server)
    return res

@router.get("/{server_id}/logs", response_model=List[LogResponse])
def get_server_logs(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server nicht gefunden")

    return db.query(UpdateLog).filter(UpdateLog.server_id == server_id).order_by(UpdateLog.id.desc()).limit(20).all()
