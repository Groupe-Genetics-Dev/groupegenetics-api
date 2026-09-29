import pandas as pd
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from passlib.context import CryptContext
from random import randint
from html import escape

from app.mailer import CONTACT_RECIPIENTS, INCIDENT_ALERT_RECIPIENTS, NEW_ACCOUNT_RECIPIENTS, send_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashed(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def generate_otp():
    return f"{randint(100000, 999999)}"

async def send_otp_email(to_email: str, otp: str):
    subject = "🔐 Code OTP pour réinitialisation de mot de passe"
    html_content = f"""
    <div>
      <h2>Bonjour,</h2>
      <p>Voici votre code OTP pour réinitialiser votre mot de passe :</p>
      <h3>{otp}</h3>
      <p>Ce code est valable 5 minutes.</p>
      <p>Si vous n'avez pas demandé ce code, veuillez ignorer cet email.</p>
    </div>
    """
    await send_email([to_email], subject, html_content)


async def send_welcome_email(user):
    subject = "👋 Bienvenue sur l'espace support Groupe Genetics"
    html_content = f"""
    <div style="font-family: Arial, sans-serif;">
      <h2>Bonjour {escape(user.name)},</h2>
      <p>Votre compte sur l'espace support <strong>Groupe Genetics</strong> a bien été créé.</p>
      <p>Vous pouvez désormais vous connecter avec l'adresse <strong>{escape(user.email)}</strong> pour :</p>
      <ul>
        <li>déclarer vos incidents techniques ;</li>
        <li>suivre leur traitement en temps réel ;</li>
        <li>être informé par e-mail de leur résolution.</li>
      </ul>
      <p>Pour toute question, répondez simplement à cet e-mail.</p>
      <br/>
      <p>Cordialement,</p>
      <p>L'équipe Support Groupe Genetics</p>
    </div>
    """
    await send_email([user.email], subject, html_content)


async def send_new_account_admin_email(user):
    subject = f"🆕 Nouveau compte client : {user.name}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif;">
      <h2>🆕 Un nouveau compte a été créé sur l'espace support</h2>
      <ul>
        <li><strong>Nom :</strong> {escape(user.name)}</li>
        <li><strong>Email :</strong> {escape(user.email)}</li>
        <li><strong>Entreprise :</strong> {escape(user.company or "-")}</li>
        <li><strong>Téléphone :</strong> {escape(user.phone or "-")}</li>
        <li><strong>Date :</strong> {user.createdAt.strftime('%Y-%m-%d %H:%M:%S')}</li>
      </ul>
    </div>
    """
    await send_email(NEW_ACCOUNT_RECIPIENTS, subject, html_content, reply_to=user.email)


async def send_incident_alert_email(incident, user):
    subject = "🚨 Nouvel incident signalé sur la plateforme Groupe Genetics"

    html_content = f"""
    <div style="font-family: Arial, sans-serif;">
      <h2>🚨 Un nouvel incident a été signalé</h2>
      <p><strong><u>Détails de l'incident</u></strong></p>
      <ul>
        <li><strong>Titre :</strong> {escape(incident.title)}</li>
        <li><strong>Description :</strong> {escape(incident.description)}</li>
        <li><strong>Priorité :</strong> {incident.priority.value}</li>
        <li><strong>Catégorie :</strong> {incident.category.value}</li>
        <li><strong>Date :</strong> {incident.createdAt.strftime('%Y-%m-%d %H:%M:%S')}</li>
      </ul>
      <p><strong><u>Informations de l'utilisateur</u></strong></p>
      <ul>
        <li><strong>Nom :</strong> {escape(user.name)}</li>
        <li><strong>Email :</strong> {escape(user.email)}</li>
        <li><strong>Entreprise :</strong> {escape(user.company or "-")}</li>
        <li><strong>Téléphone :</strong> {escape(user.phone or "-")}</li>
      </ul>
    </div>
    """
    # "Répondre" dans la boîte support écrit directement au client
    await send_email(INCIDENT_ALERT_RECIPIENTS, subject, html_content, reply_to=user.email)


async def send_incident_resolved_email(user_email: str, user_name: str, incident_title: str):
    subject = "✅ Votre incident a été résolu"
    html_content = f"""
    <div>
      <h2>Bonjour {escape(user_name)},</h2>
      <p>Votre incident intitulé <strong>{escape(incident_title)}</strong> a été marqué comme <strong>terminé</strong> par notre équipe.</p>
      <p>Merci de bien vouloir vérifier et tester si le problème est résolu.</p>
      <p>Si vous rencontrez toujours un problème, n’hésitez pas à nous recontacter.</p>
      <br/>
      <p>Cordialement,</p>
      <p>L'équipe Support</p>
    </div>
    """
    await send_email([user_email], subject, html_content)


async def send_contact_email(name: str, email: str, subject: str, message: str):
    html_content = f"""
    <div>
      <h2>📩 Nouveau message de contact</h2>
      <p><strong>Nom :</strong> {escape(name)}</p>
      <p><strong>Email :</strong> {escape(email)}</p>
      <p><strong>Sujet :</strong> {escape(subject)}</p>
      <p><strong>Message :</strong></p>
      <p>{escape(message).replace(chr(10), "<br/>")}</p>
    </div>
    """
    # Le message part de notre boîte SMTP ; "Répondre" écrit au visiteur
    await send_email(CONTACT_RECIPIENTS, f"📩 Message de contact : {subject}", html_content, reply_to=email)




def generate_ceo_report(incident_data: list[dict]) -> BytesIO:
    df = pd.DataFrame(incident_data)
    df['createdAt'] = pd.to_datetime(df['createdAt'])

    total_incidents = len(df)
    status_counts = df['status'].value_counts().to_dict()
    priority_counts = df['priority'].value_counts().to_dict()
    top_users = df.groupby(['user_name', 'user_email']).size().reset_index(name='incident_count').sort_values(by='incident_count', ascending=False)

    # Graphique circulaire
    plt.figure(figsize=(4, 4))
    df['status'].value_counts().plot.pie(autopct='%1.1f%%', startangle=90)
    plt.title('Répartition des statuts')
    pie_chart = BytesIO()
    plt.savefig(pie_chart, format='png')
    plt.close()
    pie_chart.seek(0)

    # PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Rapport des Incidents - Vue CEO", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Date de génération: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Nombre total d'incidents: {total_incidents}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Statuts
    elements.append(Paragraph("Incidents par statut:", styles['Heading3']))
    for k, v in status_counts.items():
        elements.append(Paragraph(f"- {k}: {v}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Priorité
    elements.append(Paragraph("Incidents par priorité:", styles['Heading3']))
    for k, v in priority_counts.items():
        elements.append(Paragraph(f"- {k}: {v}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Top utilisateurs
    elements.append(Paragraph("Top utilisateurs :", styles['Heading3']))
    user_data = [["Nom", "Email", "Nombre d'incidents"]]
    for _, row in top_users.iterrows():
        user_data.append([row['user_name'], row['user_email'], row['incident_count']])

    table = Table(user_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Image
    elements.append(Paragraph("Graphique: Répartition des statuts", styles['Heading3']))
    elements.append(Image(pie_chart, width=3.5 * inch, height=3.5 * inch))
    doc.build(elements)

    buffer.seek(0)
    return buffer


