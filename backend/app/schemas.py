from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"


class SmokingStatus(StrEnum):
    NEVER = "never"
    FORMER = "former"
    CURRENT = "current"


class DiabetesStatus(StrEnum):
    NO = "no"
    YES = "yes"
    NOT_SURE = "not_sure"


class AnswerPayload(BaseModel):
    age: Annotated[int, Field(ge=20, le=100)]
    sex: Sex
    systolic_bp: Annotated[int, Field(ge=80, le=240)]
    diastolic_bp: Annotated[int, Field(ge=40, le=140)]
    total_cholesterol: Annotated[int, Field(ge=100, le=400)]
    hdl_cholesterol: Annotated[int, Field(ge=20, le=120)]
    ldl_cholesterol: Annotated[int, Field(ge=40, le=300)]
    on_bp_medication: bool
    smoking_status: SmokingStatus
    diabetes: DiabetesStatus


class AssessmentQuestion(BaseModel):
    key: str
    label: str
    input_type: str
    helper_text: str
    unit: str | None = None
    options: list[dict[str, str]] | None = None
    min_value: int | None = None
    max_value: int | None = None


class AssessmentSessionResponse(BaseModel):
    session_id: str
    status: str


class AssessmentAnswersResponse(BaseModel):
    session_id: str
    saved_fields: list[str]


class RiskFactor(BaseModel):
    label: str
    value: str
    severity: str
    explanation: str


class Citation(BaseModel):
    title: str
    source_id: str
    author: str


class AIReportResponse(BaseModel):
    summary: str
    disclaimer: str
    citations: list[Citation]


class ResultResponse(BaseModel):
    session_id: str
    status: str
    scores: dict[str, Any]
    risk_factors: list[RiskFactor]
    ai_report: AIReportResponse
