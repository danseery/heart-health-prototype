from app.schemas import AnswerPayload


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

    ascvd = round(min(max(risk, 0.5), 35.0), 1)
    framingham = round(min(ascvd * 1.35 + 1.2, 40.0), 1)
    heart_age = int(
        answers.age
        + max(answers.systolic_bp - 120, 0) / 6
        + max(answers.ldl_cholesterol - 100, 0) / 12
        - max(answers.hdl_cholesterol - 50, 0) / 10
    )
    heart_age = max(answers.age - 6, min(heart_age, answers.age + 25))

    if ascvd < 5:
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
    }


def build_risk_factors(answers: AnswerPayload) -> list[dict]:
    factors: list[dict] = []
    if answers.ldl_cholesterol >= 130:
        factors.append(
            {
                "label": "LDL Cholesterol",
                "value": f"{answers.ldl_cholesterol} mg/dL",
                "severity": "elevated" if answers.ldl_cholesterol < 160 else "high",
                "explanation": "LDL is one contributor to estimated cardiovascular risk.",
            }
        )
    if answers.systolic_bp >= 130 or answers.diastolic_bp >= 80:
        factors.append(
            {
                "label": "Blood Pressure",
                "value": f"{answers.systolic_bp}/{answers.diastolic_bp} mmHg",
                "severity": "elevated" if answers.systolic_bp < 140 else "high",
                "explanation": "Repeated elevated readings should be reviewed with a clinician.",
            }
        )
    if answers.hdl_cholesterol < 45:
        factors.append(
            {
                "label": "HDL Cholesterol",
                "value": f"{answers.hdl_cholesterol} mg/dL",
                "severity": "watch",
                "explanation": "HDL is included in common cardiovascular risk estimates.",
            }
        )
    if answers.smoking_status == "current":
        factors.append(
            {
                "label": "Smoking Status",
                "value": "Current smoker",
                "severity": "high",
                "explanation": "Smoking is a significant modifiable cardiovascular risk factor.",
            }
        )
    if not factors:
        factors.append(
            {
                "label": "Protective Signals",
                "value": "No major elevated values in this demo",
                "severity": "positive",
                "explanation": "Keep reviewing your numbers with a qualified clinician.",
            }
        )
    return factors
