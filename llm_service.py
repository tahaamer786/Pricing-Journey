"""
Vertex AI (Gemini 2.5 Flash) integration.

Requires:
- GOOGLE_APPLICATION_CREDENTIALS pointing to a valid service_account.json
- GCP_PROJECT_ID and GCP_LOCATION set in .env
"""
import json
import logging
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_initialized = False


def _ensure_init():
    global _initialized
    if not _initialized:
        from google.oauth2 import service_account
        creds_path = settings.google_application_credentials
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.gcp_location,
            credentials=credentials,
        )
        _initialized = True

PERSONA_SYSTEM_CONTEXT = """
You are analyzing a prospective client for Jubala.ai, an AI voice agent product
built specifically for UK immigration and education law firms. Your job is to
assess the business described below and generate a structured persona report.

Always respond with ONLY valid JSON, no markdown, no commentary, matching this
exact shape:

{
  "business_summary": {
    "company_name": string,
    "industry": string,
    "specialization": string,
    "team_size": string,
    "location": string
  },
  "legal_needs": {
    "primary_practice_area": string,
    "secondary_areas": [string],
    "client_volume": string,
    "pain_points": [string]
  },
  "recommended_plan": {
    "plan_name": string,
    "reasoning": string
  },
  "ai_assessment_notes": string
}
"""


async def generate_persona(
    google_profile: dict,
    website_content: Optional[str] = None,
    qa_text: Optional[str] = None,
) -> dict:
    """
    Calls Gemini 2.5 Flash via Vertex AI and returns the parsed persona dict.
    Exactly one of website_content / qa_text should be provided.
    """
    _ensure_init()
    model = GenerativeModel(settings.gemini_model)

    source_block = (
        f"Website content:\n{website_content}"
        if website_content
        else f"Questionnaire answers:\n{qa_text}"
    )

    prompt = f"""{PERSONA_SYSTEM_CONTEXT}

User's Google profile:
{json.dumps(google_profile, indent=2)}

{source_block}
"""

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Strip markdown code fences if the model wraps the JSON in them
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}\nRaw: {raw_text}")
        # Fallback minimal structure so the flow doesn't crash
        return {
            "business_summary": {
                "company_name": google_profile.get("first_name", "Unknown"),
                "industry": "Unknown",
                "specialization": "Unknown",
                "team_size": "Unknown",
                "location": "Unknown",
            },
            "legal_needs": {
                "primary_practice_area": "Unknown",
                "secondary_areas": [],
                "client_volume": "Unknown",
                "pain_points": [],
            },
            "recommended_plan": {"plan_name": "Unknown", "reasoning": "Could not parse AI response"},
            "ai_assessment_notes": raw_text,
        }
