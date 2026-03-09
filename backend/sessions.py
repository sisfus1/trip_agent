import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.auth import get_current_user
from backend.database import get_db

session_router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@session_router.post("", response_model=schemas.SessionResponse)
def create_session(
    body: schemas.SessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_session = models.ChatSession(
        id=uuid.uuid4().hex[:12],
        user_id=current_user.id,
        title=body.title,
        is_persistent=body.is_persistent,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@session_router.get("", response_model=list[schemas.SessionResponse])
def list_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == current_user.id)
        .order_by(models.ChatSession.created_at.desc())
        .limit(50)
        .all()
    )


@session_router.delete("/{session_id}")
def delete_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"ok": True}


@session_router.patch("/{session_id}", response_model=schemas.SessionResponse)
def update_session_title(
    session_id: str,
    body: schemas.SessionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if body.title is not None:
        session.title = body.title
    db.commit()
    db.refresh(session)
    return session
