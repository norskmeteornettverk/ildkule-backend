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
        description="Root folder where event data files are stored",
    )
    station_log_token: Optional[str] = Field(
        default=None,
        description="Bearer token shared with event stations when pushing logs",
    )
    station_network_offline_minutes: int = Field(
        default=60,
        description="Minutes since last seen before a station or camera is treated as offline.",
    )
    station_snapshot_base_url: Optional[str] = Field(
        default=None,
        description="Optional base URL used when building live snapshot links for station cameras.",
    )
    eventload_username: Optional[str] = "sys_admin"
    eventload_password: Optional[str] = "secretpassword"

    cors_allow_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Origins FastAPI should allow in CORS responses",
    )
    contact_recipient: Optional[str] = None
    meteor_report_recipient: Optional[str] = None
    public_timezone: str = Field(
        default="Europe/Oslo",
        description="IANA timezone used for public local-time serialisation",
    )
    candidate_max_end_height_km: float = Field(
        default=25.0,
        description="Maximum end height used when flagging meteorite candidates",
    )
    candidate_max_speed_kms: float = Field(
        default=25.0,
        description="Maximum speed used when flagging meteorite candidates",
    )

    class Config:
        env_file = str(ENV_FILE_PATH)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
