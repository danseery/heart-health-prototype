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
    factors.extend(build_advanced_risk_factors(answers))
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


def advanced_risk_modifier(answers: AnswerPayload) -> float:
    modifier = 0.0
    modifier += 1.0 if answers.family_history_premature_ascvd else 0
    modifier += 1.0 if answers.chronic_kidney_disease else 0
    modifier += 0.8 if answers.metabolic_syndrome else 0
    modifier += 0.7 if answers.inflammatory_condition else 0
    modifier += 0.5 if answers.premature_menopause else 0
    modifier += 0.6 if answers.preeclampsia_history else 0
    modifier += 0.6 if answers.south_asian_ancestry else 0
    modifier += 0.8 if answers.lpa_mg_dl is not None and answers.lpa_mg_dl >= 50 else 0
    modifier += 0.7 if answers.apob_mg_dl is not None and answers.apob_mg_dl >= 130 else 0
    modifier += 0.5 if answers.hs_crp_mg_l is not None and answers.hs_crp_mg_l >= 2 else 0
    modifier += 0.5 if answers.triglycerides is not None and answers.triglycerides >= 175 else 0
    modifier += 0.8 if answers.egfr is not None and answers.egfr < 60 else 0
    modifier += 0.5 if answers.a1c_percent is not None and 5.7 <= answers.a1c_percent < 6.5 else 0
    modifier += 0.9 if answers.ankle_brachial_index is not None and answers.ankle_brachial_index < 0.9 else 0
    modifier += 0.9 if answers.carotid_plaque else 0
    modifier += 0.7 if answers.left_ventricular_hypertrophy else 0
    modifier += 0.7 if answers.atrial_fibrillation_history else 0

    if answers.cac_score is not None:
        if answers.cac_score == 0:
            modifier -= 0.8
        elif answers.cac_score < 100:
            modifier += 0.8
        elif answers.cac_score < 300:
            modifier += 2.5
        else:
            modifier += 4.0

    return modifier


def build_advanced_risk_factors(answers: AnswerPayload) -> list[dict]:
    factors: list[dict] = []
    history_flags = [
        (answers.family_history_premature_ascvd, "Family History", "Premature ASCVD in a first-degree relative"),
        (answers.chronic_kidney_disease, "Chronic Kidney Disease", "CKD is a recognized risk-enhancing factor."),
        (answers.metabolic_syndrome, "Metabolic Syndrome", "Metabolic syndrome can raise cardiovascular risk."),
        (answers.inflammatory_condition, "Inflammatory Condition", "Chronic inflammatory conditions can enhance risk."),
        (answers.premature_menopause, "Premature Menopause", "Premature menopause is a risk-enhancing history factor."),
        (answers.preeclampsia_history, "Preeclampsia History", "Preeclampsia is associated with later cardiovascular risk."),
        (answers.south_asian_ancestry, "South Asian Ancestry", "South Asian ancestry is included in guideline risk-enhancing factors."),
    ]
    for present, label, explanation in history_flags:
        if present:
            factors.append(
                {
                    "label": label,
                    "value": "Present",
                    "severity": "watch",
                    "explanation": explanation,
                }
            )

    if answers.cac_score is not None:
        factors.append(cac_factor(answers.cac_score))
    if answers.lpa_mg_dl is not None and answers.lpa_mg_dl >= 50:
        factors.append(
            {
                "label": "Lipoprotein(a)",
                "value": f"{answers.lpa_mg_dl:g} mg/dL",
                "severity": "elevated",
                "explanation": "Lp(a) at or above 50 mg/dL is commonly treated as a risk-enhancing factor.",
            }
        )
    if answers.apob_mg_dl is not None and answers.apob_mg_dl >= 130:
        factors.append(
            {
                "label": "ApoB",
                "value": f"{answers.apob_mg_dl:g} mg/dL",
                "severity": "elevated",
                "explanation": "ApoB at or above 130 mg/dL can indicate atherogenic particle burden.",
            }
        )
    if answers.hs_crp_mg_l is not None and answers.hs_crp_mg_l >= 2:
        factors.append(
            {
                "label": "hs-CRP",
                "value": f"{answers.hs_crp_mg_l:g} mg/L",
                "severity": "watch",
                "explanation": "hs-CRP at or above 2 mg/L is a risk-enhancing inflammatory marker.",
            }
        )
    if answers.triglycerides is not None and answers.triglycerides >= 175:
        factors.append(
            {
                "label": "Triglycerides",
                "value": f"{answers.triglycerides} mg/dL",
                "severity": "watch",
                "explanation": "Persistently elevated triglycerides are a guideline risk-enhancing factor.",
            }
        )
    if answers.egfr is not None and answers.egfr < 60:
        factors.append(
            {
                "label": "Kidney Function",
                "value": f"eGFR {answers.egfr:g}",
                "severity": "elevated",
                "explanation": "Reduced eGFR can reflect chronic kidney disease risk.",
            }
        )
    if answers.a1c_percent is not None and 5.7 <= answers.a1c_percent < 6.5:
        factors.append(
            {
                "label": "A1c",
                "value": f"{answers.a1c_percent:g}%",
                "severity": "watch",
                "explanation": "Prediabetes-range A1c can help contextualize cardiometabolic risk.",
            }
        )
    if answers.ankle_brachial_index is not None and answers.ankle_brachial_index < 0.9:
        factors.append(
            {
                "label": "Ankle-Brachial Index",
                "value": f"{answers.ankle_brachial_index:g}",
                "severity": "elevated",
                "explanation": "Low ABI can signal peripheral artery disease and higher cardiovascular risk.",
            }
        )
    if answers.carotid_plaque:
        factors.append(
            {
                "label": "Carotid Plaque",
                "value": "Present",
                "severity": "elevated",
                "explanation": "Documented plaque is evidence of atherosclerosis.",
            }
        )
    if answers.left_ventricular_hypertrophy:
        factors.append(
            {
                "label": "Left Ventricular Hypertrophy",
                "value": "Present",
                "severity": "watch",
                "explanation": "LVH can reflect long-term pressure strain and warrants clinical context.",
            }
        )
    if answers.atrial_fibrillation_history:
        factors.append(
            {
                "label": "Atrial Fibrillation History",
                "value": "Present",
                "severity": "watch",
                "explanation": "AFib history is important for broader cardiology risk conversations.",
            }
        )
    return factors


def cac_factor(cac_score: int) -> dict:
    if cac_score == 0:
        return {
            "label": "CAC Score",
            "value": "0",
            "severity": "positive",
            "explanation": "CAC of 0 can lower near-term coronary risk in selected prevention discussions.",
        }
    if cac_score < 100:
        severity = "watch"
        explanation = "CAC 1-99 indicates detectable coronary calcium."
    elif cac_score < 300:
        severity = "elevated"
        explanation = "CAC at or above 100 is commonly treated as a meaningful risk reclassifier."
    else:
        severity = "high"
        explanation = "CAC 300 or higher suggests high coronary plaque burden."
    return {
        "label": "CAC Score",
        "value": str(cac_score),
        "severity": severity,
        "explanation": explanation,
    }
