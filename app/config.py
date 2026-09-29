
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    postgres_url: str
    access_token_expire_minutes: int = 1440
    secret_key: str
    algorithm: str = "HS256"
    cors_origin:str="*"
    # Compte administrateur principal : identifiants fixés ici, le compte est créé
    # (ou son mot de passe mis à jour) à chaque démarrage de l'API
    admin_email: str = "support@groupegenetics.com"
    admin_password: str = ""
    admin_name: str = "Administrateur Genetics"
    # Autres adresses ayant le rôle administrateur, séparées par des virgules
    admin_emails: str = "diallo30amadoukorka@gmail.com,mohamed.thialaw@groupegenetics.com"

    @property
    def admin_email_list(self) -> list[str]:
        emails = [self.admin_email, *self.admin_emails.split(",")]
        return [e.strip().lower() for e in emails if e.strip()]

  

    @property
    def postgres_database_url(self) -> str:
        return self.postgres_url

def get_settings() -> Settings:
    return Settings()

settings = get_settings()


