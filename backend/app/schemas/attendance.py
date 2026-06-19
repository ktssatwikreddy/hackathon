from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.attendance import AttendanceStatus
from app.schemas.base import ORMModel


class AttendanceEntry(BaseModel):
    user_id: int
    status: AttendanceStatus
    notes: str | None = None


class BulkAttendanceRequest(BaseModel):
    session_id: int
    entries: list[AttendanceEntry] = Field(min_length=1)


class AttendanceOut(ORMModel):
    id: int
    session_id: int
    user_id: int
    status: AttendanceStatus
    marked_by: int
    marked_at: datetime
    notes: str | None


class MyAttendanceOut(BaseModel):
    """Attendance enriched with session/training context for the employee view."""

    id: int
    session_id: int
    session_title: str
    session_date: date
    training_id: int
    training_title: str
    status: AttendanceStatus
    marked_at: datetime
    notes: str | None
