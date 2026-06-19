from sqlalchemy.orm import Session

from app.models import Training, TrainingSession, TrainingStatus, User
from app.schemas.course import CourseCreate
from app.services.training_service import _validate_refs


def create_course(db: Session, payload: CourseCreate, current_user: User) -> Training:
    """Create a course (Training) and all of its scheduled sessions atomically."""
    _validate_refs(db, payload.trainer_id, payload.department_id)

    session_dates = [s.session_date for s in payload.sessions]
    training = Training(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        department_id=payload.department_id,
        trainer_id=payload.trainer_id,
        total_sessions=payload.total_sessions or len(payload.sessions),
        status=TrainingStatus.scheduled,
        start_date=min(session_dates),
        end_date=max(session_dates),
        created_by=current_user.id,
    )
    db.add(training)
    db.flush()

    for item in payload.sessions:
        db.add(
            TrainingSession(
                training_id=training.id,
                title=item.title,
                session_date=item.session_date,
                start_time=item.start_time,
                end_time=item.end_time,
                location=item.location,
                mode=item.mode,
                meeting_link=item.meeting_link,
            )
        )
    db.flush()
    return training
