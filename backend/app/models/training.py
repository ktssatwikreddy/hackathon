from datetime import date, datetime, time
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.types import enum_column


class TrainingStatus(str, Enum):
    draft = "draft"
    scheduled = "scheduled"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class EnrollmentStatus(str, Enum):
    enrolled = "enrolled"
    withdrawn = "withdrawn"
    completed = "completed"


class SessionMode(str, Enum):
    online = "online"
    offline = "offline"
    hybrid = "hybrid"


class SessionStatus(str, Enum):
    scheduled = "scheduled"
    ended = "ended"
    cancelled = "cancelled"


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    trainer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), index=True, nullable=True
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    capacity: Mapped[int | None] = mapped_column(nullable=True)
    total_sessions: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[TrainingStatus] = mapped_column(
        enum_column(TrainingStatus), default=TrainingStatus.draft
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["TrainingSession"]] = relationship(
        back_populates="training", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="training", cascade="all, delete-orphan"
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "training_id", name="uq_enrollment_user_training"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id"), index=True)
    enrolled_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        enum_column(EnrollmentStatus), default=EnrollmentStatus.enrolled
    )

    training: Mapped[Training] = relationship(back_populates="enrollments")


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    session_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[SessionMode] = mapped_column(
        enum_column(SessionMode), default=SessionMode.offline
    )
    meeting_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        enum_column(SessionStatus), default=SessionStatus.scheduled
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    training: Mapped[Training] = relationship(back_populates="sessions")


class SessionMaterial(Base):
    """A file/resource a trainer attaches to a session; enrolled users can view it."""

    __tablename__ = "session_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("training_sessions.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stored_path: Mapped[str] = mapped_column(String(500))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AttendanceToken(Base):
    """A QR attendance token issued for a session (the token value is a signed JWT).

    Persisting the jti lets us revoke/rotate a session's active QR before expiry.
    """

    __tablename__ = "attendance_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("training_sessions.id"), index=True
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
