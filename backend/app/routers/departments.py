from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.base import Message
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services import department_service

router = APIRouter(prefix="/api/departments", tags=["departments"])

admin_only = require_roles(UserRole.super_admin)


@router.get("", response_model=list[DepartmentOut], summary="List all departments")
def list_departments(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return department_service.list_departments(db)


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED, summary="Create a department")
def create_department(
    payload: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    dept = department_service.create_department(db, payload)
    db.flush()
    audit_log(db, action="create", entity="department", entity_id=dept.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(dept)
    return dept


@router.patch("/{dept_id}", response_model=DepartmentOut, summary="Update a department")
def update_department(
    dept_id: int,
    payload: DepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    dept = department_service.update_department(db, dept_id, payload)
    audit_log(db, action="update", entity="department", entity_id=dept.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}", response_model=Message, summary="Delete a department")
def delete_department(
    dept_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    department_service.delete_department(db, dept_id)
    audit_log(db, action="delete", entity="department", entity_id=dept_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="Department deleted")
