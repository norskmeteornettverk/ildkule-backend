import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from fastapi_app.app import main as main_module
from fastapi_app.app.config import Settings
from fastapi_app.app.utils import logging_utils

ROOT_DIR = Path(__file__).resolve().parents[2]
WORK_TMP_DIR = ROOT_DIR / ".tmp" / "runtime_config_tests"


def _has_data_mount(app) -> bool:
    return any(getattr(route, "path", None) == "/data" for route in app.routes)


def test_remote_media_mode_requires_base_url():
    with pytest.raises(ValidationError, match="EVENT_MEDIA_BASE_URL"):
        Settings(
            database_url="sqlite:///tmp.db",
            jwt_secret_key="secret",
            event_media_source_mode="remote",
        )


@pytest.mark.parametrize(
    ("raw_url", "expected_url"),
    [
        (
            "postgresql://user:pass@host:5432/dbname?sslmode=require",
            "postgresql+psycopg://user:pass@host:5432/dbname?sslmode=require",
        ),
        (
            "postgres://user:pass@host:5432/dbname",
            "postgresql+psycopg://user:pass@host:5432/dbname",
        ),
    ],
)
def test_database_url_is_normalized_for_neon_postgres(raw_url, expected_url):
    settings = Settings(database_url=raw_url, jwt_secret_key="secret")

    assert settings.database_url == expected_url


def test_create_app_skips_data_mount_in_remote_media_mode(monkeypatch):
    WORK_TMP_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main_module, "check_database_connection", lambda: None)
    monkeypatch.setattr(main_module.settings, "event_media_source_mode", "remote")
    monkeypatch.setattr(main_module.settings, "event_media_base_url", "https://example.com/meteor")
    monkeypatch.setattr(main_module.settings, "data_directory", str(WORK_TMP_DIR))

    app = main_module.create_app()

    assert not _has_data_mount(app)


def test_create_app_mounts_data_directory_in_local_media_mode(monkeypatch):
    WORK_TMP_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main_module, "check_database_connection", lambda: None)
    monkeypatch.setattr(main_module.settings, "event_media_source_mode", "local")
    monkeypatch.setattr(main_module.settings, "data_directory", str(WORK_TMP_DIR))

    app = main_module.create_app()

    assert _has_data_mount(app)


def test_configure_logging_can_disable_file_logging(monkeypatch):
    WORK_TMP_DIR.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_configured = logging_utils._CONFIGURED

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    monkeypatch.delenv("VERCEL", raising=False)
    logging_utils._CONFIGURED = False

    try:
        logger = logging_utils.configure_logging(
            log_level="INFO",
            log_file=str(WORK_TMP_DIR / "fastapi.log"),
            disable_file_logging=True,
        )
        assert logger.name == "ildkule.fastapi"
        assert not any(
            isinstance(handler, logging.FileHandler) for handler in root_logger.handlers
        )
    finally:
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
            handler.close()
        for handler in original_handlers:
            root_logger.addHandler(handler)
        logging_utils._CONFIGURED = original_configured
