from datetime import datetime

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import EnrollmentRequestStatus, User, UserRole
from app.schemas.base import Message
from app.schemas.training import TrainingOut
from app.services import enrollment_request_service

router = APIRouter(prefix="/api/enrollment-requests", tags=["enrollment-requests"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


class CreateRequest(BaseModel):
    training_id: int


class RequestOut(BaseModel):
    id: int
    user_id: int
    training_id: int
    user_name: str
    training_title: str
    status: EnrollmentRequestStatus
    created_at: datetime


@router.get("/available", response_model=list[TrainingOut], summary="Courses I can request to join")
def available_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return enrollment_request_service.list_available_courses(db, current_user)


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED, summary="Request to join a course")
def create_request(
    payload: CreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enrollment_request_service.create_request(db, current_user, payload.training_id)
    audit_log(db, action="enrollment_request", entity="training", entity_id=payload.training_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="Request sent. A trainer or admin will review it.")


@router.get("", response_model=list[RequestOut], summary="Pending enrollment requests (staff)")
def list_requests(
    db: Session = Depends(get_db), current_user: User = Depends(staff_only)
):
    return enrollment_request_service.list_requests(db, current_user)


@router.post("/{request_id}/approve", response_model=Message, summary="Approve a request (enrolls the user)")
def approve(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    enrollment_request_service.decide(db, request_id, current_user, approve=True)
    audit_log(db, action="approve_enrollment", entity="enrollment_request", entity_id=request_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="Request approved and user enrolled.")


@router.post("/{request_id}/reject", response_model=Message, summary="Reject a request")
def reject(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    enrollment_request_service.decide(db, request_id, current_user, approve=False)
    audit_log(db, action="reject_enrollment", entity="enrollment_request", entity_id=request_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="Request rejected.")
