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
    age: Annotated[int, Field(ge=18, le=100)]
    sex: Sex
    systolic_bp: Annotated[int, Field(ge=70, le=260)]
    diastolic_bp: Annotated[int, Field(ge=30, le=160)]
    total_cholesterol: Annotated[int, Field(ge=50, le=500)]
    hdl_cholesterol: Annotated[int, Field(ge=10, le=150)]
    ldl_cholesterol: Annotated[int, Field(ge=0, le=400)]
    on_bp_medication: bool
    smoking_status: SmokingStatus
    diabetes: DiabetesStatus
    established_ascvd: bool | None = None
    family_history_premature_ascvd: bool | None = None
    chronic_kidney_disease: bool | None = None
    metabolic_syndrome: bool | None = None
    inflammatory_condition: bool | None = None
    premature_menopause: bool | None = None
    preeclampsia_history: bool | None = None
    south_asian_ancestry: bool | None = None
    cac_score: Annotated[int | None, Field(ge=0, le=5000)] = None
    lpa_mg_dl: Annotated[float | None, Field(ge=0, le=500)] = None
    apob_mg_dl: Annotated[float | None, Field(ge=20, le=300)] = None
    hs_crp_mg_l: Annotated[float | None, Field(ge=0, le=100)] = None
    a1c_percent: Annotated[float | None, Field(ge=3, le=18)] = None
    egfr: Annotated[float | None, Field(ge=0, le=150)] = None
    triglycerides: Annotated[int | None, Field(ge=20, le=3000)] = None
    ankle_brachial_index: Annotated[float | None, Field(ge=0, le=2.5)] = None
    carotid_plaque: bool | None = None
    left_ventricular_hypertrophy: bool | None = None
    atrial_fibrillation_history: bool | None = None


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


class ClinicalSignal(BaseModel):
    label: str
    value: str
    severity: str
    explanation: str


class Citation(BaseModel):
    title: str
    source_id: str
    author: str
    source_url: str | None = None


class LearningResource(BaseModel):
    resource_id: str
    title: str
    source: str
    url: str
    topic: str
    applies_to: list[str]
    priority: int


class ContentSummaryResponse(BaseModel):
    content_id: str
    title: str
    topic: str
    author: str
    summary: str
    cached: bool


class AIReportResponse(BaseModel):
    summary: str
    disclaimer: str
    citations: list[Citation]


class HeartPlanCard(BaseModel):
    title: str
    priority: str
    trigger_signals: list[str]
    why_it_matters: str
    educational_next_step: str
    learning_resource: LearningResource
    clinician_question: str
    citations: list[Citation]
    disclaimer: str


class HeartPlanSection(BaseModel):
    section: str
    title: str
    cards: list[HeartPlanCard]


class HeartPlanResponse(BaseModel):
    session_id: str
    sections: list[HeartPlanSection]
    generated_by: str
    cached: bool
    disclaimer: str


class ResultResponse(BaseModel):
    session_id: str
    status: str
    scores: dict[str, Any]
    risk_factors: list[ClinicalSignal]
    protective_signals: list[ClinicalSignal]
    ai_report: AIReportResponse
