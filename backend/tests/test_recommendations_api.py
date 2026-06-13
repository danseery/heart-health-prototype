import logging

import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas import AnswerPayload
from app.services import recommendations
from app.main import app


client = TestClient(app)


BASE_ANSWERS = {
    "age": 56,
    "sex": "male",
    "systolic_bp": 142,
    "diastolic_bp": 88,
    "total_cholesterol": 232,
    "hdl_cholesterol": 39,
    "ldl_cholesterol": 166,
    "on_bp_medication": False,
    "smoking_status": "current",
    "diabetes": "yes",
    "triglycerides": 220,
    "a1c_percent": 7.2,
    "cac_score": 185,
    "atrial_fibrillation_history": True,
}

APPROVED_SOURCE_IDS = set(recommendations.APPROVED_CITATIONS)
APPROVED_RESOURCE_IDS = set(recommendations.LEARNING_RESOURCES)


def test_completed_assessment_returns_cached_heart_plan() -> None:
    with client:
        session_id = complete_assessment(BASE_ANSWERS)

        first = client.get(f"/api/recommendations/sessions/{session_id}")
        assert first.status_code == 200
        payload = first.json()
        assert payload["session_id"] == session_id
        assert payload["generated_by"] == "dummy"
        assert payload["cached"] is False
        assert [section["section"] for section in payload["sections"]] == [
            "nutrition",
            "fitness",
            "lifestyle",
        ]
        assert all(len(section["cards"]) >= 2 for section in payload["sections"])
        assert "not medical advice" in payload["disclaimer"]

        second = client.get(f"/api/recommendations/sessions/{session_id}")
        assert second.status_code == 200
        assert second.json()["cached"] is True
        assert second.json()["sections"] == payload["sections"]


def test_heart_plan_requires_completed_assessment() -> None:
    with client:
        session_response = client.post("/api/assessment/sessions")
        assert session_response.status_code == 201

        response = client.get(
            f"/api/recommendations/sessions/{session_response.json()['session_id']}"
        )
        assert response.status_code == 409


def test_heart_plan_cards_reflect_cardiology_triggers_and_approved_sources() -> None:
    with client:
        session_id = complete_assessment(BASE_ANSWERS)
        response = client.get(f"/api/recommendations/sessions/{session_id}")
        assert response.status_code == 200
        sections = response.json()["sections"]
        all_cards = [card for section in sections for card in section["cards"]]

        trigger_labels = {
            signal for card in all_cards for signal in card["trigger_signals"]
        }
        assert "LDL Cholesterol" in trigger_labels
        assert "Blood Pressure" in trigger_labels
        assert "Smoking Status" in trigger_labels
        assert "Diabetes" in trigger_labels
        assert "CAC Score" in trigger_labels
        assert "Atrial Fibrillation History" in trigger_labels

        citation_ids = {
            citation["source_id"]
            for card in all_cards
            for citation in card["citations"]
        }
        assert citation_ids
        assert citation_ids <= APPROVED_SOURCE_IDS
        assert all(
            citation["source_url"].startswith("https://")
            for card in all_cards
            for citation in card["citations"]
        )

        learning_resources = [card["learning_resource"] for card in all_cards]
        assert all(resource["resource_id"] in APPROVED_RESOURCE_IDS for resource in learning_resources)
        assert all(resource["url"].startswith("https://") for resource in learning_resources)
        assert any(
            card["title"] == "Make LDL a nutrition priority"
            and card["learning_resource"]["resource_id"] == "aha_saturated_fats"
            for card in all_cards
        )
        assert any(
            card["title"] == "Build around steady aerobic activity"
            and card["learning_resource"]["resource_id"] == "aha_physical_activity_adults"
            for card in all_cards
        )
        assert any(
            card["title"] == "Make nicotine exposure a top lifestyle signal"
            and card["learning_resource"]["resource_id"] == "aha_quit_smoking"
            for card in all_cards
        )


def test_unknown_big_brain_learning_resource_ids_are_rejected() -> None:
    default_resource = "aha_life_essential8"

    resource = recommendations.normalize_learning_resource(
        {"resource_id": "invented_general_health_blog"},
        default_resource,
    )

    assert resource["resource_id"] == default_resource


def test_big_brain_heart_plan_failure_falls_back_without_raw_value_logs(caplog) -> None:
    class FakeClient:
        def __init__(self, timeout: float) -> None:
            return None

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, *args: object, **kwargs: object) -> None:
            raise httpx.HTTPError("boom")

    caplog.set_level(logging.INFO, logger="hearthealth.recommendations")
    original_client = recommendations.httpx.Client
    recommendations.httpx.Client = FakeClient
    try:
        report = recommendations.generate_heart_plan(
            AnswerPayload(**BASE_ANSWERS),
            {
                "ascvd_risk": 21.2,
                "framingham_risk": 29.8,
                "heart_age": 70,
                "category": "high",
                "risk_factors": [
                    {
                        "label": "LDL Cholesterol",
                        "value": "166 mg/dL",
                        "severity": "high",
                        "explanation": "LDL cholesterol is one contributor.",
                    }
                ],
                "protective_signals": [],
            },
            settings=Settings(
                AI_PROVIDER="azure_openai",
                AZURE_OPENAI_ENDPOINT="https://big-brain.openai.azure.com/",
                AZURE_OPENAI_DEPLOYMENT="gpt-5.4",
                AZURE_OPENAI_API_KEY="test-key",
            ),
        )
    finally:
        recommendations.httpx.Client = original_client

    assert report["generated_by"] == "dummy"
    assert "Heart Plan provider failed provider=azure_openai using=local" in caplog.text
    assert "166 mg/dL" not in caplog.text
    assert "142" not in caplog.text


def complete_assessment(answers: dict) -> str:
    session_response = client.post("/api/assessment/sessions")
    assert session_response.status_code == 201
    session_id = session_response.json()["session_id"]

    answers_response = client.put(
        f"/api/assessment/sessions/{session_id}/answers",
        json=answers,
    )
    assert answers_response.status_code == 200

    result_response = client.post(f"/api/assessment/sessions/{session_id}/complete")
    assert result_response.status_code == 200
    return session_id
