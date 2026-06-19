from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResult,
    AssessmentResultStatus,
    Enrollment,
    QuestionType,
    User,
)
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, QuestionCreate
from app.services import notification_service
from app.services.training_service import assert_training_access, get_training

# Question types that can be graded automatically.
AUTO_GRADABLE = {QuestionType.mcq, QuestionType.short}


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def get_assessment(db: Session, assessment_id: int) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


def question_count(db: Session, assessment_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(AssessmentQuestion)
        .where(AssessmentQuestion.assessment_id == assessment_id)
    ) or 0


def list_assessments(
    db: Session, training_id: int | None = None, current_user: User | None = None
) -> list[Assessment]:
    from app.models import Enrollment, Training, UserRole

    stmt = select(Assessment)
    if training_id is not None:
        stmt = stmt.where(Assessment.training_id == training_id)

    # Employees only see assessments for trainings they're enrolled in.
    if current_user is not None and current_user.role == UserRole.employee:
        enrolled = select(Enrollment.training_id).where(Enrollment.user_id == current_user.id)
        stmt = stmt.where(Assessment.training_id.in_(enrolled))
    elif current_user is not None and current_user.role == UserRole.trainer:
        owned = select(Training.id).where(
            (Training.trainer_id == current_user.id) | (Training.created_by == current_user.id)
        )
        stmt = stmt.where(Assessment.training_id.in_(owned))

    return list(db.scalars(stmt.order_by(Assessment.id.desc())))


def _add_questions(
    db: Session, assessment: Assessment, questions: list[QuestionCreate]
) -> None:
    for q in questions:
        db.add(
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                correct_answer=q.correct_answer,
                marks=q.marks,
                order_index=q.order_index,
            )
        )


def create_assessment(
    db: Session, payload: AssessmentCreate, current_user: User
) -> Assessment:
    training = get_training(db, payload.training_id)
    assert_training_access(current_user, training)

    total_marks = payload.total_marks or sum(q.marks for q in payload.questions)
    assessment = Assessment(
        training_id=payload.training_id,
        title=payload.title,
        description=payload.description,
        total_marks=total_marks,
        passing_marks=payload.passing_marks,
        duration_minutes=payload.duration_minutes,
    )
    db.add(assessment)
    db.flush()
    _add_questions(db, assessment, payload.questions)

    # Notify enrolled learners that a new assessment is available.
    for enrollment in db.scalars(
        select(Enrollment).where(Enrollment.training_id == payload.training_id)
    ):
        notification_service.notify(
            db,
            enrollment.user_id,
            title="New assessment assigned",
            message=f"'{assessment.title}' is now available for '{training.title}'.",
            type="assessment",
            link=f"/assessments/{assessment.id}",
        )
    return assessment


def update_assessment(
    db: Session, assessment_id: int, payload: AssessmentUpdate, current_user: User
) -> Assessment:
    assessment = get_assessment(db, assessment_id)
    assert_training_access(current_user, get_training(db, assessment.training_id))
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(assessment, key, value)
    return assessment


def delete_assessment(db: Session, assessment_id: int, current_user: User) -> None:
    assessment = get_assessment(db, assessment_id)
    assert_training_access(current_user, get_training(db, assessment.training_id))
    # Remove dependent results explicitly (questions cascade via the ORM relationship).
    db.execute(delete(AssessmentResult).where(AssessmentResult.assessment_id == assessment_id))
    db.delete(assessment)


def add_questions(
    db: Session, assessment_id: int, questions: list[QuestionCreate], current_user: User
) -> Assessment:
    assessment = get_assessment(db, assessment_id)
    assert_training_access(current_user, get_training(db, assessment.training_id))
    _add_questions(db, assessment, questions)
    db.flush()
    # Keep total_marks in sync with the question pool.
    assessment.total_marks = db.scalar(
        select(func.coalesce(func.sum(AssessmentQuestion.marks), 0)).where(
            AssessmentQuestion.assessment_id == assessment_id
        )
    )
    return assessment


def list_questions(db: Session, assessment_id: int) -> list[AssessmentQuestion]:
    get_assessment(db, assessment_id)
    return list(
        db.scalars(
            select(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment_id)
            .order_by(AssessmentQuestion.order_index)
        )
    )


def submit(
    db: Session,
    assessment_id: int,
    answers: dict[str, str],
    current_user: User,
    time_taken_seconds: int | None,
) -> AssessmentResult:
    assessment = get_assessment(db, assessment_id)

    # Must be enrolled in the parent training to take its assessment.
    enrolled = db.scalar(
        select(Enrollment).where(
            Enrollment.training_id == assessment.training_id,
            Enrollment.user_id == current_user.id,
        )
    )
    if not enrolled:
        raise HTTPException(
            status_code=403, detail="You are not enrolled in this training"
        )

    questions = list_questions(db, assessment_id)
    if not questions:
        raise HTTPException(status_code=400, detail="Assessment has no questions")

    score = 0
    max_score = 0
    for q in questions:
        max_score += q.marks
        if q.question_type not in AUTO_GRADABLE or q.correct_answer is None:
            continue  # manual-grade types contribute 0 (see docs/known-gaps.md)
        submitted = answers.get(str(q.id))
        if submitted is not None and _normalize(submitted) == _normalize(q.correct_answer):
            score += q.marks

    passed = score >= assessment.passing_marks
    result = AssessmentResult(
        assessment_id=assessment_id,
        user_id=current_user.id,
        score=score,
        max_score=max_score,
        result=AssessmentResultStatus.pass_ if passed else AssessmentResultStatus.fail,
        answers=answers,
        time_taken_seconds=time_taken_seconds,
    )
    db.add(result)
    return result


def list_results(db: Session, assessment_id: int, current_user: User) -> list[AssessmentResult]:
    assessment = get_assessment(db, assessment_id)
    assert_training_access(current_user, get_training(db, assessment.training_id))
    return list(
        db.scalars(
            select(AssessmentResult).where(AssessmentResult.assessment_id == assessment_id)
        )
    )


def list_my_results(db: Session, user_id: int) -> list[AssessmentResult]:
    return list(
        db.scalars(
            select(AssessmentResult)
            .where(AssessmentResult.user_id == user_id)
            .order_by(AssessmentResult.attempt_date.desc())
        )
    )
