import base64
import io
import uuid
from datetime import datetime, timedelta, timezone

import qrcode
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_attendance_token
from app.models import AttendanceToken, TrainingSession, User
from app.services.session_service import get_session
from app.services.training_service import assert_training_access, get_training


def _render_qr_png(data: str) -> str:
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def _assert_session_access(db: Session, session_id: int, current_user: User) -> TrainingSession:
    session = get_session(db, session_id)
    assert_training_access(current_user, get_training(db, session.training_id))
    return session


def end_session(db: Session, session_id: int, current_user: User) -> TrainingSession:
    from app.models import SessionStatus

    session = _assert_session_access(db, session_id, current_user)
    session.status = SessionStatus.ended
    return session


def generate_qr(db: Session, session_id: int, current_user: User) -> dict:
    session = _assert_session_access(db, session_id, current_user)
    settings = get_settings()

    # Only one active QR per session — deactivate any prior ones.
    db.execute(
        update(AttendanceToken)
        .where(AttendanceToken.session_id == session_id, AttendanceToken.is_active.is_(True))
        .values(is_active=False)
    )

    jti = uuid.uuid4().hex
    ttl = settings.attendance_token_ttl_minutes
    token = create_attendance_token(session_id, jti, ttl)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl)

    db.add(
        AttendanceToken(
            session_id=session_id,
            jti=jti,
            token=token,
            created_by=current_user.id,
            expires_at=expires_at,
            is_active=True,
        )
    )

    checkin_url = f"{settings.frontend_base_url}/attend/{token}"
    return {
        "token": token,
        "checkin_url": checkin_url,
        "qr_png_base64": _render_qr_png(checkin_url),
        "expires_at": expires_at,
        "session_id": session_id,
    }


def _active_row(db: Session, session_id: int) -> AttendanceToken | None:
    now = datetime.now(timezone.utc)
    row = db.scalar(
        select(AttendanceToken)
        .where(
            AttendanceToken.session_id == session_id,
            AttendanceToken.is_active.is_(True),
        )
        .order_by(AttendanceToken.id.desc())
    )
    if row and _aware(row.expires_at) > now:
        return row
    return None


def _aware(dt: datetime) -> datetime:
    """SQLite returns naive datetimes; treat them as UTC."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def get_active_qr(db: Session, session_id: int, current_user: User) -> dict:
    _assert_session_access(db, session_id, current_user)
    row = _active_row(db, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="No active QR for this session")
    settings = get_settings()
    checkin_url = f"{settings.frontend_base_url}/attend/{row.token}"
    return {
        "token": row.token,
        "checkin_url": checkin_url,
        "qr_png_base64": _render_qr_png(checkin_url),
        "expires_at": _aware(row.expires_at),
        "session_id": session_id,
    }


def revoke_qr(db: Session, session_id: int, current_user: User) -> int:
    _assert_session_access(db, session_id, current_user)
    result = db.execute(
        update(AttendanceToken)
        .where(AttendanceToken.session_id == session_id, AttendanceToken.is_active.is_(True))
        .values(is_active=False)
    )
    return result.rowcount or 0
