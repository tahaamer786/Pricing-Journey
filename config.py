from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus


class Settings(BaseSettings):
    # Database
    db_host: str
    db_port: int = 3306
    db_user: str
    db_password: str
    db_name: str

    # Google OAuth (user login)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8002/api/v1/auth/google/callback"

    # Vertex AI (Gemini)
    google_application_credentials: str = "./service_account.json"
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    gemini_model: str = "gemini-2.5-flash"

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    jubala_team_email: str = "team@jubala.ai"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Admin (for Jubala team dashboard login)
    admin_username: str = "admin"
    admin_password: str = "changeme123"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8002
    frontend_url: str = "http://localhost:3000"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
