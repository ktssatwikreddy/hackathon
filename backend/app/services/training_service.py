from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Department,
    Enrollment,
    EnrollmentStatus,
    Training,
    TrainingStatus,
    User,
    UserRole,
)
from app.schemas.training import TrainingCreate, TrainingUpdate
from app.services import notification_service


def assert_training_access(user: User, training: Training) -> None:
    """Object-level check: admin always; trainer only for trainings they own."""
    if user.role == UserRole.super_admin:
        return
    if user.role == UserRole.trainer and (
        training.trainer_id == user.id or training.created_by == user.id
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this training",
    )


def get_training(db: Session, training_id: int) -> Training:
    training = db.get(Training, training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training


def list_trainings(
    db: Session,
    *,
    status_filter: TrainingStatus | None = None,
    department_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Training], int]:
    conditions = []
    if status_filter is not None:
        conditions.append(Training.status == status_filter)
    if department_id is not None:
        conditions.append(Training.department_id == department_id)
    if search:
        conditions.append(Training.title.ilike(f"%{search}%"))

    base = select(Training)
    if conditions:
        base = base.where(*conditions)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = list(
        db.scalars(base.order_by(Training.id.desc()).limit(size).offset((page - 1) * size))
    )
    return items, total


def _validate_refs(db: Session, trainer_id: int | None, department_id: int | None) -> None:
    if department_id is not None and not db.get(Department, department_id):
        raise HTTPException(status_code=422, detail="department_id does not exist")
    if trainer_id is not None:
        trainer = db.get(User, trainer_id)
        if not trainer or trainer.role not in (UserRole.trainer, UserRole.super_admin):
            raise HTTPException(status_code=422, detail="trainer_id must be a trainer")


def create_training(db: Session, payload: TrainingCreate, current_user: User) -> Training:
    data = payload.model_dump()
    # Only admins may assign an arbitrary trainer. A trainer creating a
    # training is implicitly its trainer.
    if current_user.role == UserRole.trainer:
        data["trainer_id"] = current_user.id
    _validate_refs(db, data.get("trainer_id"), data.get("department_id"))

    training = Training(**data, created_by=current_user.id)
    db.add(training)
    return training


def update_training(
    db: Session, training_id: int, payload: TrainingUpdate, current_user: User
) -> Training:
    training = get_training(db, training_id)
    assert_training_access(current_user, training)
    data = payload.model_dump(exclude_unset=True)

    # Reassigning the trainer is an admin-only action.
    if "trainer_id" in data and current_user.role != UserRole.super_admin:
        raise HTTPException(
            status_code=403, detail="Only a super admin can reassign the trainer"
        )
    _validate_refs(db, data.get("trainer_id"), data.get("department_id"))
    for key, value in data.items():
        setattr(training, key, value)
    return training


def delete_training(db: Session, training_id: int, current_user: User) -> None:
    training = get_training(db, training_id)
    assert_training_access(current_user, training)
    db.delete(training)


# --- Enrollments ---

def list_enrollments(db: Session, training_id: int) -> list[Enrollment]:
    get_training(db, training_id)
    return list(
        db.scalars(select(Enrollment).where(Enrollment.training_id == training_id))
    )


def bulk_enroll(
    db: Session, training_id: int, user_ids: list[int], current_user: User
) -> list[Enrollment]:
    training = get_training(db, training_id)
    assert_training_access(current_user, training)

    existing = {
        e.user_id
        for e in db.scalars(
            select(Enrollment).where(Enrollment.training_id == training_id)
        )
    }
    created: list[Enrollment] = []
    for uid in dict.fromkeys(user_ids):  # de-dupe, preserve order
        if uid in existing:
            continue
        user = db.get(User, uid)
        if not user:
            raise HTTPException(status_code=422, detail=f"User {uid} does not exist")
        enrollment = Enrollment(
            user_id=uid, training_id=training_id, status=EnrollmentStatus.enrolled
        )
        db.add(enrollment)
        created.append(enrollment)
        notification_service.notify(
            db,
            uid,
            title="You've been enrolled in a training",
            message=f"You are now enrolled in '{training.title}'.",
            type="enrollment",
            link=f"/trainings/{training_id}",
        )
    return created


def remove_enrollment(
    db: Session, training_id: int, user_id: int, current_user: User
) -> None:
    training = get_training(db, training_id)
    assert_training_access(current_user, training)
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.training_id == training_id, Enrollment.user_id == user_id
        )
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(enrollment)
