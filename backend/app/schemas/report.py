from datetime import datetime

from pydantic import BaseModel

from app.models.assessment import AssessmentResultStatus


class LabelCount(BaseModel):
    label: str
    count: int


class OrgReport(BaseModel):
    total_users: int
    total_trainers: int
    total_employees: int
    total_trainings: int
    active_trainings: int
    completed_trainings: int
    total_enrollments: int
    overall_attendance_rate: float
    assessment_pass_rate: float
    trainings_by_status: list[LabelCount]
    enrollments_by_department: list[LabelCount]
    attendance_by_status: list[LabelCount]


class TrainerTrainingRow(BaseModel):
    id: int
    title: str
    status: str
    enrollment_count: int


class TrainerReport(BaseModel):
    trainer_id: int
    name: str
    trainings_count: int
    sessions_count: int
    total_enrollments: int
    avg_attendance_rate: float
    assessments_count: int
    avg_assessment_score: float
    trainings: list[TrainerTrainingRow]


class EmployeeResultRow(BaseModel):
    assessment_title: str
    score: float
    max_score: float
    result: AssessmentResultStatus
    attempt_date: datetime


class EmployeeReport(BaseModel):
    user_id: int
    name: str
    attendance_pct: float
    enrolled_trainings: int
    completed_trainings: int
    assessments_taken: int
    avg_score: float
    pass_rate: float
    results: list[EmployeeResultRow]
