import uuid
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Enrollment,
    SessionMaterial,
    TrainingSession,
    User,
    UserRole,
)
from app.services.session_service import get_session
from app.services.training_service import assert_training_access, get_training

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


def _assert_can_view(db: Session, session: TrainingSession, user: User) -> None:
    """Staff who own the training, or any enrolled user, may view materials."""
    if user.role == UserRole.super_admin:
        return
    training = get_training(db, session.training_id)
    if user.role == UserRole.trainer and (
        training.trainer_id == user.id or training.created_by == user.id
    ):
        return
    enrolled = db.scalar(
        select(Enrollment).where(
            Enrollment.training_id == session.training_id,
            Enrollment.user_id == user.id,
        )
    )
    if not enrolled:
        raise HTTPException(status_code=403, detail="You cannot view this session's materials")


def add_material(
    db: Session, session_id: int, title: str, filename: str, content_type: str | None,
    data: bytes, current_user: User,
) -> SessionMaterial:
    session = get_session(db, session_id)
    assert_training_access(current_user, get_training(db, session.training_id))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe = f"{uuid.uuid4().hex}_{Path(filename).name}"
    path = UPLOAD_DIR / safe
    path.write_bytes(data)

    material = SessionMaterial(
        session_id=session_id,
        title=title or filename,
        filename=filename,
        content_type=content_type,
        stored_path=str(path),
        uploaded_by=current_user.id,
    )
    db.add(material)
    return material


def list_materials(db: Session, session_id: int, current_user: User) -> list[SessionMaterial]:
    session = get_session(db, session_id)
    _assert_can_view(db, session, current_user)
    return list(
        db.scalars(
            select(SessionMaterial).where(SessionMaterial.session_id == session_id)
            .order_by(SessionMaterial.id.desc())
        )
    )


def get_material_for_download(db: Session, material_id: int, current_user: User) -> SessionMaterial:
    material = db.get(SessionMaterial, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    session = get_session(db, material.session_id)
    _assert_can_view(db, session, current_user)
    if not Path(material.stored_path).exists():
        raise HTTPException(status_code=404, detail="File missing on server")
    return material
