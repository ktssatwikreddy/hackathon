from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.attendance import (
    AttendanceOut,
    BulkAttendanceRequest,
    MyAttendanceOut,
)
from app.schemas.qr import CheckinRequest, CheckinResponse
from app.services import attendance_service

router = APIRouter(prefix="/api/attendance", tags=["attendance"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


@router.get("", response_model=list[AttendanceOut], summary="List attendance for a session (staff)")
def list_attendance(
    session_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    return attendance_service.list_for_session(db, session_id, current_user)


@router.post("/bulk", response_model=list[AttendanceOut], status_code=status.HTTP_201_CREATED, summary="Bulk-mark attendance for a session")
def bulk_mark(
    payload: BulkAttendanceRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    created = attendance_service.bulk_mark(
        db, payload.session_id, payload.entries, current_user
    )
    audit_log(
        db,
        action="mark_attendance",
        entity="session",
        entity_id=payload.session_id,
        user_id=current_user.id,
        metadata={"count": len(created)},
        request=request,
    )
    db.commit()
    for record in created:
        db.refresh(record)
    return created


@router.get("/me", response_model=list[MyAttendanceOut], summary="View my own attendance")
def my_attendance(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return attendance_service.list_mine(db, current_user.id)


@router.post("/checkin", response_model=CheckinResponse, summary="Self check-in by scanning a session QR")
def checkin(
    payload: CheckinRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = attendance_service.checkin_by_token(db, payload.token, current_user)
    audit_log(db, action="qr_checkin", entity="session", entity_id=result["session_id"], user_id=current_user.id, request=request)
    db.commit()
    return result
