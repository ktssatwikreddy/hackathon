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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    training: Mapped[Training] = relationship(back_populates="sessions")
