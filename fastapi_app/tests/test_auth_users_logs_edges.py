from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import HTTPException

from fastapi_app.app.db import SessionLocal, get_session, session_scope
from fastapi_app.app.models import (
    Cam,
    Event,
    LogStation,
    ObservationCamData,
    Station,
    User,
    UserReview,
)
from fastapi_app.app.routers import logs as logs_router
from fastapi_app.app.routers import users as users_router
from fastapi_app.app.routers import auth as auth_router
from fastapi_app.app.security import (
    create_access_token,
    decode_token,
    enforce_role,
)
from fastapi_app.app.services import user_service as user_service_module
from fastapi_app.app.services.user_service import UserService


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


def test_login_rejects_wrong_password(client, db_session, monkeypatch):
    monkeypatch.setattr(user_service_module, "verify_password", lambda plain, stored: plain == stored)
    user = User(
        username="login@example.com",
        password="correct-password",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={"identifier": "login@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Feil brukernavn eller passord"


def test_password_reset_confirm_rejects_unknown_token(client, db_session):
    user = User(
        username="reset-confirm@example.com",
        password="initial-password",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/auth/password-reset/confirm",
        json={
            "email": user.username,
            "passwordResetId": "wrong-token",
            "password": "updated-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Kunne ikke oppdatere passordet"


def test_password_reset_request_and_confirm_success(client, monkeypatch):
    recorded = {}

    monkeypatch.setattr(auth_router.user_service, "request_password_reset", lambda session, email: recorded.setdefault("request_email", email))
    monkeypatch.setattr(auth_router.user_service, "reset_password", lambda session, email, token, password: (recorded.update({"reset_email": email, "token": token, "password": password}) or True))

    requested = client.post("/api/auth/password-reset/request", json={"email": "reset@example.com"})
    assert requested.status_code == 200
    assert requested.json()["message"] == "Passordreset sendt dersom brukeren finnes"
    assert recorded["request_email"] == "reset@example.com"

    confirmed = client.post(
        "/api/auth/password-reset/confirm",
        json={
            "email": "reset@example.com",
            "passwordResetId": "token-123",
            "password": "updated-password",
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["message"] == "Passordet ble endret"
    assert recorded["reset_email"] == "reset@example.com"


def test_verification_confirm_and_resend(client, db_session, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        user_service_module,
        "send_mail",
        lambda recipient, subject, html_body, alt_body=None, attachments=None: sent.update(
            {"recipient": recipient, "subject": subject, "body": html_body}
        ),
    )
    user = User(
        username="verify@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=False,
        confirm_token="token-123",
    )
    db_session.add(user)
    db_session.commit()

    resend = client.post(
        "/api/auth/verification/resend",
        json={"email": "verify@example.com"},
    )
    assert resend.status_code == 200
    assert "Ny verifiseringslenke" in resend.json()["message"]
    assert sent["recipient"] == "verify@example.com"

    refreshed = db_session.get(User, user.id)
    assert refreshed.confirm_token is not None

    confirm = client.get(
        "/api/auth/verification/confirm",
        params={"token": refreshed.confirm_token},
    )
    assert confirm.status_code == 200
    assert confirm.json()["account_confirmed"] is True

    db_session.refresh(refreshed)
    assert refreshed.confirmed is True
    assert refreshed.confirm_token is None

    invalid = client.get("/api/auth/verification/confirm", params={"token": "wrong"})
    assert invalid.status_code == 401


def test_user_route_requires_auth_and_rejects_invalid_or_stale_token(client):
    no_header = client.get("/api/users/1")
    assert no_header.status_code == 401
    assert no_header.json()["detail"] == "Authorization missing"

    invalid = client.get("/api/users/1", headers={"Authorization": "Bearer not-a-jwt"})
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid authentication credentials"

    stale_token = create_access_token(
        {
            "username": "missing@example.com",
            "user_id": 9999,
            "role": "ROLE_USER",
            "user_level": "1",
        }
    )
    stale = client.get("/api/users/1", headers={"Authorization": f"Bearer {stale_token}"})
    assert stale.status_code == 401
    assert stale.json()["detail"] == "User no longer exists"


def test_admin_eventboard_rejects_non_admin_user(client, db_session):
    user = User(
        username="plain-user@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.get("/api/admin/events", headers=_auth_header(user))

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient role privileges"


def test_patch_user_updates_admin_fields(client, db_session):
    admin = User(
        username="admin-patch@example.com",
        password="pw",
        role="ROLE_ADMIN",
        user_level="10",
        confirmed=True,
    )
    target = User(
        username="target@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        tutorial_completed=False,
        confirmed=False,
    )
    db_session.add_all([admin, target])
    db_session.commit()

    response = client.patch(
        f"/api/users/{target.id}",
        headers=_auth_header(admin),
        json={
            "role": "ROLE_MODERATOR",
            "user_level": "3",
            "account_confirmed": True,
            "tutorial_completed": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "ROLE_MODERATOR"
    assert payload["user_level"] == "3"
    assert payload["account_confirmed"] is True
    assert payload["tutorial_completed"] is True


def test_user_review_history_and_tutorial_metadata(client, db_session):
    owner = User(
        username="history@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    event = Event(
        datetimetag="20240102030405",
        location="Oslo",
        date=datetime(2024, 1, 2, 3, 4, 5),
        user_confirmed=1,
    )
    db_session.add_all([owner, event])
    db_session.commit()
    db_session.add(UserReview(user_id=owner.id, event_id=event.id, confirmed=1))
    db_session.commit()

    reviews = client.get(
        f"/api/users/{owner.id}/reviews",
        headers=_auth_header(owner),
    )
    assert reviews.status_code == 200
    assert reviews.json()["reviews"][0]["event_path"] == "20240102/030405"
    assert reviews.json()["reviews"][0]["review_label"] == "Ja"

    tutorial = client.get("/api/tutorial", headers=_auth_header(owner))
    assert tutorial.status_code == 200
    payload = tutorial.json()
    assert payload["version"] == "frontend-modal-2026-03"
    assert payload["content_owner"] == "frontend"
    assert payload["delivery_surface"] == "frontend_i18n"
    assert payload["status_field"] == "tutorial_completed"
    assert payload["completion_route"] == "/api/users/{user_id}/tutorial-completion"
    assert payload["minimum_level_after_completion"] == 1


def test_user_review_history_rejects_other_non_admin(client, db_session):
    owner = User(
        username="history-owner@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    other = User(
        username="history-other@example.com",
        password="pw",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    db_session.add_all([owner, other])
    db_session.commit()

    response = client.get(
        f"/api/users/{owner.id}/reviews",
        headers=_auth_header(other),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"


def test_change_password_rejects_wrong_current_password(client, db_session):
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(users_router, "verify_password", lambda plain, stored: plain == stored)
    user = User(
        username="change-password@example.com",
        password="correct-current",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.patch(
        f"/api/users/{user.id}/password",
        headers=_auth_header(user),
        json={
            "current_password": "wrong-current",
            "new_password": "new-password-123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"
    monkeypatch.undo()


def test_change_password_success(client, db_session, monkeypatch):
    monkeypatch.setattr(users_router, "verify_password", lambda plain, stored: plain == stored)
    captured = {}
    monkeypatch.setattr(
        users_router.user_service,
        "update_password",
        lambda session, user, new_password: captured.update({"user_id": user.id, "password": new_password}),
    )
    user = User(
        username="change-password-ok@example.com",
        password="correct-current",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.patch(
        f"/api/users/{user.id}/password",
        headers=_auth_header(user),
        json={
            "current_password": "correct-current",
            "new_password": "new-password-123",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Passord oppdatert"
    assert captured == {"user_id": user.id, "password": "new-password-123"}


def test_station_logs_list_and_post_auth_cases(client, db_session, monkeypatch):
    db_session.add(
        LogStation(
            station_name="sorreisa",
            code="OK",
            log_time=datetime(2024, 1, 1, 1, 2, 3),
        )
    )
    db_session.commit()

    listed = client.get("/api/station-logs")
    assert listed.status_code == 200
    assert listed.json()[0]["station_name"] == "sorreisa"

    payload = {
        "station": {
            "name": "ski",
            "code": "GOOD",
            "log_time": "2024-01-01T01:02:03",
        }
    }

    monkeypatch.setattr(logs_router.settings, "station_log_token", None)
    missing_config = client.post("/api/station-logs", json=payload)
    assert missing_config.status_code == 500
    assert missing_config.json()["detail"] == "Station log token not configured"

    monkeypatch.setattr(logs_router.settings, "station_log_token", "shared-token")
    missing_header = client.post("/api/station-logs", json=payload)
    assert missing_header.status_code == 401
    assert missing_header.json()["detail"] == "Authorization failed"

    bad_format = client.post(
        "/api/station-logs",
        json=payload,
        headers={"Authorization": "Token shared-token"},
    )
    assert bad_format.status_code == 401

    bad_token = client.post(
        "/api/station-logs",
        json=payload,
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert bad_token.status_code == 401

    ok = client.post(
        "/api/station-logs",
        json=payload,
        headers={"Authorization": "Bearer shared-token"},
    )
    assert ok.status_code == 200
    assert ok.json()["msg"] == "Success!"
    assert isinstance(ok.json()["id"], int)


def test_station_network_returns_aggregated_status(client, db_session, monkeypatch):
    station = Station(station_name="sorreisa")
    cam = Cam(station=station, cam_name="cam1")
    event = Event(
        datetimetag="20240102030405",
        date=datetime.utcnow(),
    )
    observation = ObservationCamData(
        event=event,
        cam=cam,
        observation_key="sorreisa:cam1:2024-01-02T03:04:05.000",
        source_hash="hash",
        event_start_utc=datetime.utcnow(),
    )
    db_session.add_all([station, cam, event, observation])
    db_session.add(
        LogStation(
            station_name="sorreisa",
            code="OK",
            log_time=datetime.utcnow(),
        )
    )
    db_session.commit()
    monkeypatch.setattr(logs_router.settings, "station_network_offline_minutes", 60)
    monkeypatch.setattr(logs_router.settings, "station_snapshot_base_url", "https://example.com/cam")

    response = client.get("/api/station-network")
    assert response.status_code == 200
    payload = response.json()
    assert payload["offline_after_minutes"] == 60
    assert payload["stations"][0]["station_name"] == "sorreisa"
    assert payload["stations"][0]["cameras"][0]["cam_name"] == "cam1"
    assert payload["stations"][0]["cameras"][0]["connected"] is True
    assert payload["stations"][0]["cameras"][0]["snapshot_url"].endswith("/sorreisa/cam1/snapshot.jpg")


def test_user_service_direct_edge_cases(db_session, monkeypatch):
    service = UserService()
    monkeypatch.setattr(user_service_module, "get_password_hash", lambda password: f"hashed::{password}")
    monkeypatch.setattr(user_service_module, "send_mail", lambda *args, **kwargs: None)

    created = service.create_user(db_session, "fresh@example.com", "new-password")
    assert created.username == "fresh@example.com"

    with pytest.raises(HTTPException) as duplicate:
        service.create_user(db_session, "fresh@example.com", "other-password")
    assert duplicate.value.status_code == 400

    assert service.request_password_reset(db_session, "unknown@example.com") is False

    monkeypatch.setattr(user_service_module, "send_mail", lambda *args, **kwargs: None)
    assert service.request_password_reset(db_session, "fresh@example.com") is True
    db_session.flush()
    assert service.reset_password(db_session, "fresh@example.com", "wrong-token", "pw") is False

    with pytest.raises(HTTPException) as missing_user:
        service.patch_user(db_session, {"id": 99999, "role": "ROLE_ADMIN"})
    assert missing_user.value.status_code == 404


def test_security_helpers_and_db_generators(db_session):
    with pytest.raises(HTTPException) as invalid_token:
        decode_token("not-a-token")
    assert invalid_token.value.status_code == 401

    allowed = enforce_role(allowed_roles=["ROLE_ADMIN"])
    admin = User(username="role@example.com", password="na", role="ROLE_ADMIN", user_level="5")
    assert allowed(admin) is admin

    denied = enforce_role(min_level=10)
    with pytest.raises(HTTPException) as denied_exc:
        denied(admin)
    assert denied_exc.value.status_code == 403
    assert denied_exc.value.detail == "Insufficient user level"

    generator = get_session()
    session = next(generator)
    assert session is not None
    with pytest.raises(StopIteration):
        next(generator)

    with session_scope() as scoped:
        scoped.add(
            User(
                username="scoped@example.com",
                password="pw",
                role="ROLE_USER",
                user_level="1",
            )
        )

    verify = SessionLocal()
    try:
        persisted = verify.query(User).filter(User.username == "scoped@example.com").one()
        assert persisted.username == "scoped@example.com"
    finally:
        verify.close()
