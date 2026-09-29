
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    postgres_url: str
    access_token_expire_minutes: int = 1440
    secret_key: str
    algorithm: str = "HS256"
    cors_origin:str="*"
    # Comptes administrateurs (accès au tableau de bord), séparés par des virgules
    admin_emails: str = "diallo30amadoukorka@gmail.com,support@groupegenetics.com,mohamed.thialaw@groupegenetics.com"

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

  

    @property
    def postgres_database_url(self) -> str:
        return self.postgres_url

def get_settings() -> Settings:
    return Settings()

settings = get_settings()


