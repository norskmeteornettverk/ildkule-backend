import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import mysql

from fastapi_app.app import main as main_module
from fastapi_app.app.models import Event
from fastapi_app.app.services.event_service import EventService
from fastapi_app.app.utils.sql_ordering import desc_nulls_last


def test_app_fails_startup_when_database_check_fails(monkeypatch):
    def fail_database_check():
        raise RuntimeError("db down")

    monkeypatch.setattr(main_module, "check_database_connection", fail_database_check)

    with pytest.raises(RuntimeError, match="Database startup check failed"):
        with TestClient(main_module.create_app()):
            pass


def test_unhandled_exception_returns_request_id_and_logs(monkeypatch, caplog):
    monkeypatch.setattr(main_module, "check_database_connection", lambda: None)
    app = main_module.create_app()

    @app.get("/boom")
    def boom():
        raise ValueError("boom")

    with caplog.at_level(logging.ERROR):
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/boom")

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Internal Server Error"
    assert payload["request_id"]
    assert response.headers["X-Request-ID"] == payload["request_id"]
    assert "Unhandled application exception" in caplog.text


def test_coordinate_query_compiles_without_nulls_last_for_mysql():
    stmt = (
        EventService()
        ._filtered_events_stmt(require_coordinates=True)
        .order_by(*desc_nulls_last(Event.date), Event.id.desc())
    )
    compiled = str(
        stmt.compile(
            dialect=mysql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "NULLS LAST" not in compiled.upper()
    assert "CASE WHEN" in compiled.upper()
