from pydantic import BaseModel, Field

from app.models.assessment import QuestionType


class GenerateAssessmentRequest(BaseModel):
    training_id: int
    material_text: str = Field(min_length=1)
    num_questions: int = Field(default=5, ge=1, le=50)
    types: list[QuestionType] = [QuestionType.mcq, QuestionType.short]
    objectives: list[str] = []
    title: str | None = None
    passing_pct: int = Field(default=60, ge=0, le=100)


class GeneratedQuestion(BaseModel):
    question_text: str
    question_type: QuestionType
    options: list[str] | None = None
    correct_answer: str
    marks: int = Field(default=1, ge=1)


class GeneratedQuestionList(BaseModel):
    questions: list[GeneratedQuestion]


class AnalyzePerformanceRequest(BaseModel):
    user_id: int


class PerformanceInsight(BaseModel):
    user_id: int
    summary: str
    attendance_pct: float
    avg_score: float
    completed_trainings: int
    learning_gaps: list[str]
    skill_areas: list[str]
    recommendations: list[str]
