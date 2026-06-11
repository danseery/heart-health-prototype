import json
import logging
from typing import Any

from app.core.config import Settings
from app.schemas import AnswerPayload
from app.services import ai


def test_azure_openai_summary_uses_structured_prompt(monkeypatch, caplog) -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        status_code = 200
        headers = {"x-ms-request-id": "req_test_123"}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "summary": "Personalized Big Brain summary.",
                                    "key_takeaways": ["LDL is elevated."],
                                    "clinician_questions": ["What target should I discuss?"],
                                    "disclaimer": "Educational only.",
                                }
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(
            self,
            url: str,
            *,
            params: dict,
            headers: dict,
            json: dict,
        ) -> FakeResponse:
            captured.update(
                {
                    "url": url,
                    "params": params,
                    "headers": headers,
                    "payload": json,
                }
            )
            return FakeResponse()

    monkeypatch.setattr(ai.httpx, "Client", FakeClient)
    caplog.set_level(logging.INFO, logger="hearthealth.ai")

    answers = AnswerPayload(
        age=52,
        sex="female",
        systolic_bp=138,
        diastolic_bp=88,
        total_cholesterol=214,
        hdl_cholesterol=44,
        ldl_cholesterol=148,
        on_bp_medication=False,
        smoking_status="never",
        diabetes="no",
        cac_score=0,
    )
    risk = {
        "ascvd_risk": 5.9,
        "framingham_risk": 9.2,
        "heart_age": 59,
        "category": "borderline",
        "risk_factors": [
            {
                "label": "LDL Cholesterol",
                "value": "148 mg/dL",
                "severity": "elevated",
                "explanation": "LDL cholesterol is one contributor.",
            }
        ],
        "protective_signals": [
            {
                "label": "CAC Score",
                "value": "0",
                "severity": "positive",
                "explanation": "A zero coronary calcium score can be reassuring.",
            }
        ],
    }
    settings = Settings(
        AI_PROVIDER="azure_openai",
        AZURE_OPENAI_ENDPOINT="https://big-brain-resource.openai.azure.com/",
        AZURE_OPENAI_DEPLOYMENT="heart-summary",
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_TIMEOUT_SECONDS=12,
    )

    report = ai.generate_assessment_summary(answers, risk, settings=settings)

    assert report["summary"] == "Personalized Big Brain summary."
    assert report["disclaimer"] == "Educational only."
    assert report["citations"] == ai.CITATIONS
    assert captured["url"] == (
        "https://big-brain-resource.openai.azure.com/openai/deployments/"
        "heart-summary/chat/completions"
    )
    assert captured["params"] == {"api-version": "2024-10-21"}
    assert captured["headers"]["api-key"] == "test-key"
    assert captured["payload"]["response_format"] == {"type": "json_object"}
    assert "You are HeartHealth AI" in captured["payload"]["messages"][0]["content"]
    assert "Return JSON only with this shape" in captured["payload"]["messages"][1]["content"]
    assert '"cac_score": 0' in captured["payload"]["messages"][1]["content"]
    assert "AI summary request starting provider=azure_openai" in caplog.text
    assert "AI summary response received provider=azure_openai status_code=200" in caplog.text
    assert "AI summary provider selected provider=azure_openai" in caplog.text
    assert "request_id=req_test_123" in caplog.text
    assert "AI summary generated provider=azure_openai" not in caplog.text


def test_big_brain_foundry_endpoint_uses_models_chat_route() -> None:
    url, api_version = ai.azure_chat_endpoint(
        "https://big-brain-resource.services.ai.azure.com",
        "heart-summary",
        "2024-10-21",
    )

    assert url == "https://big-brain-resource.services.ai.azure.com/models/chat/completions"
    assert api_version == "2024-05-01-preview"
