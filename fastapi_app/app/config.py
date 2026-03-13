from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field


ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        ...,
        description=(
            "SQLAlchemy compatible database URL, "
            "e.g. mysql+pymysql://user:pass@host:3306/dbname"
        ),
    )
    jwt_secret_key: str = Field(..., description="Secret key used to sign JWT tokens")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 600

    recaptcha_secret: Optional[str] = Field(
        default=None,
        description="Google reCAPTCHA secret used for public forms",
    )
    front_url: Optional[str] = Field(
        default=None,
        description="Public frontend URL used when creating password reset links",
    )

    smtp_host: Optional[str] = None
    smtp_port: int = 465
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_sender: Optional[str] = None
    smtp_debug: bool = False

    data_directory: Optional[str] = Field(
        default=None,
        description="Root folder where meteor data files are stored",
    )
    station_log_token: Optional[str] = Field(
        default=None,
        description="Bearer token shared with meteor stations when pushing logs",
    )
    meteorload_username: Optional[str] = "sys_admin"
    meteorload_password: Optional[str] = "secretpassword"

    cors_allow_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Origins FastAPI should allow in CORS responses",
    )
    contact_recipient: Optional[str] = None
    meteor_report_recipient: Optional[str] = None

    class Config:
        env_file = str(ENV_FILE_PATH)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
