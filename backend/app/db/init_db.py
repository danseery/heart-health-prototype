from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import Base, engine
from app.models import ConsentRecord, ContentItem, User, new_id


DEMO_USER_ID = "usr_demo"


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates()
    with Session(engine) as db:
        seed_demo_data(db)


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


def seed_demo_data(db: Session) -> None:
    if not db.get(User, DEMO_USER_ID):
        db.add(
            User(
                id=DEMO_USER_ID,
                email="demo@hearthealth.ai",
                display_name="Demo User",
            )
        )
        db.add(
            ConsentRecord(
                id=new_id("consent"),
                user_id=DEMO_USER_ID,
                consent_type="educational_use",
                version="2026-06-local",
            )
        )

    existing_content = db.scalar(select(ContentItem.id).limit(1))
    if not existing_content:
        db.add_all(
            [
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
            ]
        )

    db.commit()
