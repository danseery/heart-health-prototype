from app.schemas import AnswerPayload
from app.services.clinical_policy import (
    advanced_risk_modifier,
    build_protective_signals,
    build_risk_factors,
    is_secondary_prevention,
)


def calculate_risk(answers: AnswerPayload) -> dict:
    risk = 1.0
    risk += max(answers.age - 40, 0) * 0.18
    risk += max(answers.systolic_bp - 120, 0) * 0.08
    risk += max(answers.total_cholesterol - 180, 0) * 0.025
    risk += max(50 - answers.hdl_cholesterol, 0) * 0.07
    risk += 2.2 if answers.smoking_status == "current" else 0
    risk += 1.4 if answers.diabetes == "yes" else 0
    risk += 0.8 if answers.on_bp_medication else 0
    risk += 0.7 if answers.sex == "male" else 0
    risk += advanced_risk_modifier(answers)

    ascvd = round(min(max(risk, 0.5), 35.0), 1)
    framingham = round(min(ascvd * 1.35 + 1.2, 40.0), 1)
    heart_age = int(
        answers.age
        + max(answers.systolic_bp - 120, 0) / 6
        + max(answers.ldl_cholesterol - 100, 0) / 12
        - max(answers.hdl_cholesterol - 50, 0) / 10
    )
    heart_age = max(answers.age - 6, min(heart_age, answers.age + 25))

    if is_secondary_prevention(answers):
        ascvd = max(ascvd, 20.0)
        framingham = max(framingham, 25.0)
        heart_age = max(heart_age, answers.age + 8)
        category = "high"
    elif ascvd < 5:
        category = "low"
    elif ascvd < 7.5:
        category = "borderline"
    elif ascvd < 20:
        category = "intermediate"
    else:
        category = "high"

    return {
        "ascvd_risk": ascvd,
        "framingham_risk": framingham,
        "heart_age": heart_age,
        "category": category,
        "risk_factors": build_risk_factors(answers),
        "protective_signals": build_protective_signals(answers),
    }
