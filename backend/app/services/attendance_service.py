from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.models import (
    Attendance,
    AttendanceStatus,
    AttendanceToken,
    Enrollment,
    Training,
    TrainingSession,
    User,
)
from app.schemas.attendance import AttendanceEntry
from app.services.training_service import assert_training_access, get_training

# Statuses that count as "attended" for percentage calculations.
ATTENDED = {AttendanceStatus.present, AttendanceStatus.late}


def _get_session(db: Session, session_id: int) -> TrainingSession:
    session = db.get(TrainingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def list_for_session(db: Session, session_id: int, current_user: User) -> list[Attendance]:
    session = _get_session(db, session_id)
    assert_training_access(current_user, get_training(db, session.training_id))
    return list(
        db.scalars(select(Attendance).where(Attendance.session_id == session_id))
    )


def bulk_mark(
    db: Session, session_id: int, entries: list[AttendanceEntry], current_user: User
) -> list[Attendance]:
    session = _get_session(db, session_id)
    training = get_training(db, session.training_id)
    assert_training_access(current_user, training)

    enrolled_ids = {
        e.user_id
        for e in db.scalars(
            select(Enrollment).where(Enrollment.training_id == training.id)
        )
    }
    already_marked = {
        a.user_id
        for a in db.scalars(
            select(Attendance).where(Attendance.session_id == session_id)
        )
    }

    created: list[Attendance] = []
    for entry in entries:
        if entry.user_id not in enrolled_ids:
            raise HTTPException(
                status_code=422,
                detail=f"User {entry.user_id} is not enrolled in this training",
            )
        if entry.user_id in already_marked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance already recorded for user {entry.user_id} in this session",
            )
        record = Attendance(
            session_id=session_id,
            user_id=entry.user_id,
            status=entry.status,
            marked_by=current_user.id,
            notes=entry.notes,
        )
        db.add(record)
        created.append(record)
    return created


def checkin_by_token(db: Session, token: str, current_user: User) -> dict:
    """Self check-in via a scanned QR token. Idempotent on re-scan."""
    # 1. Validate the signed token (type + expiry).
    try:
        claims = decode_token(token, expected_type="attendance")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired QR code")

    # 2. The jti must still be active (not rotated/revoked).
    jti = claims.get("jti")
    row = db.scalar(select(AttendanceToken).where(AttendanceToken.jti == jti))
    if not row or not row.is_active:
        raise HTTPException(status_code=410, detail="This QR code is no longer valid")

    # 3. Resolve the session.
    session_id = int(claims["sub"])
    session = db.get(TrainingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    training = db.get(Training, session.training_id)

    # 4. Caller must be enrolled in the training.
    enrolled = db.scalar(
        select(Enrollment).where(
            Enrollment.training_id == session.training_id,
            Enrollment.user_id == current_user.id,
        )
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this training")

    # 5. Idempotent upsert.
    existing = db.scalar(
        select(Attendance).where(
            Attendance.session_id == session_id, Attendance.user_id == current_user.id
        )
    )
    already = existing is not None
    if not already:
        db.add(
            Attendance(
                session_id=session_id,
                user_id=current_user.id,
                status=AttendanceStatus.present,
                marked_by=current_user.id,
                notes="self check-in via QR",
            )
        )

    return {
        "status": "present",
        "session_id": session_id,
        "training_title": training.title if training else "",
        "already_marked": already,
    }


def list_mine(db: Session, user_id: int) -> list[dict]:
    rows = db.execute(
        select(Attendance, TrainingSession, Training)
        .join(TrainingSession, Attendance.session_id == TrainingSession.id)
        .join(Training, TrainingSession.training_id == Training.id)
        .where(Attendance.user_id == user_id)
        .order_by(TrainingSession.session_date.desc())
    ).all()
    return [
        {
            "id": att.id,
            "session_id": sess.id,
            "session_title": sess.title,
            "session_date": sess.session_date,
            "training_id": tr.id,
            "training_title": tr.title,
            "status": att.status,
            "marked_at": att.marked_at,
            "notes": att.notes,
        }
        for att, sess, tr in rows
    ]


def attendance_percentage(
    db: Session, user_id: int, training_id: int | None = None
) -> float:
    """Percentage of a user's marked sessions where they attended.

    Reused by reports and the AI performance graph.
    """
    stmt = select(Attendance.status).where(Attendance.user_id == user_id)
    if training_id is not None:
        stmt = (
            stmt.join(TrainingSession, Attendance.session_id == TrainingSession.id)
            .where(TrainingSession.training_id == training_id)
        )
    statuses = list(db.scalars(stmt))
    if not statuses:
        return 0.0
    attended = sum(1 for s in statuses if s in ATTENDED)
    return round(attended / len(statuses) * 100, 1)
