from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import require_roles
from app.models import User, UserRole

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class LmsCourse(BaseModel):
    external_id: str
    title: str
    provider: str
    enrolled: int


class LmsSyncResponse(BaseModel):
    synced_at: str
    course_count: int
    courses: list[LmsCourse]


# Deterministic mock catalogue returned by the stub.
_MOCK_COURSES = [
    LmsCourse(external_id="LMS-101", title="Cloud Fundamentals", provider="Acme LMS", enrolled=42),
    LmsCourse(external_id="LMS-204", title="Secure Coding", provider="Acme LMS", enrolled=18),
    LmsCourse(external_id="LMS-330", title="Leadership Essentials", provider="Acme LMS", enrolled=27),
]


@router.post("/lms/sync", response_model=LmsSyncResponse, summary="Sync courses from an external LMS (stub)")
def lms_sync(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.super_admin)),
):
    audit_log(
        db,
        action="lms_sync",
        entity="integration",
        user_id=current_user.id,
        metadata={"course_count": len(_MOCK_COURSES)},
        request=request,
    )
    db.commit()
    # Timestamp is provided by the response layer; kept static-free for testability.
    from datetime import datetime, timezone

    return LmsSyncResponse(
        synced_at=datetime.now(timezone.utc).isoformat(),
        course_count=len(_MOCK_COURSES),
        courses=_MOCK_COURSES,
    )
