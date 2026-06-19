from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Department, User, UserRole
from app.schemas.user import UserCreate, UserUpdate


def list_users(
    db: Session,
    *,
    role: UserRole | None = None,
    department_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[User], int]:
    conditions = []
    if role is not None:
        conditions.append(User.role == role)
    if department_id is not None:
        conditions.append(User.department_id == department_id)
    if search:
        like = f"%{search}%"
        conditions.append(
            or_(User.name.ilike(like), User.email.ilike(like), User.employee_code.ilike(like))
        )

    base = select(User)
    if conditions:
        base = base.where(*conditions)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = list(
        db.scalars(
            base.order_by(User.id).limit(size).offset((page - 1) * size)
        )
    )
    return items, total


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _validate_department(db: Session, department_id: int | None) -> None:
    if department_id is not None and not db.get(Department, department_id):
        raise HTTPException(status_code=422, detail="department_id does not exist")


def create_user(db: Session, payload: UserCreate) -> User:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.scalar(select(User).where(User.employee_code == payload.employee_code)):
        raise HTTPException(status_code=409, detail="employee_code already in use")
    _validate_department(db, payload.department_id)

    user = User(
        employee_code=payload.employee_code,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department_id=payload.department_id,
        phone=payload.phone,
        designation=payload.designation,
        joining_date=payload.joining_date,
    )
    db.add(user)
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    user = get_user(db, user_id)
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"] != user.email:
        if db.scalar(select(User).where(User.email == data["email"])):
            raise HTTPException(status_code=409, detail="Email already registered")
    if "department_id" in data:
        _validate_department(db, data["department_id"])
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))

    for key, value in data.items():
        setattr(user, key, value)
    return user


def delete_user(db: Session, user_id: int, current_user: User) -> None:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    user = get_user(db, user_id)
    db.delete(user)
