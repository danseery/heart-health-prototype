from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.init_db import DEMO_USER_ID
from app.db.session import get_db
from app.models import (
    AIReport,
    AssessmentAnswer,
    AssessmentSession,
    AssessmentStatus,
    AuditEvent,
    RiskResult,
    new_id,
)
from app.schemas import (
    AnswerPayload,
    AssessmentAnswersResponse,
    AssessmentQuestion,
    AssessmentSessionResponse,
    ResultResponse,
)
from app.services.ai import generate_assessment_summary
from app.services.scoring import calculate_risk

router = APIRouter(prefix="/assessment", tags=["assessment"])


QUESTIONS = [
    AssessmentQuestion(key="age", label="Age", input_type="number", helper_text="Use an adult age for the assessment.", min_value=20, max_value=100),
    AssessmentQuestion(key="sex", label="Sex", input_type="select", helper_text="Used by many risk calculators.", options=[{"label": "Female", "value": "female"}, {"label": "Male", "value": "male"}]),
    AssessmentQuestion(key="systolic_bp", label="Systolic blood pressure", input_type="number", helper_text="Top number on a blood pressure reading.", unit="mmHg", min_value=80, max_value=240),
    AssessmentQuestion(key="diastolic_bp", label="Diastolic blood pressure", input_type="number", helper_text="Bottom number on a blood pressure reading.", unit="mmHg", min_value=40, max_value=140),
    AssessmentQuestion(key="total_cholesterol", label="Total cholesterol", input_type="number", helper_text="From a recent lipid panel.", unit="mg/dL", min_value=100, max_value=400),
    AssessmentQuestion(key="hdl_cholesterol", label="HDL cholesterol", input_type="number", helper_text="Often called good cholesterol.", unit="mg/dL", min_value=20, max_value=120),
    AssessmentQuestion(key="ldl_cholesterol", label="LDL cholesterol", input_type="number", helper_text="Often called bad cholesterol.", unit="mg/dL", min_value=40, max_value=300),
    AssessmentQuestion(key="on_bp_medication", label="Blood pressure medication", input_type="boolean", helper_text="Whether the person is taking blood pressure medication."),
    AssessmentQuestion(key="smoking_status", label="Smoking status", input_type="select", helper_text="Current smoking changes risk estimates.", options=[{"label": "Never", "value": "never"}, {"label": "Former", "value": "former"}, {"label": "Current", "value": "current"}]),
    AssessmentQuestion(key="diabetes", label="Diabetes", input_type="select", helper_text="Used in common cardiovascular risk equations.", options=[{"label": "No", "value": "no"}, {"label": "Yes", "value": "yes"}, {"label": "Not sure", "value": "not_sure"}]),
]


@router.get("/questions", response_model=list[AssessmentQuestion])
def get_questions() -> list[AssessmentQuestion]:
    return QUESTIONS


@router.post("/sessions", response_model=AssessmentSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(db: Session = Depends(get_db)) -> AssessmentSessionResponse:
    session = AssessmentSession(id=new_id("assess"), user_id=DEMO_USER_ID)
    db.add(session)
    db.add(
        AuditEvent(
            id=new_id("audit"),
            user_id=DEMO_USER_ID,
            event_type="assessment_started",
            entity_type="assessment_session",
            entity_id=session.id,
            event_metadata={"mode": "demo"},
        )
    )
    db.commit()
    return AssessmentSessionResponse(session_id=session.id, status=session.status)


@router.put("/sessions/{session_id}/answers", response_model=AssessmentAnswersResponse)
def save_answers(
    session_id: str,
    payload: AnswerPayload,
    db: Session = Depends(get_db),
) -> AssessmentAnswersResponse:
    session = _get_demo_session(db, session_id)
    if session.status == AssessmentStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Assessment is already completed.")

    db.execute(delete(AssessmentAnswer).where(AssessmentAnswer.session_id == session_id))
    for field, value in payload.model_dump().items():
        db.add(
            AssessmentAnswer(
                id=new_id("answer"),
                session_id=session_id,
                field_key=field,
                value={"value": value},
                unit=_unit_for(field),
            )
        )
    db.commit()
    return AssessmentAnswersResponse(session_id=session_id, saved_fields=list(payload.model_dump().keys()))


@router.post("/sessions/{session_id}/complete", response_model=ResultResponse)
def complete_session(session_id: str, db: Session = Depends(get_db)) -> ResultResponse:
    session = _get_demo_session(db, session_id)
    answers = _answers_for_session(db, session_id)
    risk = calculate_risk(answers)
    report = generate_assessment_summary(answers, risk)

    db.query(RiskResult).filter(RiskResult.session_id == session_id).delete()
    db.query(AIReport).filter(AIReport.session_id == session_id).delete()

    result = RiskResult(id=new_id("result"), session_id=session_id, **risk)
    ai_report = AIReport(id=new_id("report"), session_id=session_id, **report)
    session.status = AssessmentStatus.COMPLETED
    session.completed_at = datetime.now(UTC)
    db.add(result)
    db.add(ai_report)
    db.add(
        AuditEvent(
            id=new_id("audit"),
            user_id=DEMO_USER_ID,
            event_type="assessment_completed",
            entity_type="assessment_session",
            entity_id=session_id,
            event_metadata={"risk_category": risk["category"]},
        )
    )
    db.commit()
    db.refresh(result)
    db.refresh(ai_report)
    return _result_response(session, result, ai_report)


@router.get("/results/{session_id}", response_model=ResultResponse)
def get_result(session_id: str, db: Session = Depends(get_db)) -> ResultResponse:
    session = _get_demo_session(db, session_id)
    result = db.scalar(select(RiskResult).where(RiskResult.session_id == session_id))
    report = db.scalar(select(AIReport).where(AIReport.session_id == session_id))
    if not result or not report:
        raise HTTPException(status_code=404, detail="Results are not ready for this assessment.")
    return _result_response(session, result, report)


def _get_demo_session(db: Session, session_id: str) -> AssessmentSession:
    session = db.get(AssessmentSession, session_id)
    if not session or session.user_id != DEMO_USER_ID:
        raise HTTPException(status_code=404, detail="Assessment session not found.")
    return session


def _answers_for_session(db: Session, session_id: str) -> AnswerPayload:
    rows = db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.session_id == session_id)).all()
    if not rows:
        raise HTTPException(status_code=400, detail="Assessment answers are required before completion.")
    values = {row.field_key: row.value["value"] for row in rows}
    return AnswerPayload.model_validate(values)


def _result_response(session: AssessmentSession, result: RiskResult, report: AIReport) -> ResultResponse:
    return ResultResponse(
        session_id=session.id,
        status=session.status,
        scores={
            "ascvd_risk": result.ascvd_risk,
            "framingham_risk": result.framingham_risk,
            "heart_age": result.heart_age,
            "category": result.category,
        },
        risk_factors=result.risk_factors,
        protective_signals=result.protective_signals,
        ai_report={
            "summary": report.summary,
            "disclaimer": report.disclaimer,
            "citations": report.citations,
        },
    )


def _unit_for(field: str) -> str | None:
    if field.endswith("cholesterol"):
        return "mg/dL"
    if field in {"lpa_mg_dl", "apob_mg_dl", "triglycerides"}:
        return "mg/dL"
    if field == "hs_crp_mg_l":
        return "mg/L"
    if field == "a1c_percent":
        return "%"
    if field == "egfr":
        return "mL/min/1.73 m2"
    if field == "cac_score":
        return "Agatston"
    if field == "ankle_brachial_index":
        return "ratio"
    if field.endswith("_bp"):
        return "mmHg"
    return None
