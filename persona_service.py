"""Orchestrates the full persona generation flow: fetch context -> call LLM -> save -> email."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.persona import PersonaReport, PersonaQA, SourceType
from services.llm_service import generate_persona
from services.scraper_service import scrape_website
from services.email_service import send_persona_email

logger = logging.getLogger(__name__)


async def generate_and_save_persona(db: AsyncSession, user: User) -> PersonaReport:
    """
    Called after business-info step is complete for a user.
    Reads user.company_url (URL route) or existing PersonaQA answers (questions route),
    calls the LLM, saves the result, and emails the Jubala team.
    """
    google_profile = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }

    website_content = None
    qa_text = None
    source_type = SourceType.url if user.company_url else SourceType.questions

    if user.company_url:
        website_content = await scrape_website(user.company_url)
        if not website_content:
            # Scrape failed — this should ideally not happen if business-info
            # step validated the URL, but fail gracefully with a note.
            website_content = f"(Could not fetch content from {user.company_url})"
    else:
        # Pull answers submitted in the questions flow
        qa_stmt = select(PersonaQA).join(PersonaReport).where(PersonaReport.user_id == user.id)
        qa_result = await db.execute(qa_stmt)
        existing_qa = qa_result.scalars().all()
        qa_text = "\n".join(f"Q: {qa.question}\nA: {qa.answer}" for qa in existing_qa)

    persona_json = await generate_persona(
        google_profile=google_profile,
        website_content=website_content,
        qa_text=qa_text,
    )

    persona = PersonaReport(
        user_id=user.id,
        source_type=source_type,
        company_url=user.company_url,
        persona_json=persona_json,
    )
    db.add(persona)
    await db.commit()
    await db.refresh(persona)

    logger.info(f"✅ Persona report {persona.id} generated for user {user.id}")

    # Fire-and-forget style — email failure should not break the flow
    await send_persona_email(persona_json, google_profile)

    return persona
