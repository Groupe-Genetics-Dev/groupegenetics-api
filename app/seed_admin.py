"""Crée ou met à jour le compte administrateur défini dans le .env (ADMIN_EMAIL / ADMIN_PASSWORD)."""

import uuid

from rich.console import Console

from app.config import settings
from app.model import AccountStatus, User
from app.postgres_connect import SessionLocal
from app.utils import hashed, verify

console = Console()


def ensure_admin_account() -> None:
    email = settings.admin_email.strip().lower()
    if not email or not settings.admin_password:
        console.print("[yellow]ADMIN_EMAIL / ADMIN_PASSWORD non définis : compte administrateur non créé.[/]")
        return

    with SessionLocal() as db:
        admin = db.query(User).filter(User.email.ilike(email)).first()
        if admin is None:
            db.add(User(
                id=uuid.uuid4(),
                email=email,
                name=settings.admin_name,
                password=hashed(settings.admin_password),
                account_status=AccountStatus.APPROVED,
            ))
            console.print(f"[green]Compte administrateur créé : {email}[/]")
        else:
            if not verify(settings.admin_password, admin.password):
                admin.password = hashed(settings.admin_password)
                console.print(f"[green]Mot de passe administrateur mis à jour : {email}[/]")
            admin.account_status = AccountStatus.APPROVED
        db.commit()


if __name__ == "__main__":
    ensure_admin_account()
