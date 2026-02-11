from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from typing import Any

from aiosmtplib import SMTP
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config import settings


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    env = _get_env()
    template = env.get_template(template_name)
    return template.render(**context)


async def _send_email(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    if not settings.SMTP_HOST:
        return False

    message = EmailMessage()
    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "noreply@beehus.local"
    message["From"] = formataddr((settings.SMTP_FROM_NAME, from_email))
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_content)
    message.add_alternative(html_content, subtype="html")

    smtp = SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, use_tls=False)
    try:
        await smtp.connect()
        if settings.SMTP_USE_TLS:
            await smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.send_message(message)
        await smtp.quit()
        return True
    except Exception as exc:
        print(f"SMTP send failed: {exc}")
        try:
            await smtp.quit()
        except Exception:
            pass
        return False


async def send_invitation_email(
    to_email: str,
    invitation_link: str,
    invited_by: str,
    full_name: str,
) -> bool:
    context = {
        "full_name": full_name or "there",
        "invitation_link": invitation_link,
        "invited_by": invited_by,
    }
    html_content = _render_template("invitation.html", context)
    text_content = (
        f"Hello {context['full_name']},\n\n"
        f"You have been invited to Beehus Platform by {invited_by}.\n"
        f"Accept the invitation: {invitation_link}\n"
    )
    return await _send_email(to_email, "Your Beehus invitation", html_content, text_content)


async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    context = {"reset_link": reset_link}
    html_content = _render_template("password_reset.html", context)
    text_content = (
        "You requested a password reset.\n\n"
        f"Reset your password: {reset_link}\n"
    )
    return await _send_email(to_email, "Reset your Beehus password", html_content, text_content)
