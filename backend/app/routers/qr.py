from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import User, UserRole
from app.schemas.base import Message
from app.schemas.qr import QrTokenOut
from app.schemas.session import SessionOut
from app.services import qr_service

router = APIRouter(prefix="/api/sessions", tags=["qr-attendance"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


@router.post("/{session_id}/end", response_model=SessionOut, summary="Mark a session ended")
def end_session(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    session = qr_service.end_session(db, session_id, current_user)
    audit_log(db, action="end_session", entity="session", entity_id=session_id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/qr", response_model=QrTokenOut, status_code=status.HTTP_201_CREATED, summary="Generate (or rotate) the attendance QR for a session")
def generate_qr(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    result = qr_service.generate_qr(db, session_id, current_user)
    audit_log(db, action="generate_qr", entity="session", entity_id=session_id, user_id=current_user.id, request=request)
    db.commit()
    return result


@router.get("/{session_id}/qr", response_model=QrTokenOut, summary="Get the current active QR for a session")
def get_qr(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    return qr_service.get_active_qr(db, session_id, current_user)


@router.delete("/{session_id}/qr", response_model=Message, summary="Revoke the active QR for a session")
def revoke_qr(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    count = qr_service.revoke_qr(db, session_id, current_user)
    audit_log(db, action="revoke_qr", entity="session", entity_id=session_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message=f"Revoked {count} active QR token(s)")
