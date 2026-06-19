from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.assessment_chain import generate_questions
from app.ai.groq_client import GroqService
from app.ai.performance_graph import analyze_performance
from app.models import Assessment, Enrollment, Training, User, UserRole
from app.schemas.ai import GenerateAssessmentRequest
from app.schemas.assessment import AssessmentCreate, QuestionCreate
from app.services import assessment_service
from app.services.training_service import assert_training_access, get_training


def generate_assessment(
    db: Session, groq: GroqService, payload: GenerateAssessmentRequest, current_user: User
) -> Assessment:
    training = get_training(db, payload.training_id)
    assert_training_access(current_user, training)

    generated = generate_questions(
        groq,
        material_text=payload.material_text,
        num_questions=payload.num_questions,
        types=[t.value for t in payload.types],
        objectives=payload.objectives,
        topic=training.title,
    )

    questions = [
        QuestionCreate(
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            correct_answer=q.correct_answer,
            marks=q.marks,
            order_index=i,
        )
        for i, q in enumerate(generated.questions)
    ]
    total = sum(q.marks for q in questions)
    create = AssessmentCreate(
        training_id=payload.training_id,
        title=payload.title or f"AI Assessment — {training.title}",
        description="Generated from training material via AI.",
        total_marks=total,
        passing_marks=round(total * payload.passing_pct / 100),
        duration_minutes=max(10, len(questions) * 2),
        questions=questions,
    )
    return assessment_service.create_assessment(db, create, current_user)


def assert_can_view_performance(db: Session, current_user: User, target_user_id: int) -> None:
    if current_user.role == UserRole.super_admin:
        return
    if current_user.id == target_user_id:
        return
    if current_user.role == UserRole.trainer:
        # Trainee = enrolled in any training owned by this trainer.
        owned = db.scalar(
            select(Enrollment.id)
            .join(Training, Enrollment.training_id == Training.id)
            .where(
                Enrollment.user_id == target_user_id,
                Training.trainer_id == current_user.id,
            )
            .limit(1)
        )
        if owned:
            return
    raise HTTPException(
        status_code=403, detail="You may not view this user's performance insight"
    )


def analyze(db: Session, groq: GroqService, user_id: int) -> dict:
    if not db.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return analyze_performance(db, groq, user_id)
