import json
import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.schemas import AnswerPayload
from app.services.ai import (
    azure_chat_endpoint,
    is_foundry_models_endpoint,
)


logger = logging.getLogger("hearthealth.recommendations")

HEART_PLAN_DISCLAIMER = (
    "This Heart Plan is educational cardiology information based on your entered "
    "risk signals and curated source priorities. It is not medical advice, "
    "diagnosis, or treatment. Discuss personal decisions with a qualified clinician."
)

APPROVED_CITATIONS = {
    "source_aha_acc_prevention": {
        "title": "AHA/ACC Cardiovascular Prevention Guidance",
        "source_id": "source_aha_acc_prevention",
        "author": "AHA/ACC",
        "source_url": "https://www.acc.org/Guidelines/Hubs/Prevention",
    },
    "source_aha_life_essential8": {
        "title": "American Heart Association Life's Essential 8",
        "source_id": "source_aha_life_essential8",
        "author": "American Heart Association",
        "source_url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8",
    },
    "source_esc_prevention": {
        "title": "ESC Cardiovascular Disease Prevention Guidance",
        "source_id": "source_esc_prevention",
        "author": "European Society of Cardiology",
        "source_url": "https://www.escardio.org/Guidelines/Clinical-Practice-Guidelines/CVD-Prevention-in-clinical-practice",
    },
    "source_ne_jm_jama_evidence": {
        "title": "NEJM and JAMA Cardiovascular Evidence",
        "source_id": "source_ne_jm_jama_evidence",
        "author": "NEJM/JAMA",
        "source_url": "https://www.nejm.org/cardiology",
    },
}

LEARNING_RESOURCES = {
    "aha_saturated_fats": {
        "resource_id": "aha_saturated_fats",
        "title": "Saturated Fats",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/saturated-fats",
        "topic": "Nutrition",
        "applies_to": ["ldl", "saturated_fat", "cholesterol"],
        "priority": 1,
    },
    "aha_mediterranean_diet": {
        "resource_id": "aha_mediterranean_diet",
        "title": "What is the Mediterranean Diet?",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/nutrition-basics/mediterranean-diet",
        "topic": "Nutrition",
        "applies_to": ["ldl", "diet_pattern", "mediterranean", "triglycerides"],
        "priority": 2,
    },
    "aha_life_essential8": {
        "resource_id": "aha_life_essential8",
        "title": "Life's Essential 8",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/lifes-essential-8",
        "topic": "Lifestyle",
        "applies_to": ["blood_pressure", "glucose", "cholesterol", "weight", "prevention"],
        "priority": 3,
    },
    "aha_physical_activity_adults": {
        "resource_id": "aha_physical_activity_adults",
        "title": "American Heart Association Recommendations for Physical Activity",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/exercise-and-physical-activity/fitness-basics/aha-recs-for-physical-activity-in-adults",
        "topic": "Fitness",
        "applies_to": ["exercise", "aerobic", "strength", "activity"],
        "priority": 1,
    },
    "aha_sleep": {
        "resource_id": "aha_sleep",
        "title": "Sleep",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/sleep",
        "topic": "Lifestyle",
        "applies_to": ["sleep"],
        "priority": 1,
    },
    "aha_stress_management": {
        "resource_id": "aha_stress_management",
        "title": "Stress Management",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/stress-management",
        "topic": "Lifestyle",
        "applies_to": ["stress"],
        "priority": 1,
    },
    "aha_home_bp_monitoring": {
        "resource_id": "aha_home_bp_monitoring",
        "title": "Monitoring Your Blood Pressure at Home",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings/monitoring-your-blood-pressure-at-home",
        "topic": "Lifestyle",
        "applies_to": ["home_bp", "blood_pressure"],
        "priority": 1,
    },
    "aha_quit_smoking": {
        "resource_id": "aha_quit_smoking",
        "title": "Quit Smoking, Tobacco and Vaping",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/healthy-living/healthy-lifestyle/quit-smoking-tobacco-vaping",
        "topic": "Lifestyle",
        "applies_to": ["smoking", "nicotine", "tobacco"],
        "priority": 1,
    },
    "aha_diabetes": {
        "resource_id": "aha_diabetes",
        "title": "Diabetes and Your Heart",
        "source": "American Heart Association",
        "url": "https://www.heart.org/en/health-topics/diabetes",
        "topic": "Nutrition",
        "applies_to": ["diabetes", "a1c", "glucose", "cardiometabolic"],
        "priority": 2,
    },
    "acc_prevention_hub": {
        "resource_id": "acc_prevention_hub",
        "title": "Cardiovascular Prevention Guidelines Hub",
        "source": "American College of Cardiology",
        "url": "https://www.acc.org/Guidelines/Hubs/Prevention",
        "topic": "Cardiology",
        "applies_to": ["prevention", "risk", "testing", "clinician_discussion"],
        "priority": 9,
    },
}

SECTION_TITLES = {
    "nutrition": "Nutrition",
    "fitness": "Fitness",
    "lifestyle": "Lifestyle",
}

HEART_PLAN_SYSTEM_PROMPT = """You are HeartHealth AI's cardiology education planner.

Create source-grounded educational cards for a post-assessment Heart Plan. Stay focused on cardiovascular health: nutrition, fitness, and lifestyle choices that affect cardiac risk factors.

You must not diagnose, prescribe, recommend medication changes, give emergency advice, or present instructions as a treatment plan. You must cite only the approved sources provided by source_id. Do not cite WebMD or generic consumer-health sites.

Return JSON only."""


def generate_heart_plan(
    answers: AnswerPayload,
    risk: dict,
    settings: Settings | None = None,
) -> dict:
    active_settings = settings or get_settings()
    provider = active_settings.ai_provider.strip().lower()
    logger.info("Heart Plan provider selected provider=%s", provider)

    if provider == "azure_openai":
        try:
            return generate_azure_heart_plan(answers, risk, active_settings)
        except Exception:
            logger.exception("Heart Plan provider failed provider=azure_openai using=local")
            return generate_dummy_heart_plan(answers, risk)
    if provider == "dummy":
        return generate_dummy_heart_plan(answers, risk)

    raise ValueError(f"Unsupported AI provider: {active_settings.ai_provider}")


def generate_azure_heart_plan(
    answers: AnswerPayload,
    risk: dict,
    settings: Settings,
) -> dict:
    endpoint = settings.azure_openai_endpoint.rstrip("/")
    deployment = settings.azure_openai_deployment.strip()
    api_key = settings.azure_openai_api_key.strip()
    if not endpoint or not deployment or not api_key:
        raise ValueError(
            "Azure OpenAI requires AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_DEPLOYMENT, and AZURE_OPENAI_API_KEY."
        )

    url, api_version = azure_chat_endpoint(endpoint, deployment, settings.azure_openai_api_version)
    payload: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": HEART_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": build_heart_plan_prompt(answers, risk)},
        ],
        "temperature": 0.2,
        "max_tokens": settings.azure_openai_max_tokens,
        "response_format": {"type": "json_object"},
    }
    if is_foundry_models_endpoint(endpoint):
        payload["model"] = deployment

    logger.info(
        "Heart Plan request starting provider=azure_openai deployment=%s api_version=%s",
        deployment,
        api_version,
    )
    with httpx.Client(timeout=settings.azure_openai_timeout_seconds) as client:
        response = client.post(
            url,
            params={"api-version": api_version},
            headers={"Content-Type": "application/json", "api-key": api_key},
            json=payload,
        )
        logger.info(
            "Heart Plan response received provider=azure_openai status_code=%s request_id=%s",
            response.status_code,
            response.headers.get("x-ms-request-id")
            or response.headers.get("apim-request-id")
            or "unavailable",
        )
        response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return normalize_heart_plan(parsed, default_plan=generate_dummy_heart_plan(answers, risk))


def build_heart_plan_prompt(answers: AnswerPayload, risk: dict) -> str:
    safe_context = {
        "age": answers.age,
        "sex": answers.sex,
        "systolic_bp": answers.systolic_bp,
        "diastolic_bp": answers.diastolic_bp,
        "ldl_cholesterol": answers.ldl_cholesterol,
        "hdl_cholesterol": answers.hdl_cholesterol,
        "triglycerides": answers.triglycerides,
        "a1c_percent": answers.a1c_percent,
        "smoking_status": answers.smoking_status,
        "diabetes": answers.diabetes,
        "established_ascvd": answers.established_ascvd,
        "cac_score": answers.cac_score,
        "atrial_fibrillation_history": answers.atrial_fibrillation_history,
    }
    return f"""Create a Heart Plan for this completed cardiovascular risk assessment.

Assessment context:
{json.dumps(safe_context, ensure_ascii=True)}

Calculated scores and signals:
{json.dumps(risk, ensure_ascii=True)}

Approved source priorities:
{json.dumps(list(APPROVED_CITATIONS.values()), ensure_ascii=True)}

Approved learning resources:
{json.dumps(list(LEARNING_RESOURCES.values()), ensure_ascii=True)}

Return JSON only with this shape:
{{
  "sections": [
    {{
      "section": "nutrition",
      "title": "Nutrition",
      "cards": [
        {{
          "title": "Short cardiology-focused title",
          "priority": "high|medium|low",
          "trigger_signals": ["LDL Cholesterol"],
          "why_it_matters": "Plain-English explanation.",
          "educational_next_step": "Educational next step, not medical advice.",
          "learning_resource_id": "aha_saturated_fats",
          "clinician_question": "Question the user could ask a clinician.",
          "citations": [{{"source_id": "source_aha_acc_prevention"}}]
        }}
      ]
    }}
  ],
  "disclaimer": "Educational-only disclaimer."
}}

Rules:
- Include exactly three sections: nutrition, fitness, lifestyle.
- Include 2-4 cards per section.
- Stay cardiology-specific.
- Select exactly one approved learning_resource_id for each card.
- Cite only approved source_id values.
- Do not mention account creation, subscriptions, payments, or locked features.
- Do not recommend specific medications, supplements, procedures, or treatment changes."""


def normalize_heart_plan(parsed: dict, default_plan: dict) -> dict:
    sections = parsed.get("sections")
    if not isinstance(sections, list):
        return default_plan

    normalized_sections = []
    for section_name in ("nutrition", "fitness", "lifestyle"):
        raw_section = next(
            (
                section
                for section in sections
                if isinstance(section, dict) and section.get("section") == section_name
            ),
            None,
        )
        if not raw_section:
            return default_plan

        cards = raw_section.get("cards")
        if not isinstance(cards, list) or not cards:
            return default_plan

        normalized_cards = []
        for raw_card in cards[:4]:
            if not isinstance(raw_card, dict):
                continue
            citations = normalize_citations(raw_card.get("citations"))
            if not citations:
                citations = default_citations_for(section_name)
            learning_resource = normalize_learning_resource(
                raw_card.get("learning_resource_id") or raw_card.get("learning_resource"),
                default_learning_resource_for_card(raw_card, section_name),
            )
            normalized_cards.append(
                {
                    "title": str(raw_card.get("title") or "Cardiology education focus"),
                    "priority": normalize_priority(raw_card.get("priority")),
                    "trigger_signals": normalize_string_list(raw_card.get("trigger_signals")),
                    "why_it_matters": str(raw_card.get("why_it_matters") or ""),
                    "educational_next_step": str(raw_card.get("educational_next_step") or ""),
                    "learning_resource": learning_resource,
                    "clinician_question": str(raw_card.get("clinician_question") or ""),
                    "citations": citations,
                    "disclaimer": HEART_PLAN_DISCLAIMER,
                }
            )
        if len(normalized_cards) < 2:
            return default_plan
        normalized_sections.append(
            {
                "section": section_name,
                "title": SECTION_TITLES[section_name],
                "cards": normalized_cards,
            }
        )

    return {
        "sections": normalized_sections,
        "disclaimer": str(parsed.get("disclaimer") or HEART_PLAN_DISCLAIMER),
        "generated_by": "azure_openai",
    }


def generate_dummy_heart_plan(answers: AnswerPayload, risk: dict) -> dict:
    nutrition_cards = [
        ldl_nutrition_card(answers),
        blood_pressure_nutrition_card(answers),
    ]
    if answers.triglycerides is not None and answers.triglycerides >= 175:
        nutrition_cards.append(triglyceride_nutrition_card(answers))
    if answers.diabetes == "yes" or (
        answers.a1c_percent is not None and answers.a1c_percent >= 5.7
    ):
        nutrition_cards.append(glucose_nutrition_card(answers))

    fitness_cards = [
        aerobic_fitness_card(answers),
        resistance_fitness_card(),
    ]
    if answers.systolic_bp >= 130 or answers.diastolic_bp >= 80:
        fitness_cards.append(bp_fitness_card(answers))
    if answers.established_ascvd or answers.atrial_fibrillation_history:
        fitness_cards.append(cardiology_fitness_safety_card(answers))

    lifestyle_cards = [
        sleep_stress_card(),
        follow_up_card(answers),
    ]
    if answers.smoking_status == "current":
        lifestyle_cards.insert(0, smoking_lifestyle_card())
    if answers.cac_score is not None or answers.atrial_fibrillation_history:
        lifestyle_cards.append(test_context_card(answers))
    if answers.systolic_bp >= 130 or answers.diastolic_bp >= 80:
        lifestyle_cards.append(home_bp_card(answers))

    return {
        "sections": [
            section("nutrition", nutrition_cards[:4]),
            section("fitness", fitness_cards[:4]),
            section("lifestyle", lifestyle_cards[:4]),
        ],
        "disclaimer": HEART_PLAN_DISCLAIMER,
        "generated_by": "dummy",
    }


def section(section_name: str, cards: list[dict]) -> dict:
    return {
        "section": section_name,
        "title": SECTION_TITLES[section_name],
        "cards": cards,
    }


def card(
    title: str,
    priority: str,
    trigger_signals: list[str],
    why_it_matters: str,
    educational_next_step: str,
    learning_resource_id: str,
    clinician_question: str,
    citations: list[dict],
) -> dict:
    return {
        "title": title,
        "priority": priority,
        "trigger_signals": trigger_signals,
        "why_it_matters": why_it_matters,
        "educational_next_step": educational_next_step,
        "learning_resource": LEARNING_RESOURCES[learning_resource_id],
        "clinician_question": clinician_question,
        "citations": citations,
        "disclaimer": HEART_PLAN_DISCLAIMER,
    }


def ldl_nutrition_card(answers: AnswerPayload) -> dict:
    priority = "high" if answers.ldl_cholesterol >= 160 or answers.established_ascvd else "medium"
    return card(
        "Make LDL a nutrition priority",
        priority,
        ["LDL Cholesterol"],
        (
            "LDL is one of the clearest nutrition-linked signals in cardiovascular "
            "risk discussions, especially when it is elevated or secondary prevention applies."
        ),
        (
            "Use this as a prompt to learn about saturated fat, fiber-rich foods, "
            "and Mediterranean or DASH-style eating patterns from cardiology sources."
        ),
        "aha_saturated_fats",
        "What LDL goal should I discuss given my overall risk profile?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_esc_prevention"]],
    )


def blood_pressure_nutrition_card(answers: AnswerPayload) -> dict:
    elevated = answers.systolic_bp >= 130 or answers.diastolic_bp >= 80
    return card(
        "Connect sodium and blood pressure",
        "high" if elevated else "low",
        ["Blood Pressure"] if elevated else ["Blood Pressure baseline"],
        (
            "Blood pressure is a major cardiovascular risk factor, and eating patterns "
            "can influence it over time."
        ),
        (
            "Review cardiology-backed education on sodium awareness, potassium-rich "
            "foods when appropriate, and DASH-style patterns."
        ),
        "aha_home_bp_monitoring",
        "Would home blood pressure tracking help interpret my readings?",
        [APPROVED_CITATIONS["source_aha_life_essential8"], APPROVED_CITATIONS["source_aha_acc_prevention"]],
    )


def triglyceride_nutrition_card(answers: AnswerPayload) -> dict:
    return card(
        "Put triglycerides in cardiometabolic context",
        "medium",
        ["Triglycerides"],
        "Elevated triglycerides can travel with insulin resistance, alcohol intake, diet pattern, and broader metabolic risk.",
        "Use this as an education cue to review added sugars, refined carbohydrates, alcohol, and weight-related risk context.",
        "aha_mediterranean_diet",
        "Are my triglycerides persistent enough to change my prevention conversation?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_ne_jm_jama_evidence"]],
    )


def glucose_nutrition_card(answers: AnswerPayload) -> dict:
    return card(
        "Link glucose patterns to heart risk",
        "medium",
        ["Diabetes" if answers.diabetes == "yes" else "A1c"],
        "Diabetes and prediabetes patterns can materially change cardiovascular prevention discussions.",
        "Focus education on cardiometabolic eating patterns rather than one-off foods or supplement claims.",
        "aha_diabetes",
        "How should my glucose or A1c history affect my heart prevention plan?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_aha_life_essential8"]],
    )


def aerobic_fitness_card(answers: AnswerPayload) -> dict:
    return card(
        "Build around steady aerobic activity",
        "medium",
        ["Overall cardiovascular risk"],
        "Regular aerobic activity is central to cardiovascular health, blood pressure, insulin sensitivity, and fitness capacity.",
        "Learn about gradual, sustainable activity routines and how intensity should be individualized.",
        "aha_physical_activity_adults",
        "Are there any symptoms or history that should change how I start exercising?",
        [APPROVED_CITATIONS["source_aha_life_essential8"], APPROVED_CITATIONS["source_esc_prevention"]],
    )


def resistance_fitness_card() -> dict:
    return card(
        "Include strength training context",
        "low",
        ["Lifestyle risk reduction"],
        "Resistance training can support metabolic health, function, and long-term activity habits.",
        "Pair strength education with aerobic activity instead of treating exercise as a single category.",
        "aha_physical_activity_adults",
        "What kind of resistance training is appropriate for my age, history, and symptoms?",
        [APPROVED_CITATIONS["source_aha_life_essential8"]],
    )


def bp_fitness_card(answers: AnswerPayload) -> dict:
    return card(
        "Exercise and blood pressure deserve context",
        "medium",
        ["Blood Pressure"],
        "Elevated blood pressure can affect how people think about exercise intensity and monitoring.",
        "Use cardiology education to understand gradual conditioning, warmups, and why repeated BP readings matter.",
        "aha_physical_activity_adults",
        "Should I monitor blood pressure around exercise or adjust intensity based on my readings?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_esc_prevention"]],
    )


def cardiology_fitness_safety_card(answers: AnswerPayload) -> dict:
    trigger = "Atrial Fibrillation History" if answers.atrial_fibrillation_history else "Established ASCVD"
    return card(
        "Ask about exercise safety boundaries",
        "high",
        [trigger],
        "A prior cardiovascular event or rhythm history can change how exercise questions should be framed.",
        "Treat this as a discussion prompt, not a restriction: the goal is safe, individualized activity planning.",
        "acc_prevention_hub",
        "Are there any exercise limits or warning symptoms I should know about?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_esc_prevention"]],
    )


def smoking_lifestyle_card() -> dict:
    return card(
        "Make nicotine exposure a top lifestyle signal",
        "high",
        ["Smoking Status"],
        "Current smoking is one of the strongest modifiable cardiovascular risk factors.",
        "Use trusted cardiology education to understand why quitting support matters and what options to discuss clinically.",
        "aha_quit_smoking",
        "What smoking cessation supports would fit my situation?",
        [APPROVED_CITATIONS["source_aha_life_essential8"], APPROVED_CITATIONS["source_aha_acc_prevention"]],
    )


def sleep_stress_card() -> dict:
    return card(
        "Do not ignore sleep and stress",
        "low",
        ["Lifestyle context"],
        "Sleep and stress can influence blood pressure, activity consistency, eating patterns, and cardiometabolic health.",
        "Frame these as cardiovascular health inputs, especially when other risk factors are present.",
        "aha_sleep",
        "Could sleep quality, stress, or possible sleep apnea be affecting my risk factors?",
        [APPROVED_CITATIONS["source_aha_life_essential8"]],
    )


def follow_up_card(answers: AnswerPayload) -> dict:
    return card(
        "Turn results into better clinician questions",
        "medium",
        ["Risk Factors", "Protective Signals"],
        "The most useful next step is often a clearer conversation about which risk signals matter most.",
        "Bring your risk factors, protective signals, and any advanced labs or cardiac tests to a clinician discussion.",
        "acc_prevention_hub",
        "Which of my risk factors should we focus on first, and what should we recheck?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_ne_jm_jama_evidence"]],
    )


def home_bp_card(answers: AnswerPayload) -> dict:
    return card(
        "Use repeated readings, not one number",
        "medium",
        ["Blood Pressure"],
        "Blood pressure decisions usually depend on patterns over time, not a single isolated reading.",
        "Learn how home readings can support a more accurate conversation when reviewed with a clinician.",
        "aha_home_bp_monitoring",
        "What home blood pressure process should I use before my next visit?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"]],
    )


def test_context_card(answers: AnswerPayload) -> dict:
    triggers = []
    if answers.cac_score is not None:
        triggers.append("CAC Score")
    if answers.atrial_fibrillation_history:
        triggers.append("Atrial Fibrillation History")
    return card(
        "Keep cardiac test results in context",
        "medium",
        triggers,
        "Cardiac testing can reframe risk, but results need to be interpreted with the full clinical picture.",
        "Use cardiology-specific sources and Dr. Chen-reviewed content as the product grows, especially for testing questions.",
        "acc_prevention_hub",
        "How should this test result change my prevention or follow-up discussion?",
        [APPROVED_CITATIONS["source_aha_acc_prevention"], APPROVED_CITATIONS["source_esc_prevention"]],
    )


def normalize_citations(raw_citations: Any) -> list[dict]:
    if not isinstance(raw_citations, list):
        return []

    citations = []
    seen = set()
    for raw in raw_citations:
        source_id = raw.get("source_id") if isinstance(raw, dict) else None
        if source_id in APPROVED_CITATIONS and source_id not in seen:
            citations.append(APPROVED_CITATIONS[source_id])
            seen.add(source_id)
    return citations


def default_citations_for(section_name: str) -> list[dict]:
    if section_name == "nutrition":
        return [APPROVED_CITATIONS["source_aha_acc_prevention"]]
    if section_name == "fitness":
        return [APPROVED_CITATIONS["source_aha_life_essential8"]]
    return [APPROVED_CITATIONS["source_aha_acc_prevention"]]


def normalize_learning_resource(raw_resource: Any, default_resource_id: str) -> dict:
    resource_id = raw_resource
    if isinstance(raw_resource, dict):
        resource_id = raw_resource.get("resource_id")
    if resource_id in LEARNING_RESOURCES:
        return LEARNING_RESOURCES[str(resource_id)]
    return LEARNING_RESOURCES[default_resource_id]


def default_learning_resource_for_card(raw_card: dict, section_name: str) -> str:
    haystack = " ".join(
        [
            str(raw_card.get("title") or ""),
            str(raw_card.get("educational_next_step") or ""),
            " ".join(normalize_string_list(raw_card.get("trigger_signals"))),
        ]
    ).lower()

    if "smoking" in haystack or "nicotine" in haystack or "tobacco" in haystack:
        return "aha_quit_smoking"
    if "home blood pressure" in haystack or "home bp" in haystack:
        return "aha_home_bp_monitoring"
    if "blood pressure" in haystack or "sodium" in haystack:
        return "aha_home_bp_monitoring"
    if "diabetes" in haystack or "glucose" in haystack or "a1c" in haystack:
        return "aha_diabetes"
    if "triglyceride" in haystack or "mediterranean" in haystack:
        return "aha_mediterranean_diet"
    if "ldl" in haystack or "saturated fat" in haystack or "cholesterol" in haystack:
        return "aha_saturated_fats"
    if "stress" in haystack:
        return "aha_stress_management"
    if "sleep" in haystack:
        return "aha_sleep"
    if "exercise" in haystack or "activity" in haystack or "strength" in haystack:
        return "aha_physical_activity_adults"
    if "cac" in haystack or "atrial fibrillation" in haystack or "test" in haystack:
        return "acc_prevention_hub"
    if section_name == "fitness":
        return "aha_physical_activity_adults"
    if section_name == "nutrition":
        return "aha_mediterranean_diet"
    return "aha_life_essential8"


def normalize_priority(raw_priority: Any) -> str:
    priority = str(raw_priority or "medium").lower()
    return priority if priority in {"high", "medium", "low"} else "medium"


def normalize_string_list(raw_items: Any) -> list[str]:
    if not isinstance(raw_items, list):
        return []
    return [str(item) for item in raw_items if str(item).strip()]


def enrich_citations(sections: list[dict]) -> list[dict]:
    enriched_sections = []
    for section in sections:
        enriched_cards = []
        for card in section.get("cards", []):
            enriched_card = {**card}
            enriched_card["citations"] = normalize_citations(card.get("citations"))
            enriched_card["learning_resource"] = normalize_learning_resource(
                card.get("learning_resource"),
                default_learning_resource_for_card(card, section.get("section", "lifestyle")),
            )
            enriched_cards.append(enriched_card)
        enriched_sections.append({**section, "cards": enriched_cards})
    return enriched_sections
