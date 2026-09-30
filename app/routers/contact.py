from fastapi import APIRouter, BackgroundTasks, status
from app.mailer import send_in_background
from app.schemas.contact import ContactMessage
from app.utils import send_contact_email

router = APIRouter(prefix="/contact", tags=["Contact"])

@router.post("/send-email", status_code=status.HTTP_200_OK)
def contact_company(message: ContactMessage, background_tasks: BackgroundTasks):
    # Envoi après la réponse : le visiteur n'attend pas le serveur SMTP
    send_in_background(background_tasks, send_contact_email,
                       message.name, message.email, message.subject, message.message)
    return {"message": "Votre message a été envoyé avec succès. Nous vous contacterons bientôt."}
