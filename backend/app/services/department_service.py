from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Department, User
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def list_departments(db: Session) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)))


def get_department(db: Session, dept_id: int) -> Department:
    dept = db.get(Department, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    if db.scalar(select(Department).where(Department.name == payload.name)):
        raise HTTPException(status_code=409, detail="Department name already exists")
    dept = Department(name=payload.name, description=payload.description)
    db.add(dept)
    return dept


def update_department(db: Session, dept_id: int, payload: DepartmentUpdate) -> Department:
    dept = get_department(db, dept_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != dept.name:
        if db.scalar(select(Department).where(Department.name == data["name"])):
            raise HTTPException(status_code=409, detail="Department name already exists")
    for key, value in data.items():
        setattr(dept, key, value)
    return dept


def delete_department(db: Session, dept_id: int) -> None:
    dept = get_department(db, dept_id)
    # Detach users so we don't leave dangling references.
    for user in db.scalars(select(User).where(User.department_id == dept_id)):
        user.department_id = None
    db.delete(dept)
