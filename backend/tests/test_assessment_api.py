from fastapi.testclient import TestClient

from app.main import app


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
    with client:
        first = client.get("/api/content/content_cholesterol_basics/summary")
        assert first.status_code == 200
        assert first.json()["cached"] is False
        assert "Understanding LDL and HDL Cholesterol" in first.json()["title"]

        second = client.get("/api/content/content_cholesterol_basics/summary")
        assert second.status_code == 200
        assert second.json()["cached"] is True
        assert second.json()["summary"] == first.json()["summary"]
