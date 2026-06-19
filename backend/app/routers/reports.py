from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.report import EmployeeReport, OrgReport, TrainerReport
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/org", response_model=OrgReport, summary="Org-wide report (admin)")
def org_report(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.super_admin)),
):
    return report_service.org_report(db)


@router.get("/trainer/{trainer_id}", response_model=TrainerReport, summary="Trainer report (self or admin)")
def trainer_report(
    trainer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.super_admin and current_user.id != trainer_id:
        raise HTTPException(status_code=403, detail="You can only view your own trainer report")
    return report_service.trainer_report(db, trainer_id)


@router.get("/employee/{user_id}", response_model=EmployeeReport, summary="Employee report (self or admin)")
def employee_report(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.super_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own report")
    return report_service.employee_report(db, user_id)
