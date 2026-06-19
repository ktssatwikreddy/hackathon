from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import Assessment, User, UserRole
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentOut,
    AssessmentUpdate,
    QuestionCreate,
    QuestionPublic,
    ResultOut,
    SubmitRequest,
)
from app.services import assessment_service

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


def _to_out(db: Session, assessment: Assessment) -> AssessmentOut:
    out = AssessmentOut.model_validate(assessment)
    out.question_count = assessment_service.question_count(db, assessment.id)
    return out


@router.get("", response_model=list[AssessmentOut], summary="List assessments (optionally by training)")
def list_assessments(
    training_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [_to_out(db, a) for a in assessment_service.list_assessments(db, training_id)]


@router.get("/me/results", response_model=list[ResultOut], summary="My assessment results")
def my_results(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return assessment_service.list_my_results(db, current_user.id)


@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED, summary="Create an assessment (optionally with questions)")
def create_assessment(
    payload: AssessmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    assessment = assessment_service.create_assessment(db, payload, current_user)
    audit_log(db, action="create", entity="assessment", entity_id=assessment.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(assessment)
    return _to_out(db, assessment)


@router.get("/{assessment_id}", response_model=AssessmentOut, summary="Get a single assessment")
def get_assessment(
    assessment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return _to_out(db, assessment_service.get_assessment(db, assessment_id))


@router.patch("/{assessment_id}", response_model=AssessmentOut, summary="Update an assessment")
def update_assessment(
    assessment_id: int,
    payload: AssessmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    assessment = assessment_service.update_assessment(db, assessment_id, payload, current_user)
    audit_log(db, action="update", entity="assessment", entity_id=assessment.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(assessment)
    return _to_out(db, assessment)


@router.get("/{assessment_id}/questions", response_model=list[QuestionPublic], summary="List questions (no answer key)")
def list_questions(
    assessment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return assessment_service.list_questions(db, assessment_id)


@router.post("/{assessment_id}/questions", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED, summary="Add questions to an assessment")
def add_questions(
    assessment_id: int,
    payload: list[QuestionCreate],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    assessment = assessment_service.add_questions(db, assessment_id, payload, current_user)
    audit_log(db, action="add_questions", entity="assessment", entity_id=assessment_id, user_id=current_user.id, metadata={"count": len(payload)}, request=request)
    db.commit()
    db.refresh(assessment)
    return _to_out(db, assessment)


@router.post("/{assessment_id}/submit", response_model=ResultOut, status_code=status.HTTP_201_CREATED, summary="Submit answers and get auto-graded result")
def submit_assessment(
    assessment_id: int,
    payload: SubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = assessment_service.submit(
        db, assessment_id, payload.answers, current_user, payload.time_taken_seconds
    )
    audit_log(db, action="submit", entity="assessment", entity_id=assessment_id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(result)
    return result


@router.get("/{assessment_id}/results", response_model=list[ResultOut], summary="All results for an assessment (staff)")
def list_results(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
):
    return assessment_service.list_results(db, assessment_id, current_user)
