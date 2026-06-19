from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import TrainingStatus, User, UserRole
from app.schemas.base import Message
from app.schemas.common import Paginated
from app.schemas.training import (
    BulkEnrollRequest,
    EnrollmentOut,
    TrainingCreate,
    TrainingOut,
    TrainingUpdate,
)
from app.services import training_service

router = APIRouter(prefix="/api/trainings", tags=["trainings"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


@router.get("", response_model=Paginated[TrainingOut], summary="List trainings (filter + paginate)")
def list_trainings(
    status_filter: TrainingStatus | None = Query(default=None, alias="status"),
    department_id: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = training_service.list_trainings(
        db, status_filter=status_filter, department_id=department_id, search=search, page=page, size=size
    )
    return Paginated.build([TrainingOut.model_validate(t) for t in items], total, page, size)


@router.get("/{training_id}", response_model=TrainingOut, summary="Get a single training")
def get_training(
    training_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return training_service.get_training(db, training_id)


@router.post("", response_model=TrainingOut, status_code=status.HTTP_201_CREATED, summary="Create a training")
def create_training(
    payload: TrainingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    training = training_service.create_training(db, payload, current_user)
    db.flush()
    audit_log(db, action="create", entity="training", entity_id=training.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(training)
    return training


@router.patch("/{training_id}", response_model=TrainingOut, summary="Update a training")
def update_training(
    training_id: int,
    payload: TrainingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    training = training_service.update_training(db, training_id, payload, current_user)
    audit_log(db, action="update", entity="training", entity_id=training.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(training)
    return training


@router.delete("/{training_id}", response_model=Message, summary="Delete a training")
def delete_training(
    training_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    training_service.delete_training(db, training_id, current_user)
    audit_log(db, action="delete", entity="training", entity_id=training_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="Training deleted")


# --- Enrollments (nested under a training) ---

@router.get("/{training_id}/enrollments", response_model=list[EnrollmentOut], summary="List enrollments for a training")
def list_enrollments(
    training_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return training_service.list_enrollments(db, training_id)


@router.post("/{training_id}/enrollments", response_model=list[EnrollmentOut], status_code=status.HTTP_201_CREATED, summary="Bulk-enroll users into a training")
def bulk_enroll(
    training_id: int,
    payload: BulkEnrollRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    created = training_service.bulk_enroll(db, training_id, payload.user_ids, current_user)
    audit_log(db, action="bulk_enroll", entity="training", entity_id=training_id, user_id=current_user.id, metadata={"count": len(created)}, request=request)
    db.commit()
    for e in created:
        db.refresh(e)
    return created


@router.delete("/{training_id}/enrollments/{user_id}", response_model=Message, summary="Remove a user from a training")
def remove_enrollment(
    training_id: int,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    training_service.remove_enrollment(db, training_id, user_id, current_user)
    audit_log(db, action="unenroll", entity="training", entity_id=training_id, user_id=current_user.id, metadata={"user_id": user_id}, request=request)
    db.commit()
    return Message(message="Enrollment removed")
