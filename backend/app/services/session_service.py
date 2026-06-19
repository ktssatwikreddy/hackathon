from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TrainingSession, User
from app.schemas.session import SessionCreate, SessionUpdate
from app.services.training_service import assert_training_access, get_training


def get_session(db: Session, session_id: int) -> TrainingSession:
    session = db.get(TrainingSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def list_sessions(
    db: Session,
    *,
    training_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[TrainingSession]:
    conditions = []
    if training_id is not None:
        conditions.append(TrainingSession.training_id == training_id)
    if date_from is not None:
        conditions.append(TrainingSession.session_date >= date_from)
    if date_to is not None:
        conditions.append(TrainingSession.session_date <= date_to)
    stmt = select(TrainingSession)
    if conditions:
        stmt = stmt.where(*conditions)
    return list(db.scalars(stmt.order_by(TrainingSession.session_date)))


def create_session(db: Session, payload: SessionCreate, current_user: User) -> TrainingSession:
    training = get_training(db, payload.training_id)
    assert_training_access(current_user, training)
    session = TrainingSession(**payload.model_dump())
    db.add(session)
    return session


def update_session(
    db: Session, session_id: int, payload: SessionUpdate, current_user: User
) -> TrainingSession:
    session = get_session(db, session_id)
    assert_training_access(current_user, get_training(db, session.training_id))
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, key, value)
    return session


def delete_session(db: Session, session_id: int, current_user: User) -> None:
    session = get_session(db, session_id)
    assert_training_access(current_user, get_training(db, session.training_id))
    db.delete(session)
