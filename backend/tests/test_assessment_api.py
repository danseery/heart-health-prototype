from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.main import app
from app.models import AssessmentSummaryCache, ContentSummary


client = TestClient(app)


def test_assessment_to_results_flow() -> None:
    with client:
        with SessionLocal() as db:
            db.execute(delete(AssessmentSummaryCache))
            db.commit()

        session_response = client.post("/api/assessment/sessions")
        assert session_response.status_code == 201
        session_id = session_response.json()["session_id"]

        answers_response = client.put(
            f"/api/assessment/sessions/{session_id}/answers",
            json={
                "age": 52,
                "sex": "female",
                "systolic_bp": 138,
                "diastolic_bp": 88,
                "total_cholesterol": 214,
                "hdl_cholesterol": 44,
                "ldl_cholesterol": 148,
                "on_bp_medication": False,
                "smoking_status": "never",
                "diabetes": "no",
            },
        )
        assert answers_response.status_code == 200

        result_response = client.post(f"/api/assessment/sessions/{session_id}/complete")
        assert result_response.status_code == 200
        payload = result_response.json()
        assert payload["status"] == "completed"
        assert payload["scores"]["category"] == "borderline"
        assert payload["protective_signals"]
        assert payload["ai_report"]["citations"]
        assert "not medical advice" in payload["ai_report"]["disclaimer"]


def test_assessment_accepts_optional_advanced_inputs() -> None:
    with client:
        session_id = client.post("/api/assessment/sessions").json()["session_id"]
        response = client.put(
            f"/api/assessment/sessions/{session_id}/answers",
            json={
                "age": 58,
                "sex": "male",
                "systolic_bp": 132,
                "diastolic_bp": 82,
                "total_cholesterol": 205,
                "hdl_cholesterol": 48,
                "ldl_cholesterol": 136,
                "on_bp_medication": False,
                "smoking_status": "former",
                "diabetes": "no",
                "cac_score": 145,
                "family_history_premature_ascvd": True,
                "a1c_percent": 4.6,
                "hs_crp_mg_l": 2.5,
                "ankle_brachial_index": None,
            },
        )
        assert response.status_code == 200

        result = client.post(f"/api/assessment/sessions/{session_id}/complete")
        assert result.status_code == 200
        labels = [factor["label"] for factor in result.json()["risk_factors"]]
        assert "CAC Score" in labels
        assert "Family History" in labels


def test_secondary_prevention_payload_returns_context_sensitive_signals() -> None:
    with client:
        session_id = client.post("/api/assessment/sessions").json()["session_id"]
        response = client.put(
            f"/api/assessment/sessions/{session_id}/answers",
            json={
                "age": 61,
                "sex": "male",
                "systolic_bp": 126,
                "diastolic_bp": 76,
                "total_cholesterol": 168,
                "hdl_cholesterol": 58,
                "ldl_cholesterol": 82,
                "on_bp_medication": True,
                "smoking_status": "former",
                "diabetes": "no",
                "established_ascvd": True,
                "apob_mg_dl": 78,
            },
        )
        assert response.status_code == 200

        result = client.post(f"/api/assessment/sessions/{session_id}/complete")
        assert result.status_code == 200
        payload = result.json()
        assert payload["scores"]["category"] == "high"
        assert "secondary-prevention targets" in payload["ai_report"]["summary"]
        assert any(
            factor["label"] == "LDL Cholesterol" for factor in payload["risk_factors"]
        )
        assert any(
            signal["label"] == "ApoB" for signal in payload["protective_signals"]
        )


def test_assessment_summary_is_reused_for_identical_inputs(monkeypatch) -> None:
    from app.api import assessment

    calls = 0

    def fake_generate_assessment_summary(*args, **kwargs) -> dict:
        nonlocal calls
        calls += 1
        report = {
            "summary": "Cached personalized summary.",
            "disclaimer": "Educational only.",
            "citations": [],
        }
        if kwargs.get("include_metadata"):
            report["_generated_by"] = "dummy"
        return report

    monkeypatch.setattr(
        assessment,
        "generate_assessment_summary",
        fake_generate_assessment_summary,
    )
    answers = {
        "age": 54,
        "sex": "female",
        "systolic_bp": 138,
        "diastolic_bp": 88,
        "total_cholesterol": 214,
        "hdl_cholesterol": 44,
        "ldl_cholesterol": 148,
        "on_bp_medication": False,
        "smoking_status": "never",
        "diabetes": "no",
    }

    with client:
        with SessionLocal() as db:
            db.execute(delete(AssessmentSummaryCache))
            db.commit()

        first_session_id = client.post("/api/assessment/sessions").json()["session_id"]
        assert client.put(
            f"/api/assessment/sessions/{first_session_id}/answers",
            json=answers,
        ).status_code == 200
        first = client.post(f"/api/assessment/sessions/{first_session_id}/complete")
        assert first.status_code == 200

        second_session_id = client.post("/api/assessment/sessions").json()["session_id"]
        assert client.put(
            f"/api/assessment/sessions/{second_session_id}/answers",
            json=answers,
        ).status_code == 200
        second = client.post(f"/api/assessment/sessions/{second_session_id}/complete")
        assert second.status_code == 200

    assert calls == 1
    assert second.json()["ai_report"]["summary"] == "Cached personalized summary."


def test_rejects_out_of_range_health_values() -> None:
    with client:
        session_id = client.post("/api/assessment/sessions").json()["session_id"]
        response = client.put(
            f"/api/assessment/sessions/{session_id}/answers",
            json={
                "age": 12,
                "sex": "female",
                "systolic_bp": 138,
                "diastolic_bp": 88,
                "total_cholesterol": 214,
                "hdl_cholesterol": 44,
                "ldl_cholesterol": 148,
                "on_bp_medication": False,
                "smoking_status": "never",
                "diabetes": "no",
            },
        )
        assert response.status_code == 422


def test_content_summary_is_generated_then_cached() -> None:
    with SessionLocal() as db:
        db.execute(
            delete(ContentSummary).where(
                ContentSummary.content_item_id == "content_cholesterol_basics"
            )
        )
        db.commit()

    with client:
        first = client.get("/api/content/content_cholesterol_basics/summary")
        assert first.status_code == 200
        assert first.json()["cached"] is False
        assert "Understanding LDL and HDL Cholesterol" in first.json()["title"]

        second = client.get("/api/content/content_cholesterol_basics/summary")
        assert second.status_code == 200
        assert second.json()["cached"] is True
        assert second.json()["summary"] == first.json()["summary"]
