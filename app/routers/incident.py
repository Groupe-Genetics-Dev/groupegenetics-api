import os
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
import logging

from app.mailer import send_in_background
from app.postgres_connect import get_db
from app.model import Incident, User
from app.schemas.incident import (
    IncidentCreate, IncidentOut, IncidentStatusUpdate, 
    IncidentUpdate, DateRange, IncidentStatus
)
from app.oauth2 import get_current_user, get_current_ceo_user
from app.utils import (
    generate_ceo_report, send_incident_alert_email, send_incident_resolved_email
)

# 📁 Dossier pour stocker les rapports PDF
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "../../reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

router = APIRouter(prefix="/incidents", tags=["Incidents"])
logger = logging.getLogger(__name__)

# ✅ Création d’un incident
@router.post("/create-incident", response_model=IncidentOut)
def create_incident(
    incident: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_incident = Incident(**incident.model_dump(), userId=current_user.id)
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)

    # Alerte envoyée après la réponse : l'incident est enregistré même si l'envoi échoue
    send_in_background(background_tasks, send_incident_alert_email, new_incident, current_user)
    return new_incident

# 📄 Liste des incidents de l’utilisateur connecté
@router.get("/list-incidents", response_model=list[IncidentOut])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Incident).filter(Incident.userId == current_user.id).all()

# 🔎 Détails d’un incident
@router.get("/get-incident/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).filter_by(id=incident_id, userId=current_user.id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    return incident

# ✏️ Modifier un incident
@router.put("/update-incident/{incident_id}", response_model=IncidentOut)
def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).filter_by(id=incident_id, userId=current_user.id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)
    return incident

# ❌ Supprimer un incident
@router.delete("/delete-incident/{incident_id}")
def delete_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    incident = db.query(Incident).filter_by(id=incident_id, userId=current_user.id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")

    db.delete(incident)
    db.commit()
    return {"message": "Incident supprimé avec succès"}

# 🔁 Changer le statut (CEO uniquement)
@router.patch("/update-status/{incident_id}", response_model=IncidentOut)
def update_incident_status(
    incident_id: UUID,
    payload: IncidentStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    __current_ceo: User = Depends(get_current_ceo_user)
):
    incident = db.query(Incident).filter_by(id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")

    incident.status = payload.status
    db.commit()
    db.refresh(incident)

    if payload.status == IncidentStatus.TERMINE:
        user = incident.user
        if user:
            send_in_background(background_tasks, send_incident_resolved_email, user.email, user.name, incident.title)

    return incident

# 📊 Tous les incidents (CEO)
@router.get("/all-incidents", response_model=list[IncidentOut])
def get_all_incidents(
    db: Session = Depends(get_db),
    __current_ceo: User = Depends(get_current_ceo_user)
):
    return db.query(Incident).all()

# 📤 Générer et télécharger un rapport (CEO)
@router.post("/report-ceo", response_class=StreamingResponse)
def download_ceo_report(
    date_range: DateRange,
    db: Session = Depends(get_db),
    __ceo: User = Depends(get_current_ceo_user)
):
    start_date = date_range.start_date
    end_date = date_range.end_date

    # end_date est inclusive : on prend tout jusqu'au lendemain 00:00
    incidents = db.query(Incident).filter(
        Incident.createdAt >= start_date,
        Incident.createdAt < end_date + timedelta(days=1)
    ).all()

    if not incidents:
        raise HTTPException(status_code=404, detail="Aucun incident trouvé sur cette période")

    data = [{
        "title": i.title,
        "priority": i.priority.value,
        "status": i.status.value,
        "category": i.category.value,
        "createdAt": i.createdAt,
        "user_name": i.user.name,
        "user_email": i.user.email,
    } for i in incidents]

    pdf_buffer = generate_ceo_report(data)

    filename = f"rapport_ceo_incidents_{start_date}_to_{end_date}.pdf"
    file_path = os.path.join(REPORTS_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(pdf_buffer.getbuffer())
    pdf_buffer.seek(0)

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

# 📂 Lister les rapports disponibles
@router.get("/list-reports")
def list_generated_reports(
    __ceo = Depends(get_current_ceo_user)
):
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".pdf")]
    return {"reports": files}

# ⬇️ Télécharger un rapport existant
@router.get("/download-report/{filename}", response_class=FileResponse)
def download_existing_report(
    filename: str,
    __ceo = Depends(get_current_ceo_user)
):
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Rapport introuvable")

    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)

