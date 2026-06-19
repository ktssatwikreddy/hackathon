from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.base import Message
from app.schemas.notification import NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut], summary="List my notifications")
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return notification_service.list_for(db, current_user.id, unread_only=unread_only)


@router.post("/{notification_id}/read", response_model=NotificationOut, summary="Mark a notification read")
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = notification_service.mark_read(db, notification_id, current_user)
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/read-all", response_model=Message, summary="Mark all my notifications read")
def mark_all_read(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    count = notification_service.mark_all_read(db, current_user.id)
    db.commit()
    return Message(message=f"Marked {count} notifications as read")
