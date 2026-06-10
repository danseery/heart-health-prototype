from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.main import app
from app.models import ContentSummary


client = TestClient(app)


def test_assessment_to_results_flow() -> None:
    with client:
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
