"""Envoi des e-mails par SMTP (ex. Hostinger : smtp.hostinger.com, port 465, SSL)."""

import asyncio
import html as html_lib
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
# "ssl" (port 465), "starttls" (port 587) ou "none" (tests locaux uniquement)
SMTP_SECURITY = os.getenv("SMTP_SECURITY", "ssl").lower()
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_TIMEOUT = 20

# Expéditeur : doit être la boîte SMTP ou un alias autorisé de celle-ci
MAIL_FROM = os.getenv("MAIL_FROM") or SMTP_USER
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Groupe Genetics Support")


def _recipients(env_name: str, default: str) -> list[str]:
    return [a.strip() for a in os.getenv(env_name, default).split(",") if a.strip()]


# Destinataires internes
INCIDENT_ALERT_RECIPIENTS = _recipients("INCIDENT_ALERT_RECIPIENTS", "support@groupegenetics.com")
NEW_ACCOUNT_RECIPIENTS = _recipients("NEW_ACCOUNT_RECIPIENTS", "support@groupegenetics.com")
CONTACT_RECIPIENTS = _recipients("CONTACT_RECIPIENTS", "contact@groupegenetics.com,admin@groupegenetics.com")


def _html_to_text(html: str) -> str:
    text = re.sub(r"<(br|/p|/h\d|/li|/div)\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.I)
    text = html_lib.unescape(re.sub(r"<[^>]+>", "", text))
    lines = [line.strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _send(to: list[str], subject: str, html: str, reply_to: str | None = None) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP non configuré : renseignez SMTP_USER et SMTP_PASSWORD dans le .env")

    msg = EmailMessage()
    msg["From"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=MAIL_FROM.split("@")[-1])
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(_html_to_text(html))
    msg.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    if SMTP_SECURITY == "ssl":
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=SMTP_TIMEOUT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
            if SMTP_SECURITY == "starttls":
                smtp.starttls(context=context)
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)


async def send_email(to: list[str], subject: str, html: str, reply_to: str | None = None) -> None:
    """Envoie un e-mail HTML (avec version texte) sans bloquer la boucle asyncio."""
    await asyncio.to_thread(_send, to, subject, html, reply_to)
