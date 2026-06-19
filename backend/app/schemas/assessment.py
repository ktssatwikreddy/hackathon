from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assessment import AssessmentResultStatus, QuestionType
from app.schemas.base import ORMModel


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_type: QuestionType
    options: list[str] | None = None
    correct_answer: str | None = None
    marks: int = Field(default=1, ge=1)
    order_index: int = 0


class QuestionOut(ORMModel):
    """Full question incl. the answer key — staff only."""

    id: int
    assessment_id: int
    question_text: str
    question_type: QuestionType
    options: list[str] | None
    correct_answer: str | None
    marks: int
    order_index: int


class QuestionPublic(ORMModel):
    """Question without the answer key — used when taking an assessment."""

    id: int
    assessment_id: int
    question_text: str
    question_type: QuestionType
    options: list[str] | None
    marks: int
    order_index: int


class AssessmentCreate(BaseModel):
    training_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    total_marks: int = Field(default=0, ge=0)
    passing_marks: int = Field(default=0, ge=0)
    duration_minutes: int = Field(default=30, ge=1)
    questions: list[QuestionCreate] = []


class AssessmentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    total_marks: int | None = Field(default=None, ge=0)
    passing_marks: int | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=1)


class AssessmentOut(ORMModel):
    id: int
    training_id: int
    title: str
    description: str | None
    total_marks: int
    passing_marks: int
    duration_minutes: int
    created_at: datetime
    question_count: int = 0


class QuestionAnalytics(QuestionOut):
    attempts: int
    correct: int
    accuracy: float


class SubmitRequest(BaseModel):
    # Map of question_id (as string) -> submitted answer.
    answers: dict[str, str]
    time_taken_seconds: int | None = Field(default=None, ge=0)


class ResultOut(ORMModel):
    id: int
    assessment_id: int
    user_id: int
    score: float
    max_score: float
    result: AssessmentResultStatus
    attempt_date: datetime
    time_taken_seconds: int | None
