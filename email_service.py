"""Sends the persona report notification email to the Jubala team."""
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_persona_email_html(persona: dict, user: dict) -> str:
    biz = persona.get("business_summary", {})
    needs = persona.get("legal_needs", {})
    plan = persona.get("recommended_plan", {})
    notes = persona.get("ai_assessment_notes", "")

    pain_points_html = "".join(f"<li>{p}</li>" for p in needs.get("pain_points", []))
    secondary_html = ", ".join(needs.get("secondary_areas", [])) or "None"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>🆕 New Persona Report — {biz.get('company_name', 'Unknown')}</h2>

        <h3>👤 Contact Info</h3>
        <p>Name: {user.get('first_name', '')} {user.get('last_name', '')}<br>
        Email: {user.get('email', '')}</p>

        <h3>🏢 Business Info</h3>
        <p>
            Company: {biz.get('company_name', 'N/A')}<br>
            Industry: {biz.get('industry', 'N/A')}<br>
            Specialization: {biz.get('specialization', 'N/A')}<br>
            Location: {biz.get('location', 'N/A')}<br>
            Team Size: {biz.get('team_size', 'N/A')}
        </p>

        <h3>⚖️ Legal Needs</h3>
        <p>
            Primary Area: {needs.get('primary_practice_area', 'N/A')}<br>
            Secondary: {secondary_html}<br>
            Client Volume: {needs.get('client_volume', 'N/A')}
        </p>
        <ul>{pain_points_html}</ul>

        <h3>💡 AI Assessment</h3>
        <p>{notes}</p>

        <h3>📋 Recommended Plan</h3>
        <p><strong>{plan.get('plan_name', 'N/A')}</strong><br>
        Reason: {plan.get('reasoning', 'N/A')}</p>
    </body>
    </html>
    """


async def send_persona_email(persona: dict, user: dict) -> None:
    """Send the persona report to the Jubala team inbox."""
    try:
        html = _build_persona_email_html(persona, user)
        company_name = persona.get("business_summary", {}).get("company_name", "New Lead")

        msg = MIMEMultipart("alternative")
        msg["From"] = settings.from_email or settings.smtp_username
        msg["To"] = settings.jubala_team_email
        msg["Subject"] = f"🆕 New Persona Report — {company_name}"
        msg.attach(MIMEText(html, "html"))

        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=(settings.smtp_port == 587),
        )
        async with smtp:
            await smtp.login(settings.smtp_username, settings.smtp_password)
            await smtp.send_message(msg)

        logger.info(f"✅ Persona email sent for {company_name}")

    except Exception as e:
        logger.error(f"❌ Failed to send persona email: {e}")
        # Don't crash the request if email fails — persona is already saved
