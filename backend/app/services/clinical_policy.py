from app.schemas import AnswerPayload


def is_secondary_prevention(answers: AnswerPayload) -> bool:
    return bool(answers.established_ascvd)


def ldl_goal_mg_dl(answers: AnswerPayload) -> int:
    return 70 if is_secondary_prevention(answers) else 100


def apob_goal_mg_dl(answers: AnswerPayload) -> int:
    return 80 if is_secondary_prevention(answers) else 90


def build_risk_factors(answers: AnswerPayload) -> list[dict]:
    factors: list[dict] = []
    secondary_prevention = is_secondary_prevention(answers)

    if secondary_prevention:
        factors.append(
            signal(
                label="Established ASCVD",
                value="Present",
                severity="high",
                explanation=(
                    "A reported prior cardiovascular event places this assessment in a "
                    "secondary-prevention context."
                ),
            )
        )

    ldl_goal = ldl_goal_mg_dl(answers)
    if secondary_prevention:
        if answers.ldl_cholesterol >= 100:
            severity = "high"
        elif answers.ldl_cholesterol >= ldl_goal:
            severity = "elevated"
        else:
            severity = None
        if severity:
            factors.append(
                signal(
                    label="LDL Cholesterol",
                    value=f"{answers.ldl_cholesterol} mg/dL",
                    severity=severity,
                    explanation=(
                        "With established ASCVD, LDL-C is commonly targeted below "
                        "70 mg/dL."
                    ),
                )
            )
    elif answers.ldl_cholesterol >= 130:
        factors.append(
            signal(
                label="LDL Cholesterol",
                value=f"{answers.ldl_cholesterol} mg/dL",
                severity="high" if answers.ldl_cholesterol >= 160 else "elevated",
                explanation="LDL cholesterol is one contributor to estimated cardiovascular risk.",
            )
        )

    if answers.systolic_bp >= 140 or answers.diastolic_bp >= 90:
        bp_severity = "high"
    elif answers.systolic_bp >= 130 or answers.diastolic_bp >= 80:
        bp_severity = "elevated"
    else:
        bp_severity = None
    if bp_severity:
        factors.append(
            signal(
                label="Blood Pressure",
                value=f"{answers.systolic_bp}/{answers.diastolic_bp} mmHg",
                severity=bp_severity,
                explanation="Repeated elevated readings should be reviewed with a clinician.",
            )
        )

    hdl_floor = 50 if answers.sex == "female" else 40
    if answers.hdl_cholesterol < hdl_floor:
        factors.append(
            signal(
                label="HDL Cholesterol",
                value=f"{answers.hdl_cholesterol} mg/dL",
                severity="borderline" if answers.hdl_cholesterol >= hdl_floor - 10 else "elevated",
                explanation="Lower HDL can contribute to less favorable lipid-related risk estimates.",
            )
        )

    if answers.smoking_status == "current":
        factors.append(
            signal(
                label="Smoking Status",
                value="Current smoker",
                severity="high",
                explanation="Smoking is a major modifiable cardiovascular risk factor.",
            )
        )

    if answers.diabetes == "yes":
        factors.append(
            signal(
                label="Diabetes",
                value="Present",
                severity="elevated",
                explanation="Diabetes meaningfully raises cardiovascular risk and changes treatment goals.",
            )
        )

    factors.extend(build_advanced_risk_factors(answers))
    return factors


def build_protective_signals(answers: AnswerPayload) -> list[dict]:
    signals: list[dict] = []
    secondary_prevention = is_secondary_prevention(answers)

    ldl_goal = ldl_goal_mg_dl(answers)
    if answers.ldl_cholesterol < ldl_goal:
        explanation = (
            "This LDL-C level is below a common secondary-prevention goal."
            if secondary_prevention
            else "This LDL-C level is in an optimal range for many prevention discussions."
        )
        signals.append(
            signal(
                label="LDL Cholesterol",
                value=f"{answers.ldl_cholesterol} mg/dL",
                severity="positive",
                explanation=explanation,
            )
        )

    if answers.hdl_cholesterol >= 60 and answers.hdl_cholesterol <= 90:
        signals.append(
            signal(
                label="HDL Cholesterol",
                value=f"{answers.hdl_cholesterol} mg/dL",
                severity="positive",
                explanation="HDL in this range is commonly treated as a favorable signal.",
            )
        )

    if secondary_prevention:
        blood_pressure_controlled = (
            answers.systolic_bp < 130 and answers.diastolic_bp < 80
        )
        blood_pressure_explanation = (
            "Blood pressure is below a common treatment target for established ASCVD."
        )
    else:
        blood_pressure_controlled = (
            answers.systolic_bp < 120
            and answers.diastolic_bp < 80
            and not answers.on_bp_medication
        )
        blood_pressure_explanation = (
            "This is within the normal blood pressure range without medication support."
        )
    if blood_pressure_controlled:
        signals.append(
            signal(
                label="Blood Pressure",
                value=f"{answers.systolic_bp}/{answers.diastolic_bp} mmHg",
                severity="positive",
                explanation=blood_pressure_explanation,
            )
        )

    if answers.smoking_status in {"never", "former"}:
        signals.append(
            signal(
                label="Smoking Status",
                value="No current use",
                severity="positive",
                explanation="No current smoking reported, which supports cardiovascular risk reduction.",
            )
        )

    if answers.a1c_percent is not None:
        if answers.diabetes == "yes" and answers.a1c_percent <= 7:
            signals.append(
                signal(
                    label="A1c",
                    value=f"{answers.a1c_percent:g}%",
                    severity="positive",
                    explanation="This is within a commonly used control target for many adults with diabetes.",
                )
            )
        elif answers.diabetes != "yes" and answers.a1c_percent < 5.7:
            signals.append(
                signal(
                    label="A1c",
                    value=f"{answers.a1c_percent:g}%",
                    severity="positive",
                    explanation="This is within a non-diabetes range.",
                )
            )

    if not secondary_prevention and answers.cac_score is not None and answers.cac_score == 0:
        signals.append(
            signal(
                label="CAC Score",
                value="0",
                severity="positive",
                explanation="A zero coronary calcium score can be reassuring in primary prevention.",
            )
        )

    if answers.hs_crp_mg_l is not None and answers.hs_crp_mg_l < 1:
        signals.append(
            signal(
                label="hs-CRP",
                value=f"{answers.hs_crp_mg_l:g} mg/L",
                severity="positive",
                explanation="This hs-CRP level is in a low inflammatory-risk range.",
            )
        )

    if answers.lpa_mg_dl is not None and answers.lpa_mg_dl < 30:
        signals.append(
            signal(
                label="Lp(a)",
                value=f"{answers.lpa_mg_dl:g} mg/dL",
                severity="positive",
                explanation="Lp(a) is below a commonly used elevated-risk threshold.",
            )
        )

    apob_goal = apob_goal_mg_dl(answers)
    if answers.apob_mg_dl is not None and answers.apob_mg_dl < apob_goal:
        explanation = (
            "ApoB is below a common secondary-prevention goal."
            if secondary_prevention
            else "ApoB is in a favorable range for atherogenic particle burden."
        )
        signals.append(
            signal(
                label="ApoB",
                value=f"{answers.apob_mg_dl:g} mg/dL",
                severity="positive",
                explanation=explanation,
            )
        )

    if answers.triglycerides is not None and answers.triglycerides < 150:
        signals.append(
            signal(
                label="Triglycerides",
                value=f"{answers.triglycerides} mg/dL",
                severity="positive",
                explanation="Triglycerides are within a normal range.",
            )
        )

    return signals


def advanced_risk_modifier(answers: AnswerPayload) -> float:
    modifier = 0.0
    modifier += 5.0 if answers.established_ascvd else 0
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
    modifier += 1.1 if answers.a1c_percent is not None and answers.a1c_percent >= 6.5 else 0
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
        (
            answers.family_history_premature_ascvd,
            "Family History",
            "Premature ASCVD in a first-degree relative is a recognized risk-enhancing factor.",
        ),
        (
            answers.chronic_kidney_disease,
            "Chronic Kidney Disease",
            "CKD is a recognized cardiovascular risk-enhancing factor.",
        ),
        (
            answers.metabolic_syndrome,
            "Metabolic Syndrome",
            "Metabolic syndrome can raise cardiovascular risk.",
        ),
        (
            answers.inflammatory_condition,
            "Inflammatory Condition",
            "Chronic inflammatory conditions can enhance cardiovascular risk.",
        ),
        (
            answers.premature_menopause,
            "Premature Menopause",
            "Premature menopause is a risk-enhancing history factor.",
        ),
        (
            answers.preeclampsia_history,
            "Preeclampsia History",
            "Preeclampsia is associated with later cardiovascular risk.",
        ),
        (
            answers.south_asian_ancestry,
            "South Asian Ancestry",
            "South Asian ancestry is included in guideline risk-enhancing factors.",
        ),
    ]
    for present, label, explanation in history_flags:
        if present:
            factors.append(
                signal(
                    label=label,
                    value="Present",
                    severity="borderline",
                    explanation=explanation,
                )
            )

    if answers.cac_score is not None and answers.cac_score > 0:
        factors.append(cac_factor(answers.cac_score))
    if answers.lpa_mg_dl is not None and answers.lpa_mg_dl >= 50:
        factors.append(
            signal(
                label="Lipoprotein(a)",
                value=f"{answers.lpa_mg_dl:g} mg/dL",
                severity="elevated",
                explanation="Lp(a) at or above 50 mg/dL is commonly treated as a risk-enhancing factor.",
            )
        )
    secondary_prevention = is_secondary_prevention(answers)
    apob_high_threshold = 100 if secondary_prevention else 130
    if answers.apob_mg_dl is not None and answers.apob_mg_dl >= apob_high_threshold:
        factors.append(
            signal(
                label="ApoB",
                value=f"{answers.apob_mg_dl:g} mg/dL",
                severity="elevated",
                explanation=(
                    "ApoB is above a common secondary-prevention threshold."
                    if secondary_prevention
                    else "ApoB at or above 130 mg/dL can indicate atherogenic particle burden."
                ),
            )
        )
    if answers.hs_crp_mg_l is not None and answers.hs_crp_mg_l >= 2:
        factors.append(
            signal(
                label="hs-CRP",
                value=f"{answers.hs_crp_mg_l:g} mg/L",
                severity="borderline" if answers.hs_crp_mg_l < 3 else "elevated",
                explanation="hs-CRP at or above 2 mg/L is a risk-enhancing inflammatory marker.",
            )
        )
    if answers.triglycerides is not None and answers.triglycerides >= 175:
        factors.append(
            signal(
                label="Triglycerides",
                value=f"{answers.triglycerides} mg/dL",
                severity="borderline" if answers.triglycerides < 500 else "high",
                explanation="Persistently elevated triglycerides are a guideline risk-enhancing factor.",
            )
        )
    if answers.egfr is not None and answers.egfr < 60:
        factors.append(
            signal(
                label="Kidney Function",
                value=f"eGFR {answers.egfr:g}",
                severity="elevated" if answers.egfr >= 30 else "high",
                explanation="Reduced eGFR can reflect chronic kidney disease risk.",
            )
        )
    if answers.a1c_percent is not None:
        if 5.7 <= answers.a1c_percent < 6.5:
            factors.append(
                signal(
                    label="A1c",
                    value=f"{answers.a1c_percent:g}%",
                    severity="borderline",
                    explanation="Prediabetes-range A1c can help contextualize cardiometabolic risk.",
                )
            )
        elif answers.a1c_percent >= 6.5:
            factors.append(
                signal(
                    label="A1c",
                    value=f"{answers.a1c_percent:g}%",
                    severity="high",
                    explanation="This A1c is within the diabetes range and can materially change cardiovascular risk.",
                )
            )
    if answers.ankle_brachial_index is not None and answers.ankle_brachial_index < 0.9:
        factors.append(
            signal(
                label="Ankle-Brachial Index",
                value=f"{answers.ankle_brachial_index:g}",
                severity="elevated",
                explanation="Low ABI can signal peripheral artery disease and higher cardiovascular risk.",
            )
        )
    if answers.carotid_plaque:
        factors.append(
            signal(
                label="Carotid Plaque",
                value="Present",
                severity="high",
                explanation="Documented plaque is evidence of atherosclerosis.",
            )
        )
    if answers.left_ventricular_hypertrophy:
        factors.append(
            signal(
                label="Left Ventricular Hypertrophy",
                value="Present",
                severity="borderline",
                explanation="LVH can reflect long-term pressure strain and warrants clinical context.",
            )
        )
    if answers.atrial_fibrillation_history:
        factors.append(
            signal(
                label="Atrial Fibrillation History",
                value="Present",
                severity="borderline",
                explanation="AFib history is important for broader cardiology risk conversations.",
            )
        )
    return factors


def cac_factor(cac_score: int) -> dict:
    if cac_score == 0:
        return signal(
            label="CAC Score",
            value="0",
            severity="positive",
            explanation="CAC of 0 can lower near-term coronary risk in selected prevention discussions.",
        )
    if cac_score < 100:
        severity = "borderline"
        explanation = "CAC 1-99 indicates detectable coronary calcium."
    elif cac_score < 300:
        severity = "elevated"
        explanation = "CAC at or above 100 is commonly treated as a meaningful risk reclassifier."
    else:
        severity = "high"
        explanation = "CAC 300 or higher suggests high coronary plaque burden."
    return signal(
        label="CAC Score",
        value=str(cac_score),
        severity=severity,
        explanation=explanation,
    )


def signal(label: str, value: str, severity: str, explanation: str) -> dict:
    return {
        "label": label,
        "value": value,
        "severity": severity,
        "explanation": explanation,
    }
