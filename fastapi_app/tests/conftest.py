import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure project root is on PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configure environment variables before importing the app settings/DB modules
TEST_DB_PATH = ROOT_DIR / "fastapi_app" / "tests" / "test.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("SMTP_SENDER", "noreply@example.com")
os.environ.setdefault("CONTACT_RECIPIENT", "contact-test@example.com")
os.environ.setdefault("METEOR_REPORT_RECIPIENT", "meteor-test@example.com")

from fastapi_app.app.config import get_settings
from fastapi_app.app.db import Base, SessionLocal, engine, get_session
from fastapi_app.app.main import app


@pytest.fixture(scope="function")
def db_session() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    def override_session():
        try:
            yield db_session
            db_session.commit()
        finally:
            db_session.rollback()

    app.dependency_overrides[get_session] = override_session
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.fixture(scope="function")
def settings_override():
    return get_settings()
