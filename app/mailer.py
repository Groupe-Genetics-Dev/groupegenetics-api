"""Envoi des e-mails par SMTP (ex. Hostinger : smtp.hostinger.com, port 465, SSL)."""

import asyncio
import html as html_lib
import logging
import os
import re
import smtplib
import socket
import ssl
from email.message import EmailMessage
from types import SimpleNamespace
from email.utils import formataddr, make_msgid

from dotenv import load_dotenv
from sqlalchemy import inspect as sa_inspect

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com").strip().strip("\"'")
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
# Liens insérés dans les e-mails
SITE_LOGIN_URL = os.getenv("SITE_LOGIN_URL", "http://localhost:3001/support/login")
ADMIN_ACCOUNTS_URL = os.getenv("ADMIN_ACCOUNTS_URL", "http://localhost:3001/support/admin/accounts")
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


def _send_quietly(send, *args) -> None:
    try:
        asyncio.run(send(*args))
    except Exception:
        logging.getLogger(__name__).exception("Envoi de l'e-mail %s impossible", send.__name__)


def _snapshot(value):
    """Copie les colonnes d'un objet SQLAlchemy : la session est fermée quand la tâche s'exécute."""
    state = sa_inspect(value, raiseerr=False)
    if state is None or not hasattr(state, "mapper"):
        return value
    return SimpleNamespace(**{attr.key: getattr(value, attr.key) for attr in state.mapper.column_attrs})


def send_in_background(background_tasks, send, *args) -> None:
    """Planifie l'envoi après la réponse HTTP : l'utilisateur n'attend pas le serveur SMTP
    et un échec d'envoi est seulement journalisé."""
    background_tasks.add_task(_send_quietly, send, *(_snapshot(a) for a in args))


def _diagnose(test_to: str | None) -> int:
    """Vérifie la configuration SMTP : python -m app.mailer [adresse-de-test]"""
    print(f"Serveur    : {SMTP_HOST}:{SMTP_PORT} ({SMTP_SECURITY})")
    print(f"Utilisateur: {SMTP_USER or '(vide)'}")
    print(f"Mot de passe: {len(SMTP_PASSWORD)} caractères"
          + (" - attention : espaces au début/à la fin" if SMTP_PASSWORD != SMTP_PASSWORD.strip() else "")
          + (" - attention : guillemets inclus" if SMTP_PASSWORD[:1] in "\"'" else ""))
    print(f"Expéditeur : {MAIL_FROM_NAME} <{MAIL_FROM}>")
    try:
        ip = socket.gethostbyname(SMTP_HOST)
        print(f"DNS        : {SMTP_HOST} -> {ip}")
    except socket.gaierror as e:
        print(f"❌ Nom de serveur introuvable ({SMTP_HOST!r}) : {e} - vérifiez SMTP_HOST dans le .env, "
              "puis le DNS de Docker (redémarrez Docker Desktop, désactivez le VPN)")
        return 1
    try:
        context = ssl.create_default_context()
        if SMTP_SECURITY == "ssl":
            smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=SMTP_TIMEOUT)
        else:
            smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT)
            if SMTP_SECURITY == "starttls":
                smtp.starttls(context=context)
        with smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            print("✅ Connexion SMTP réussie : identifiants corrects")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Identifiants refusés par le serveur ({e.smtp_code}) : vérifiez SMTP_USER et SMTP_PASSWORD")
        return 1
    except Exception as e:
        print(f"❌ Serveur injoignable : {e!r} (port bloqué par le réseau ? essayez 587 + starttls)")
        return 1
    if test_to:
        try:
            _send([test_to], "Test d'envoi - API Groupe Genetics", "<p>Ceci est un e-mail de test : l'envoi SMTP fonctionne.</p>")
        except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as e:
            print(f"❌ Envoi refusé : {e}")
            if MAIL_FROM.lower() != SMTP_USER.lower():
                print(f"   MAIL_FROM ({MAIL_FROM}) doit être la boîte SMTP_USER ({SMTP_USER}) ou un de ses alias")
            return 1
        print(f"✅ E-mail de test envoyé à {test_to}")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(_diagnose(sys.argv[1] if len(sys.argv) > 1 else None))
