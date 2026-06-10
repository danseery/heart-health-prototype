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


def test_advanced_inputs_are_optional_but_can_modify_risk() -> None:
    base_answers = AnswerPayload(
        age=52,
        sex="female",
        systolic_bp=118,
        diastolic_bp=74,
        total_cholesterol=178,
        hdl_cholesterol=62,
        ldl_cholesterol=96,
        on_bp_medication=False,
        smoking_status="never",
        diabetes="no",
    )
    advanced_answers = base_answers.model_copy(
        update={
            "cac_score": 125,
            "family_history_premature_ascvd": True,
            "lpa_mg_dl": 62,
        }
    )

    base = calculate_risk(base_answers)
    advanced = calculate_risk(advanced_answers)

    assert advanced["ascvd_risk"] > base["ascvd_risk"]
    assert "CAC Score" in [factor["label"] for factor in advanced["risk_factors"]]
    assert "Family History" in [factor["label"] for factor in advanced["risk_factors"]]
