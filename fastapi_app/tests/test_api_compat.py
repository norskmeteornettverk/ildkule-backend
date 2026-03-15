from datetime import datetime

from fastapi_app.app.services import contact_service
from fastapi_app.app.models import Event, User, UserReview
from fastapi_app.app.security import create_access_token


def _auth_header(user_id: int, role: str = "ROLE_USER", user_level: str = "1") -> dict:
    token = create_access_token(
        {
            "username": f"user{user_id}@example.com",
            "user_id": user_id,
            "role": role,
            "user_level": user_level,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_event_review_accepts_legacy_and_modern_payload(client, db_session):
    user = User(
        username="reviewer@example.com",
        password="not-used-in-this-test",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    event = Event(datetimetag="20240101010101", date=datetime.utcnow())
    db_session.add_all([user, event])
    db_session.commit()

    response = client.post(
        f"/api/event/{event.id}/review",
        headers=_auth_header(user.id),
        json={"confirmed": "Positive"},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Takk for din anbefaling (Ja)"

    review = db_session.get(UserReview, (user.id, event.id))
    assert review is not None
    assert review.confirmed == 1

    mismatch = client.post(
        f"/api/event/{event.id}/review",
        headers=_auth_header(user.id),
        json={"eventID": event.id + 1, "userID": user.id, "confirmed": "Positive"},
    )
    assert mismatch.status_code == 400


def test_eventboard_accepts_pagination_params(client, db_session):
    admin = User(
        username="admin@example.com",
        password="not-used-in-this-test",
        role="ROLE_ADMIN",
        user_level="10",
        confirmed=True,
    )
    events = [
        Event(datetimetag=f"2024010101010{i}", date=datetime.utcnow())
        for i in range(1, 4)
    ]
    db_session.add(admin)
    db_session.add_all(events)
    db_session.commit()

    response = client.get(
        "/api/eventboard?page=1&limit=2&orderby=date&order=desc",
        headers=_auth_header(admin.id, role="ROLE_ADMIN", user_level="10"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["currentPage"] == 1
    assert len(payload["events"]) == 2


def test_forms_recaptcha_failure_has_legacy_message_shape(client, monkeypatch):
    monkeypatch.setattr(contact_service, "verify_recaptcha", lambda _token: False)

    contact = client.post(
        "/api/contact",
        json={
            "rcToken": "invalid",
            "form": {
                "fornavn": "Ada",
                "etternavn": "Lovelace",
                "epost": "ada@example.com",
                "melding": "Hei",
            },
        },
    )
    assert contact.status_code == 401
    assert "message" in contact.json()
    assert "error" in contact.json()

    report = client.post(
        "/api/reportmeteor",
        json={
            "rcToken": "invalid",
            "form": {"navn": "Ada", "epost": "ada@example.com"},
        },
    )
    assert report.status_code == 401
    assert "message" in report.json()
    assert "error" in report.json()
