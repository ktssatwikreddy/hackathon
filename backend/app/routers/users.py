from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.base import Message
from app.schemas.common import Paginated
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["users"])

admin_only = require_roles(UserRole.super_admin)


@router.get("", response_model=Paginated[UserOut], summary="List users (filter + paginate)")
def list_users(
    role: UserRole | None = None,
    department_id: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = user_service.list_users(
        db, role=role, department_id=department_id, search=search, page=page, size=size
    )
    return Paginated.build([UserOut.model_validate(u) for u in items], total, page, size)


@router.get("/{user_id}", response_model=UserOut, summary="Get a single user")
def get_user(
    user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return user_service.get_user(db, user_id)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Create a user")
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    user = user_service.create_user(db, payload)
    db.flush()
    audit_log(db, action="create", entity="user", entity_id=user.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserOut, summary="Update a user")
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    user = user_service.update_user(db, user_id, payload)
    audit_log(db, action="update", entity="user", entity_id=user.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=Message, summary="Delete a user")
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    user_service.delete_user(db, user_id, current_user)
    audit_log(db, action="delete", entity="user", entity_id=user_id, user_id=current_user.id, request=request)
    db.commit()
    return Message(message="User deleted")
