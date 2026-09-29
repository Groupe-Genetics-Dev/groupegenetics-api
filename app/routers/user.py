import asyncio
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta
from uuid import UUID
from app.schemas.user import  ResetPasswordRequest, UserCreate, UserMe, UserOut, UserUpdate, UserBase
from app.model import  User
from app.postgres_connect import get_db
from app.oauth2 import  get_current_user, user_role
from app.utils import generate_otp, hashed
from app.utils import send_otp_email, send_new_account_admin_email, send_welcome_email


router = APIRouter(prefix="/users", tags=["Users"])
logger = logging.getLogger(__name__)
otp_store = {}

@router.post("/create-user", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user_exist = db.query(User).filter_by(email=user.email).first()
    if user_exist:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, 
                            detail=f"Un utilisateur avec l'email ({user_exist.email}) existe déjà")

    new_user = User(
        id=uuid.uuid4(),
        email=user.email,
        name=user.name,
        password=hashed(user.password),
        company=user.company,
        phone=user.phone,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # E-mails de bienvenue (client) et de notification (admin) : un échec d'envoi
    # ne doit pas empêcher la création du compte
    for send in (send_welcome_email, send_new_account_admin_email):
        try:
            asyncio.run(send(new_user))
        except Exception:
            logger.exception("Envoi de l'e-mail %s impossible pour %s", send.__name__, new_user.email)
    return new_user


@router.get("/me", response_model=UserMe)
async def get_current_user(current_user: User = Depends(get_current_user)):
    return UserMe(**UserOut.model_validate(current_user).model_dump(), role=user_role(current_user))


# Mise à jour complète du compte
@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, updates: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Utilisateur introuvable.")

    if updates.name:
        user.name = updates.name
    if updates.company:
        user.company = updates.company
    if updates.phone:
        user.phone = updates.phone
    if updates.password:
        user.password = hashed(updates.password)

    db.commit()
    db.refresh(user)
    return user


# Mise à jour des informations personnelles (partielle)

@router.patch("/{user_id}/profile", response_model=UserOut)
def update_profile(user_id: UUID, updates: UserBase, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Utilisateur introuvable.")

    if updates.name:
        user.name = updates.name
    if updates.company:
        user.company = updates.company
    if updates.phone:
        user.phone = updates.phone

    if updates.email:
        user.email = updates.email

    db.commit()
    db.refresh(user)
    return user


@router.post("/forgot-password/request-otp")
async def request_otp(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Aucun utilisateur avec cet email.")

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Enregistrement dans la base
    user.otp_code = otp
    user.otp_expires_at = expires_at
    db.commit()

    try:
        await send_otp_email(email, otp)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             detail=f"Erreur lors de l'envoi de l'email : {str(e)}")

    return {"message": "Code OTP envoyé par email."}


@router.post("/forgot-password/reset")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Les mots de passe ne correspondent pas.")

    user = db.query(User).filter_by(email=payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail="Utilisateur introuvable.")

    if not user.otp_code or user.otp_code != payload.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Code OTP invalide.")

    if user.otp_expires_at is None or user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Le code OTP a expiré.")

    # Mise à jour du mot de passe
    user.password = hashed(payload.new_password)
    user.otp_code = None
    user.otp_expires_at = None

    db.commit()

    return {"message": "Mot de passe mis à jour avec succès."}


@router.get("/all", response_model=list[UserOut])
async def get_all_users(db: Annotated[Session, Depends(get_db)]):
    users = db.query(User).all()
    return users

