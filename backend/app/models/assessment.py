from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.types import enum_column


class QuestionType(str, Enum):
    mcq = "mcq"
    short = "short"
    scenario = "scenario"
    coding = "coding"


class AssessmentResultStatus(str, Enum):
    pass_ = "pass"
    fail = "fail"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    training_id: Mapped[int] = mapped_column(ForeignKey("trainings.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_marks: Mapped[int] = mapped_column(default=0)
    passing_marks: Mapped[int] = mapped_column(default=0)
    duration_minutes: Mapped[int] = mapped_column(default=30)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestion.order_index",
    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"), index=True
    )
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[QuestionType] = mapped_column(enum_column(QuestionType))
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[int] = mapped_column(default=1)
    order_index: Mapped[int] = mapped_column(default=0)

    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    score: Mapped[float] = mapped_column(Numeric(6, 2))
    max_score: Mapped[float] = mapped_column(Numeric(6, 2))
    result: Mapped[AssessmentResultStatus] = mapped_column(
        enum_column(AssessmentResultStatus)
    )
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    attempt_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    time_taken_seconds: Mapped[int | None] = mapped_column(nullable=True)
