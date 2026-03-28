from __future__ import annotations

import base64
from datetime import datetime

from fastapi_app.app.models import User
from fastapi_app.app.routers import admin as admin_router
from fastapi_app.app.routers import events as events_router
from fastapi_app.app.routers import users as users_router
from fastapi_app.app.security import create_access_token


def _auth_header(user: User) -> dict[str, str]:
    token = create_access_token(
        {
            "username": user.username,
            "user_id": user.id,
            "role": user.role,
            "user_level": user.user_level,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def _basic_header(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def _minimal_event(event_id: int = 1, title: str = "Test event") -> dict:
    return {
        "id": event_id,
        "location": "Oslo",
        "event_type": "Krysspeilet",
        "cross_station_confirmed": True,
        "event_path": "20240101/010203",
        "public_url": None,
        "event_artifacts": [],
        "preview": {
            "type": None,
            "thumbnail_url": None,
            "image_url": None,
            "has_preview": False,
        },
        "candidate": {
            "is_candidate": False,
            "max_end_height_km": 25.0,
            "max_speed_kms": 25.0,
        },
        "final_classification": "Meteor",
        "times": {"utc": "2024-01-01T01:02:03Z", "local": None, "timezone": "Europe/Oslo"},
        "title": title,
        "title_basis": {
            "event_type": "Krysspeilet",
            "location": "Oslo",
            "cross_station_confirmed": True,
        },
        "station_summary": {
            "station_count": 1,
            "observation_count": 1,
            "stations": ["ski"],
            "cameras": ["cam1"],
            "label": "1 stasjon, 1 kamera",
        },
        "station_count": 1,
        "observation_count": 1,
        "shower": None,
        "ai_score": None,
        "technical_validity": {
            "is_valid": True,
            "is_deleted": False,
            "source_bad_detection": None,
            "proper_triangulation": None,
        },
        "header": {
            "id": event_id,
            "event_path": "20240101/010203",
            "title": title,
            "location": "Oslo",
            "times": {"utc": "2024-01-01T01:02:03Z", "local": None, "timezone": "Europe/Oslo"},
            "cross_station_confirmed": True,
        },
        "summary_basis": {
            "location": "Oslo",
            "station_summary": {
                "station_count": 1,
                "observation_count": 1,
                "stations": ["ski"],
                "cameras": ["cam1"],
                "label": "1 stasjon, 1 kamera",
            },
            "shower": None,
            "candidate": {
                "is_candidate": False,
                "max_end_height_km": 25.0,
                "max_speed_kms": 25.0,
            },
        },
        "classification": {
            "final_classification": "Meteor",
            "cross_station_confirmed": True,
        },
        "analysis": None,
        "observations": None,
    }


def test_admin_event_import_auth_and_config_edges(client, monkeypatch):
    monkeypatch.setattr(admin_router.settings, "eventload_username", "loader")
    monkeypatch.setattr(admin_router.settings, "eventload_password", "secret")

    bad = client.post(
        "/api/admin/event-imports",
        headers=_basic_header("loader", "wrong"),
        json={"date_from": "20240101", "date_to": "20240101"},
    )
    assert bad.status_code == 401
    assert bad.json()["detail"] == "Feil brukernavn eller passord"

    monkeypatch.setattr(admin_router.settings, "data_directory", None)
    missing_dir = client.post(
        "/api/admin/event-imports",
        headers=_basic_header("loader", "secret"),
        json={"date_from": "20240101", "date_to": "20240101"},
    )
    assert missing_dir.status_code == 500
    assert missing_dir.json()["detail"] == "DATA_DIRECTORY is not configured"


def test_users_create_and_self_service_edges(client, db_session, monkeypatch):
    monkeypatch.setattr(users_router.user_service, "create_user", lambda session, username, password: User(
        id=55,
        username=username,
        password=password,
        role="ROLE_USER",
        user_level="1",
        confirmed=False,
        tutorial_completed=False,
        create_time=datetime.utcnow(),
    ))
    created = client.post(
        "/api/users",
        json={"identifier": "created@example.com", "password": "password-123"},
    )
    assert created.status_code == 201
    assert created.json()["identifier"] == "created@example.com"

    owner = User(
        username="owner@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
        tutorial_completed=False,
    )
    other = User(
        username="other@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
        tutorial_completed=False,
    )
    db_session.add_all([owner, other])
    db_session.commit()

    missing = client.get("/api/users/9999", headers=_auth_header(owner))
    assert missing.status_code == 403
    assert missing.json()["detail"] == "Not authorized"

    denied_tutorial = client.put(
        f"/api/users/{other.id}/tutorial-completion",
        headers=_auth_header(owner),
        json={"completed": True},
    )
    assert denied_tutorial.status_code == 403
    assert denied_tutorial.json()["detail"] == "Not authorized"

    denied_password = client.patch(
        f"/api/users/{other.id}/password",
        headers=_auth_header(owner),
        json={"current_password": "pw", "new_password": "new-password-456"},
    )
    assert denied_password.status_code == 403
    assert denied_password.json()["detail"] == "Not authorized"


def test_events_list_search_filter_and_explore_bool_parsing(client, monkeypatch):
    monkeypatch.setattr(
        events_router.event_service,
        "search",
        lambda session, term, include_deleted=False: {
            "totalItems": 1,
            "events": [_minimal_event(1, f"search:{term}")],
            "totalPages": 1,
            "currentPage": 1,
        },
    )
    monkeypatch.setattr(
        events_router.event_service,
        "filter",
        lambda session, stations, years, classes, include_deleted=False: {
            "totalItems": 1,
            "events": [_minimal_event(2, "filter")],
            "totalPages": 1,
            "currentPage": 1,
        },
    )
    monkeypatch.setattr(
        events_router.event_service,
        "list_events",
        lambda session, page, limit, orderby=None, order=None, include_deleted=False, **kwargs: {
            "totalItems": 1,
            "events": [_minimal_event(3, "list")],
            "totalPages": 1,
            "currentPage": page,
        },
    )
    monkeypatch.setattr(
        events_router.event_service,
        "explore",
        lambda session, **kwargs: {
            "filters": {
                "from_date": kwargs.get("from_date"),
                "to_date": kwargs.get("to_date"),
                "stations": kwargs.get("stations") or [],
                "cross_station_confirmed": kwargs.get("cross_station_confirmed"),
                "candidate": kwargs.get("candidate_only", False),
            },
            "candidate_settings": {"max_end_height_km": 25.0, "max_speed_kms": 25.0},
            "kpi": {
                "total_events": 1,
                "cross_station_confirmed": 1,
                "candidates": 0,
                "stations": ["ski"],
            },
            "events": [],
        },
    )

    searched = client.get("/api/events", params={"searchTerm": "fireball", "includeDeleted": True})
    assert searched.status_code == 200
    assert searched.json()["events"][0]["title"] == "search:fireball"

    filtered = client.get(
        "/api/events",
        params={"stationName": "ski,sorreisa", "year": "2023,2024", "eventType": "Krysspeilet,Upeilet"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["events"][0]["title"] == "filter"

    listed = client.get("/api/events", params={"page": 3, "limit": 7})
    assert listed.status_code == 200
    assert listed.json()["currentPage"] == 3

    explore_true = client.get("/api/explore", params={"cross_station_confirmed": "yes"})
    assert explore_true.status_code == 200
    assert explore_true.json()["filters"]["cross_station_confirmed"] is True

    explore_false = client.get("/api/explore", params={"cross_station_confirmed": "0"})
    assert explore_false.status_code == 200
    assert explore_false.json()["filters"]["cross_station_confirmed"] is False

    invalid = client.get("/api/explore", params={"cross_station_confirmed": "maybe"})
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Invalid boolean value: maybe"


def test_event_review_messages_and_alias_routes(client, db_session, monkeypatch):
    user = User(
        username="reviewer@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    admin = User(
        username="admin@example.com",
        password="pw",
        role="ROLE_ADMIN",
        user_level="10",
        confirmed=True,
    )
    db_session.add_all([user, admin])
    db_session.commit()

    calls = []
    monkeypatch.setattr(
        events_router.event_service,
        "review_event",
        lambda session, event_id, user_id, rating: calls.append((event_id, user_id, rating)),
    )
    monkeypatch.setattr(
        events_router.event_service,
        "update_user_confirmation",
        lambda session, event_id, value: calls.append(("classify", event_id, value)),
    )
    monkeypatch.setattr(
        events_router.event_service,
        "get_insight",
        lambda session, report_name: (
            [
                {
                    "Stasjonsnavn": "Ski",
                    "Kameranavn": "cam1",
                    "ForsteObservasjonsTidspunkt": "2024-01-01T01:02:03",
                    "SisteObervasjonsTidspunkt": "2024-01-01T01:02:03",
                    "DagerMedObservasjoner": 1,
                    "DagerSidenSisteObservasjon": 1,
                    "Kameraopptak": 1,
                    "Hendelser": 1,
                    "Krysspeilede": 1,
                    "Meteorittkandidater": 1,
                }
            ]
            if report_name == "cam"
            else [
                {
                    "Stasjonsnavn": "Ski",
                    "ForsteObservasjonsTidspunkt": "2024-01-01T01:02:03",
                    "SisteObervasjonsTidspunkt": "2024-01-01T01:02:03",
                    "DagerMedObservasjoner": 1,
                    "DagerSidenSisteObservasjon": 1,
                    "Kameraopptak": 1,
                    "Hendelser": 1,
                    "Krysspeilede": 1,
                    "Meteorittkandidater": 1,
                }
            ]
            if report_name == "station"
            else [
                {
                    "ForsteObservasjonsTidspunkt": "2024-01-01T01:02:03",
                    "SisteObervasjonsTidspunkt": "2024-01-01T01:02:03",
                    "DagerMedObservasjoner": 1,
                    "DagerSidenSisteObservasjon": 1,
                    "Kameraopptak": 1,
                    "Hendelser": 1,
                    "Krysspeilede": 1,
                    "Meteorittkandidater": 1,
                }
            ]
            if report_name == "total"
            else [
                {
                    "id": 10,
                    "datetimetag": "20240101010203",
                    "station_cam": "cam1@ski",
                    "number_of_stations": 1,
                    "lat": 59.9,
                    "lng": 10.7,
                    "slat": 60.1,
                    "slng": 10.8,
                    "radiant_ra": None,
                    "radiant_dec": None,
                    "radiant_ecl_lat": None,
                    "radiant_ecl_long": None,
                    "track_speed": None,
                    "track_endheight": None,
                    "radiant_shower": None,
                    "date": None,
                    "triangulation": False,
                    "proper_triangulation": None,
                    "ai_score": None,
                }
            ]
            if report_name == "coordinates"
            else [{"report": report_name}]
        ),
    )
    monkeypatch.setattr(
        events_router.event_service,
        "get_coordinate_insight",
        lambda session, **kwargs: [
            {
                "id": 10,
                "datetimetag": "20240101010203",
                "station_cam": "cam1@ski",
                "number_of_stations": 1,
                "lat": 59.9,
                "lng": 10.7,
                "slat": 60.1,
                "slng": 10.8,
                "radiant_ra": None,
                "radiant_dec": None,
                "radiant_ecl_lat": None,
                "radiant_ecl_long": None,
                "track_speed": None,
                "track_endheight": None,
                "radiant_shower": None,
                "date": None,
                "triangulation": False,
                "proper_triangulation": None,
                "ai_score": None,
            }
        ],
    )
    monkeypatch.setattr(
        events_router.event_service,
        "get_event_by_datetimetag",
        lambda session, date_tag, time_tag, include_deleted=False: _minimal_event(4, f"{date_tag}/{time_tag}"),
    )

    mismatch = client.post(
        "/api/events/10/review",
        headers=_auth_header(user),
        json={"confirmed": "Positive", "userID": user.id + 1},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["detail"] == "userID does not match token user"

    negative = client.post(
        "/api/events/10/review",
        headers=_auth_header(user),
        json={"confirmed": "Negative"},
    )
    assert negative.status_code == 200
    assert negative.json()["msg"] == "Takk for din anbefaling (Nei)"

    reset = client.post(
        "/api/events/10/review",
        headers=_auth_header(user),
        json={"confirmed": "Unsure"},
    )
    assert reset.status_code == 200
    assert reset.json()["msg"] == "Anbefalingen er nullstilt"

    classified = client.put(
        "/api/events/10/classification",
        headers=_auth_header(admin),
        json={"user_confirmed": "Positive"},
    )
    assert classified.status_code == 200
    assert classified.json()["msg"] == "Success!"

    insight = client.get("/api/insights/cam")
    assert insight.status_code == 200
    assert insight.json()[0]["Kameranavn"] == "cam1"

    station_insight = client.get("/api/insights/station")
    assert station_insight.status_code == 200
    assert station_insight.json()[0]["Stasjonsnavn"] == "Ski"

    total_insight = client.get("/api/insights/total")
    assert total_insight.status_code == 200
    assert total_insight.json()[0]["Hendelser"] == 1

    coordinates = client.get("/api/insights/coordinates")
    assert coordinates.status_code == 200
    assert coordinates.json()[0]["datetimetag"] == "20240101010203"

    by_path = client.get("/api/events/by-path/20240101/010203", params={"includeDeleted": True})
    assert by_path.status_code == 200
    assert by_path.json()["title"] == "20240101/010203"


def test_admin_eventboard_uses_admin_response_shape(client, db_session, monkeypatch):
    monkeypatch.setattr(
        events_router.event_service,
        "list_events",
        lambda session, page, limit, order_by, order, include_deleted=False, include_ratings=False: {
            "totalItems": 1,
            "events": [
                {
                    **_minimal_event(9, "admin"),
                    "datetimetag": "20240203040506",
                    "date": "2024-02-03T04:05:06",
                    "camera_confirmed": 1,
                    "user_confirmed": 1,
                    "ratings": 5,
                    "positive_ratings": 3,
                    "negative_ratings": 2,
                }
            ],
            "totalPages": 1,
            "currentPage": page,
        },
    )
    admin = User(
        username="board@example.com",
        password="pw",
        role="ROLE_ADMIN",
        user_level="10",
        confirmed=True,
    )
    db_session.add(admin)
    db_session.commit()

    response = client.get("/api/admin/events", headers=_auth_header(admin))
    assert response.status_code == 200
    payload = response.json()
    assert payload["events"][0]["datetimetag"] == "20240203040506"
    assert payload["events"][0]["date"] == "2024-02-03T04:05:06"
    assert payload["events"][0]["camera_confirmed"] == 1
    assert payload["events"][0]["user_confirmed"] == 1
    assert payload["events"][0]["ratings"] == 5
    assert payload["events"][0]["positive_ratings"] == 3
    assert payload["events"][0]["negative_ratings"] == 2


def test_explore_export_rejects_unsupported_format(client):
    response = client.get("/api/explore/export", params={"format": "json"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Only csv export is supported"
