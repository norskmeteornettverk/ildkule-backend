from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, root_validator, validator


ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        ...,
        description=(
            "SQLAlchemy compatible database URL, "
            "e.g. mysql+pymysql://user:pass@host:3306/dbname "
            "or postgresql+psycopg://user:pass@host:5432/dbname"
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
    event_media_source_mode: str = Field(
        default="local",
        description="How event and media URLs are built: local or remote.",
    )
    event_media_base_url: Optional[str] = Field(
        default=None,
        description="Optional base URL used when building public event/media file links.",
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
    cors_allow_credentials: bool = Field(
        default=False,
        description="Whether CORS responses should allow credentials such as cookies.",
    )
    contact_recipient: Optional[str] = None
    meteor_report_recipient: Optional[str] = None
    app_log_level: str = Field(
        default="INFO",
        description="Application log level for FastAPI runtime logging.",
    )
    app_log_file: str = Field(
        default=str(Path(__file__).resolve().parents[1] / "logs" / "fastapi.log"),
        description="File path where FastAPI runtime logs are written.",
    )
    disable_file_logging: bool = Field(
        default=False,
        description="Disable file-based logging and only log to stdout/stderr.",
    )
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

    @validator("database_url", pre=True)
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        lowered = value.lower()
        if lowered.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://") :]
        if lowered.startswith("postgres://"):
            return "postgresql+psycopg://" + value[len("postgres://") :]
        return value

    @root_validator
    def validate_media_settings(cls, values):
        mode = (values.get("event_media_source_mode") or "local").strip().lower()
        values["event_media_source_mode"] = mode
        if mode not in {"local", "remote"}:
            raise ValueError("EVENT_MEDIA_SOURCE_MODE must be 'local' or 'remote'")
        if mode == "remote" and not values.get("event_media_base_url"):
            raise ValueError(
                "EVENT_MEDIA_BASE_URL is required when EVENT_MEDIA_SOURCE_MODE=remote"
            )
        return values

    class Config:
        env_file = str(ENV_FILE_PATH)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()
