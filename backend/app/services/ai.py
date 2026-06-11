from app.schemas import AnswerPayload


EDUCATIONAL_DISCLAIMER = (
    "This is educational information based on simplified calculations and curated "
    "content. It is not medical advice, diagnosis, or treatment. Discuss personal "
    "medical decisions with a qualified clinician."
)


def generate_assessment_summary(answers: AnswerPayload, risk: dict) -> dict:
    primary_risk = risk["risk_factors"][0] if risk["risk_factors"] else None
    primary_protective = (
        risk["protective_signals"][0] if risk["protective_signals"] else None
    )

    summary = (
        f"Your estimated 10-year ASCVD-style risk is {risk['ascvd_risk']}%, "
        f"which is categorized as {risk['category']}."
    )
    if answers.established_ascvd:
        summary += (
            " A prior cardiovascular event was reported, so secondary-prevention "
            "targets are more relevant than primary-prevention risk scoring alone."
        )
    elif primary_risk:
        summary += (
            f" The most notable risk signal in this assessment is "
            f"{primary_risk['label'].lower()} ({primary_risk['value']})."
        )
    elif primary_protective:
        summary += (
            f" A favorable finding in this assessment is "
            f"{primary_protective['label'].lower()} ({primary_protective['value']})."
        )

    if answers.established_ascvd and answers.ldl_cholesterol >= 70:
        summary += (
            " Because established ASCVD is present, LDL-C is commonly targeted below "
            "70 mg/dL."
        )
    if answers.smoking_status == "current":
        summary += (
            " Smoking status is also highlighted because it can materially affect "
            "cardiovascular risk."
        )
    summary += (
        " These calculations are simplified and should be interpreted alongside the "
        "full clinical picture."
    )

    return {
        "summary": summary,
        "disclaimer": EDUCATIONAL_DISCLAIMER,
        "citations": [
            {
                "title": "Understanding LDL and HDL Cholesterol",
                "source_id": "content_cholesterol_basics",
                "author": "Dr. Brian Chen, DO",
            },
            {
                "title": "Blood Pressure Numbers Explained",
                "source_id": "content_bp_basics",
                "author": "Dr. Brian Chen, DO",
            },
        ],
    }


def generate_content_summary(title: str, body: str) -> str:
    return (
        f"{title}: {body} In practical terms, this topic helps frame what a "
        "patient may want to ask their clinician, which values matter, and why "
        "a single number should be interpreted alongside the full risk profile."
    )
