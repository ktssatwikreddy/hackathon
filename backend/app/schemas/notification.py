from datetime import datetime

from app.schemas.base import ORMModel


class NotificationOut(ORMModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    link: str | None
    is_read: bool
    created_at: datetime
