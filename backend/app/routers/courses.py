from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import User, UserRole
from app.schemas.course import CourseCreate, CourseOut
from app.services import course_service

router = APIRouter(prefix="/api/courses", tags=["courses"])

admin_only = require_roles(UserRole.super_admin)


@router.post(
    "",
    response_model=CourseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a course (training + scheduled sessions) in one call",
)
def create_course(
    payload: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    training = course_service.create_course(db, payload, current_user)
    audit_log(
        db,
        action="create_course",
        entity="training",
        entity_id=training.id,
        user_id=current_user.id,
        metadata={"sessions": len(payload.sessions)},
        request=request,
    )
    db.commit()
    db.refresh(training)
    return training
