from sqlalchemy.orm import Session

from app.db.session import Base, engine
from app.models import ConsentRecord, ContentItem, User, new_id


OPEN_SESSION_USER_ID = "usr_open_session"


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    with Session(engine) as db:
        seed_open_session_data(db)


def ensure_schema_updates() -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as conn:
        risk_result_columns = {
            row[1] for row in conn.exec_driver_sql("PRAGMA table_info(risk_results)")
        }
        if "protective_signals" not in risk_result_columns:
            conn.exec_driver_sql(
                "ALTER TABLE risk_results ADD COLUMN protective_signals JSON NOT NULL DEFAULT '[]'"
            )


def seed_open_session_data(db: Session) -> None:
    if not db.get(User, OPEN_SESSION_USER_ID):
        db.add(
            User(
                id=OPEN_SESSION_USER_ID,
                email="open-session@hearthealth.ai",
                display_name="Open Session User",
            )
        )
        db.add(
            ConsentRecord(
                id=new_id("consent"),
                user_id=OPEN_SESSION_USER_ID,
                consent_type="educational_use",
                version="2026-06-local",
            )
        )

    ensure_content_item(
        db,
        ContentItem(
            id="content_cholesterol_basics",
            topic="Cholesterol",
            title="Understanding LDL and HDL Cholesterol",
            content_type="guide",
            author="Dr. Brian Chen, DO",
            body=(
                "LDL cholesterol is one of several risk factors clinicians use "
                "when estimating future cardiovascular risk. HDL, blood pressure, "
                "age, diabetes, and smoking status also matter."
            ),
        ),
    )
    ensure_content_item(
        db,
        ContentItem(
            id="content_bp_basics",
            topic="Hypertension",
            title="Blood Pressure Numbers Explained",
            content_type="guide",
            author="Dr. Brian Chen, DO",
            body=(
                "Blood pressure readings include systolic and diastolic values. "
                "Repeated elevated readings are worth discussing with a clinician."
            ),
        ),
    )
    ensure_content_item(
        db,
        ContentItem(
            id="source_aha_acc_prevention",
            topic="Source",
            title="AHA/ACC Cardiovascular Prevention Guidance",
            content_type="source",
            author="AHA/ACC",
            body=(
                "The American Heart Association and American College of Cardiology "
                "publish major United States cardiovascular prevention guidance. "
                "HeartHealth AI prioritizes these sources for general cardiology "
                "education and risk-factor context."
            ),
        ),
    )
    ensure_content_item(
        db,
        ContentItem(
            id="source_aha_life_essential8",
            topic="Source",
            title="American Heart Association Life's Essential 8",
            content_type="source",
            author="American Heart Association",
            body=(
                "AHA Life's Essential 8 frames cardiovascular health around nutrition, "
                "physical activity, nicotine exposure, sleep, weight, cholesterol, "
                "blood glucose, and blood pressure."
            ),
        ),
    )
    ensure_content_item(
        db,
        ContentItem(
            id="source_esc_prevention",
            topic="Source",
            title="ESC Cardiovascular Disease Prevention Guidance",
            content_type="source",
            author="European Society of Cardiology",
            body=(
                "The European Society of Cardiology publishes prevention guidance "
                "that is useful for broad cardiology education and lifestyle context."
            ),
        ),
    )
    ensure_content_item(
        db,
        ContentItem(
            id="source_ne_jm_jama_evidence",
            topic="Source",
            title="NEJM and JAMA Cardiovascular Evidence",
            content_type="source",
            author="NEJM/JAMA",
            body=(
                "Major peer-reviewed cardiovascular studies and reviews in NEJM and "
                "JAMA provide high-quality evidence context for cardiology education."
            ),
        )
    )

    db.commit()


def ensure_content_item(db: Session, item: ContentItem) -> None:
    if not db.get(ContentItem, item.id):
        db.add(item)
