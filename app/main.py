
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rich.console import Console

from app.routers import user, auth, incident, contact
from app.seed_admin import ensure_admin_account

console = Console()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    console.print(":banana: [cyan underline]Groupe Genetics Api is starting ...[/]")
    ensure_admin_account()
    yield
    console.print(":mango: [bold red underline]Groupe Genetics Api shutting down ...[/]")


app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ajout de la route racine
@app.get("/")
async def root():
    return {
        "message": "Bienvenue sur l'API Groupe Genetics pour la gestion de leurs supports",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs"
    }

# Inclusion des routeurs
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(incident.router)
app.include_router(contact.router)



