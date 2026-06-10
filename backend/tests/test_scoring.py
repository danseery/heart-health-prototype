from app.schemas import AnswerPayload
from app.services.scoring import calculate_risk


def test_calculate_risk_flags_elevated_values() -> None:
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
    )

    result = calculate_risk(answers)

    assert result["category"] == "borderline"
    assert result["ascvd_risk"] == 5.9
    assert result["heart_age"] == 59
    assert [factor["label"] for factor in result["risk_factors"]] == [
        "LDL Cholesterol",
        "Blood Pressure",
        "HDL Cholesterol",
    ]
