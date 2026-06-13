from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.init_db import OPEN_SESSION_USER_ID
from app.db.session import get_db
from app.models import (
    AssessmentAnswer,
    AssessmentSession,
    AssessmentStatus,
    HeartPlanRecommendation,
    RiskResult,
    new_id,
)
from app.schemas import AnswerPayload, HeartPlanResponse
from app.services.recommendations import enrich_citations, generate_heart_plan


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/sessions/{session_id}", response_model=HeartPlanResponse)
def get_heart_plan(
    session_id: str,
    db: Session = Depends(get_db),
) -> HeartPlanResponse:
    session = _get_open_session(db, session_id)
    if session.status != AssessmentStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Assessment must be completed before recommendations are available.",
        )

    cached_plan = db.scalar(
        select(HeartPlanRecommendation).where(
            HeartPlanRecommendation.session_id == session_id
        )
    )
    if cached_plan:
        return _heart_plan_response(session_id, cached_plan, cached=True)

    result = db.scalar(select(RiskResult).where(RiskResult.session_id == session_id))
    if not result:
        raise HTTPException(
            status_code=409,
            detail="Assessment results are required before recommendations are available.",
        )

    generated = generate_heart_plan(_answers_for_session(db, session_id), _risk_dict(result))
    plan = HeartPlanRecommendation(
        id=new_id("heartplan"),
        session_id=session_id,
        sections=generated["sections"],
        disclaimer=generated["disclaimer"],
        generated_by=generated["generated_by"],
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _heart_plan_response(session_id, plan, cached=False)


def _get_open_session(db: Session, session_id: str) -> AssessmentSession:
    session = db.get(AssessmentSession, session_id)
    if not session or session.user_id != OPEN_SESSION_USER_ID:
        raise HTTPException(status_code=404, detail="Assessment session not found.")
    return session


def _answers_for_session(db: Session, session_id: str) -> AnswerPayload:
    rows = db.scalars(
        select(AssessmentAnswer).where(AssessmentAnswer.session_id == session_id)
    ).all()
    if not rows:
        raise HTTPException(
            status_code=409,
            detail="Assessment answers are required before recommendations are available.",
        )
    values = {row.field_key: row.value["value"] for row in rows}
    return AnswerPayload.model_validate(values)


def _risk_dict(result: RiskResult) -> dict:
    return {
        "ascvd_risk": result.ascvd_risk,
        "framingham_risk": result.framingham_risk,
        "heart_age": result.heart_age,
        "category": result.category,
        "risk_factors": result.risk_factors,
        "protective_signals": result.protective_signals,
    }


def _heart_plan_response(
    session_id: str,
    plan: HeartPlanRecommendation,
    *,
    cached: bool,
) -> HeartPlanResponse:
    return HeartPlanResponse(
        session_id=session_id,
        sections=enrich_citations(plan.sections),
        generated_by=plan.generated_by,
        cached=cached,
        disclaimer=plan.disclaimer,
    )
