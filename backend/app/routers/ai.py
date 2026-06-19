from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.ai.groq_client import GroqService, get_groq_service
from app.core.audit import audit_log
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models import User, UserRole
from app.schemas.ai import (
    AnalyzePerformanceRequest,
    GenerateAssessmentRequest,
    PerformanceInsight,
)
from app.schemas.assessment import AssessmentOut
from app.services import ai_service, assessment_service

router = APIRouter(prefix="/api/ai", tags=["ai"])

staff_only = require_roles(UserRole.super_admin, UserRole.trainer)


@router.post(
    "/generate-assessment",
    response_model=AssessmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and persist an assessment from material text",
)
def generate_assessment(
    payload: GenerateAssessmentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_only),
    groq: GroqService = Depends(get_groq_service),
):
    assessment = ai_service.generate_assessment(db, groq, payload, current_user)
    audit_log(db, action="ai_generate_assessment", entity="assessment", entity_id=assessment.id, user_id=current_user.id, request=request)
    db.commit()
    db.refresh(assessment)
    out = AssessmentOut.model_validate(assessment)
    out.question_count = assessment_service.question_count(db, assessment.id)
    return out


@router.post(
    "/analyze-performance",
    response_model=PerformanceInsight,
    summary="AI performance insight for a user (RBAC: self / own trainees / any)",
)
def analyze_performance(
    payload: AnalyzePerformanceRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    groq: GroqService = Depends(get_groq_service),
):
    ai_service.assert_can_view_performance(db, current_user, payload.user_id)
    insight = ai_service.analyze(db, groq, payload.user_id)
    audit_log(db, action="ai_analyze_performance", entity="user", entity_id=payload.user_id, user_id=current_user.id, request=request)
    db.commit()
    return PerformanceInsight(**insight)
