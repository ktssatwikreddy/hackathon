from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models.training import SessionMode, SessionStatus
from app.schemas.base import ORMModel


class SessionCreate(BaseModel):
    training_id: int
    title: str = Field(min_length=1, max_length=200)
    session_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    mode: SessionMode = SessionMode.offline
    meeting_link: str | None = None


class SessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    session_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    mode: SessionMode | None = None
    meeting_link: str | None = None


class SessionOut(ORMModel):
    id: int
    training_id: int
    title: str
    session_date: date
    start_time: time | None
    end_time: time | None
    location: str | None
    mode: SessionMode
    meeting_link: str | None
    status: SessionStatus
    created_at: datetime
