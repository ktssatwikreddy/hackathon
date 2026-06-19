from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.base import Message
from app.schemas.session import SessionCreate, SessionOut, SessionUpdate
from app.services import session_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


@router.get("", response_model=list[SessionOut], summary="List sessions (filter by training/date range)")
def list_sessions(
    training_id: int | None = None,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return session_service.list_sessions(
        db, training_id=training_id, date_from=date_from, date_to=date_to
    )


@router.get("/{session_id}", response_model=SessionOut, summary="Get a single session")
def get_session(
    session_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return session_service.get_session(db, session_id)


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED, summary="Create a session")
def create_session(
    payload: SessionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    session = session_service.create_session(db, payload, current_user)
    db.flush()
    audit_log(db, action="create", entity="session", entity_id=session.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/{session_id}", response_model=SessionOut, summary="Update a session")
def update_session(
    session_id: int,
    payload: SessionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    session = session_service.update_session(db, session_id, payload, current_user)
    audit_log(db, action="update", entity="session", entity_id=session.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", response_model=Message, summary="Delete a session")
def delete_session(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    session_service.delete_session(db, session_id, current_user)
    audit_log(db, action="delete", entity="session", entity_id=session_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="Session deleted")
