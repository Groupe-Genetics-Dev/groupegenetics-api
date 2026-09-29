import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship, DeclarativeBase
)


class Base(DeclarativeBase):
    pass

class Priority(PyEnum):
    FAIBLE = "FAIBLE"
    MOYENNE = "MOYENNE"
    HAUTE = "HAUTE"
    CRITIQUE = "CRITIQUE"

class Category(PyEnum):
    RESEAU = "RESEAU"
    SECURITE = "SECURITE"
    LOGICIEL = "LOGICIEL"
    MATERIEL = "MATERIEL"
    ACCES = "ACCES"
    SURVEILLANCE = "SURVEILLANCE"
    AUTRE = "AUTRE"

class IncidentStatus(PyEnum):
    EN_ATTENTE = "EN_ATTENTE"
    EN_TRAITEMENT = "EN_TRAITEMENT"
    TERMINE = "TERMINE"

class AccountStatus(PyEnum):
    PENDING = "PENDING"      # en attente de validation par un administrateur
    APPROVED = "APPROVED"    # validé : peut se connecter
    REJECTED = "REJECTED"    # refusé

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    otp_code: Mapped[Optional[str]] = mapped_column(String(length=6), nullable=True)
    otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), nullable=False, default=AccountStatus.PENDING, server_default=AccountStatus.PENDING.value
    )
    reviewedAt: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)



    incidents: Mapped[List["Incident"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), nullable=False)
    category: Mapped[Category] = mapped_column(Enum(Category), nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.EN_ATTENTE)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    userId: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped[User] = relationship(back_populates="incidents")


