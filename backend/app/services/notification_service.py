from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Notification, User


def notify(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    *,
    type: str = "info",
    link: str | None = None,
) -> Notification:
    """Create a notification row. Caller commits."""
    notification = Notification(
        user_id=user_id, title=title, message=message, type=type, link=link
    )
    db.add(notification)
    return notification


def list_for(db: Session, user_id: int, unread_only: bool = False) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    return list(db.scalars(stmt.order_by(Notification.created_at.desc())))


def mark_read(db: Session, notification_id: int, current_user: User) -> Notification:
    notification = db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    return notification


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    return result.rowcount or 0
