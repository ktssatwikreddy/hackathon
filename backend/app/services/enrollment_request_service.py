from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Enrollment,
    EnrollmentRequest,
    EnrollmentRequestStatus,
    EnrollmentStatus,
    Training,
    User,
    UserRole,
)
from app.services import notification_service
from app.services.training_service import get_training


def list_available_courses(db: Session, user: User) -> list[Training]:
    """Trainings the user is neither enrolled in nor has a pending request for."""
    enrolled = select(Enrollment.training_id).where(Enrollment.user_id == user.id)
    pending = select(EnrollmentRequest.training_id).where(
        EnrollmentRequest.user_id == user.id,
        EnrollmentRequest.status == EnrollmentRequestStatus.pending,
    )
    stmt = select(Training).where(
        Training.id.not_in(enrolled), Training.id.not_in(pending)
    ).order_by(Training.id.desc())
    return list(db.scalars(stmt))


def create_request(db: Session, user: User, training_id: int) -> EnrollmentRequest:
    training = get_training(db, training_id)

    if db.scalar(
        select(Enrollment).where(
            Enrollment.training_id == training_id, Enrollment.user_id == user.id
        )
    ):
        raise HTTPException(status_code=409, detail="You are already enrolled in this course")
    if db.scalar(
        select(EnrollmentRequest).where(
            EnrollmentRequest.training_id == training_id,
            EnrollmentRequest.user_id == user.id,
            EnrollmentRequest.status == EnrollmentRequestStatus.pending,
        )
    ):
        raise HTTPException(status_code=409, detail="You already have a pending request for this course")

    req = EnrollmentRequest(user_id=user.id, training_id=training_id)
    db.add(req)

    # Notify the course trainer + all admins.
    recipients: set[int] = set()
    if training.trainer_id:
        recipients.add(training.trainer_id)
    for admin in db.scalars(select(User).where(User.role == UserRole.super_admin)):
        recipients.add(admin.id)
    for rid in recipients:
        notification_service.notify(
            db,
            rid,
            title="New enrollment request",
            message=f"{user.name} requested to join '{training.title}'.",
            type="enrollment_request",
            link="/requests",
        )
    return req


def _can_decide(db: Session, current_user: User, training: Training) -> bool:
    if current_user.role == UserRole.super_admin:
        return True
    return current_user.role == UserRole.trainer and (
        training.trainer_id == current_user.id or training.created_by == current_user.id
    )


def list_requests(db: Session, current_user: User) -> list[dict]:
    """Pending requests visible to the caller (admin: all; trainer: own courses)."""
    rows = db.execute(
        select(EnrollmentRequest, User.name, Training.title, Training.trainer_id, Training.created_by)
        .join(User, EnrollmentRequest.user_id == User.id)
        .join(Training, EnrollmentRequest.training_id == Training.id)
        .where(EnrollmentRequest.status == EnrollmentRequestStatus.pending)
        .order_by(EnrollmentRequest.id.desc())
    ).all()
    out = []
    for req, user_name, title, trainer_id, created_by in rows:
        if current_user.role == UserRole.super_admin or (
            current_user.role == UserRole.trainer
            and (trainer_id == current_user.id or created_by == current_user.id)
        ):
            out.append(
                {
                    "id": req.id,
                    "user_id": req.user_id,
                    "training_id": req.training_id,
                    "user_name": user_name,
                    "training_title": title,
                    "status": req.status,
                    "created_at": req.created_at,
                }
            )
    return out


def decide(db: Session, request_id: int, current_user: User, approve: bool) -> EnrollmentRequest:
    req = db.get(EnrollmentRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != EnrollmentRequestStatus.pending:
        raise HTTPException(status_code=409, detail="This request has already been decided")

    training = get_training(db, req.training_id)
    if not _can_decide(db, current_user, training):
        raise HTTPException(status_code=403, detail="You cannot decide this request")

    req.decided_by = current_user.id
    req.decided_at = datetime.now(timezone.utc)

    if approve:
        req.status = EnrollmentRequestStatus.approved
        # Enroll if not already (first acceptance wins).
        if not db.scalar(
            select(Enrollment).where(
                Enrollment.training_id == req.training_id, Enrollment.user_id == req.user_id
            )
        ):
            db.add(
                Enrollment(
                    user_id=req.user_id,
                    training_id=req.training_id,
                    status=EnrollmentStatus.enrolled,
                )
            )
        notification_service.notify(
            db, req.user_id,
            title="Enrollment approved",
            message=f"You've been enrolled in '{training.title}'.",
            type="enrollment", link=f"/trainings/{training.id}",
        )
    else:
        req.status = EnrollmentRequestStatus.rejected
        notification_service.notify(
            db, req.user_id,
            title="Enrollment request declined",
            message=f"Your request to join '{training.title}' was declined.",
            type="enrollment_request",
        )
    return req
