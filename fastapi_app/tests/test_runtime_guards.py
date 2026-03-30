import logging

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.dialects import mysql, postgresql

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


@pytest.mark.parametrize(
    ("dialect", "expected_station_name_expr", "expected_days_since_expr"),
    [
        (
            "sqlite",
            "upper(substr(s.station_name, 1, 1)) || substr(s.station_name, 2)",
            "CAST(julianday('now') - julianday(max(m.date)) AS INTEGER)",
        ),
        (
            "mysql",
            "CONCAT(UPPER(LEFT(s.station_name, 1)), SUBSTRING(s.station_name, 2))",
            "DATEDIFF(CURRENT_DATE, DATE(max(m.date)))",
        ),
        (
            "postgresql",
            "upper(left(s.station_name, 1)) || substring(s.station_name from 2)",
            "(CURRENT_DATE - CAST(max(m.date) AS DATE))",
        ),
    ],
)
def test_insight_sql_parts_are_dialect_safe(
    dialect, expected_station_name_expr, expected_days_since_expr
):
    parts = EventService()._insight_sql_parts(dialect)

    assert parts["station_name_expr"] == expected_station_name_expr
    assert parts["days_since_expr"] == expected_days_since_expr


def test_insight_sql_parts_supports_mariadb_alias():
    mysql_parts = EventService()._insight_sql_parts("mysql")
    mariadb_parts = EventService()._insight_sql_parts("mariadb")

    assert mariadb_parts == mysql_parts


def test_insight_sql_parts_rejects_unsupported_dialect():
    with pytest.raises(HTTPException) as exc_info:
        EventService()._insight_sql_parts("oracle")

    assert exc_info.value.status_code == 500
    assert "Unsupported database dialect" in exc_info.value.detail


def test_coordinate_query_compiles_for_postgresql():
    stmt = (
        EventService()
        ._filtered_events_stmt(require_coordinates=True)
        .order_by(*desc_nulls_last(Event.date), Event.id.desc())
    )
    compiled = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "CASE WHEN" in compiled.upper()
    assert "ORDER BY" in compiled.upper()


def test_postgresql_insight_sql_uses_postgresql_safe_functions():
    parts = EventService()._insight_sql_parts("postgresql")
    sql = f"""
    select {parts["station_name_expr"]} as Stasjonsnavn,
    {parts["days_since_expr"]} as DagerSidenSisteObservasjon
    from station as s
    left outer join cam as c on s.id = c.station_id
    left outer join observation_cam_data as d on c.id = d.cam_id
    left outer join event as m on d.event_id = m.id
    group by {parts["station_name_expr"]}
    order by {parts["station_name_expr"]}
    """

    assert "substring(s.station_name from 2)" in sql
    assert "CURRENT_DATE - CAST(max(m.date) AS DATE)" in sql
    assert "DATEDIFF" not in sql
    assert "julianday" not in sql


def test_list_events_ratings_sort_coalesces_nulls_for_postgresql():
    service = EventService()
    ratings_subquery = service._ratings_subquery()
    stmt = (
        select(Event)
        .outerjoin(ratings_subquery, Event.id == ratings_subquery.c.event_id)
        .order_by(*service._ordering_clauses(func.coalesce(ratings_subquery.c.ratings, 0), "desc"))
    )
    compiled = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "COALESCE" in compiled.upper()
    assert "CASE WHEN" in compiled.upper()


def test_search_desc_order_uses_null_safe_date_sort_for_postgresql():
    stmt = (
        select(Event)
        .where(Event.location.ilike("%abc%"))
        .order_by(*EventService()._ordering_clauses(Event.date, "desc"))
    )
    compiled = str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "CASE WHEN" in compiled.upper()
    assert "EVENT.DATE DESC" in compiled.upper()


def test_normalize_insight_row_restores_expected_postgresql_alias_casing():
    service = EventService()
    lowered_row = {
        "forsteobservasjonstidspunkt": "2026-03-30T00:00:00",
        "sisteobervasjonstidspunkt": "2026-03-30T01:00:00",
        "dagermedobservasjoner": 1,
        "dagersidensisteobservasjon": 0,
        "kameraopptak": 2,
        "hendelser": 3,
        "krysspeilede": 1,
        "meteorittkandidater": 1,
    }

    normalized = service._normalize_insight_row("total", lowered_row)

    assert normalized["ForsteObservasjonsTidspunkt"] == "2026-03-30T00:00:00"
    assert normalized["SisteObervasjonsTidspunkt"] == "2026-03-30T01:00:00"
    assert normalized["DagerMedObservasjoner"] == 1
    assert normalized["DagerSidenSisteObservasjon"] == 0
    assert normalized["Kameraopptak"] == 2
    assert normalized["Hendelser"] == 3
    assert normalized["Krysspeilede"] == 1
    assert normalized["Meteorittkandidater"] == 1
