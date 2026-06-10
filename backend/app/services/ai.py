from app.schemas import AnswerPayload


EDUCATIONAL_DISCLAIMER = (
    "This is educational information based on simplified calculations and curated "
    "content. It is not medical advice, diagnosis, or treatment. Discuss personal "
    "medical decisions with a qualified clinician."
)


def generate_assessment_summary(answers: AnswerPayload, risk: dict) -> dict:
    primary = risk["risk_factors"][0]
    summary = (
        f"Your estimated 10-year ASCVD-style risk is {risk['ascvd_risk']}%, "
        f"which is categorized as {risk['category']}. The most notable signal in "
        f"this demo assessment is {primary['label'].lower()} ({primary['value']}). "
        "These calculations are simplified, but they show how "
        "the product can translate clinical-style inputs into plain-language guidance."
    )
    if answers.smoking_status == "current":
        summary += " Smoking status is also highlighted because it can materially affect cardiovascular risk."

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
