from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CV Processing Backend"
    APP_VERSION: str = "1.0.0"

    # Authentication
    SECRET_KEY: str  # Required for API authentication

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/cv_processor"

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: str = "noreply@cvprocessor.com"
    EMAILS_FROM_NAME: str = "CV Processor"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file


settings = Settings()
