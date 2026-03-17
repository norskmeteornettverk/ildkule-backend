from datetime import datetime

from fastapi_app.app.services import contact_service
from fastapi_app.app.models import Cam, Event, ObservationCamData, Station, User, UserReview
from fastapi_app.app.security import create_access_token


def _observation_kwargs(key: str) -> dict:
    return {
        "observation_key": key,
        "source_hash": f"hash-{key}",
    }


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
        f"/api/events/{event.id}/review",
        headers=_auth_header(user.id),
        json={"confirmed": "Positive"},
    )
    assert response.status_code == 200
    assert response.json()["msg"] == "Takk for din anbefaling (Ja)"

    review = db_session.get(UserReview, (user.id, event.id))
    assert review is not None
    assert review.confirmed == 1

    mismatch = client.post(
        f"/api/events/{event.id}/review",
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
        "/api/admin/events?page=1&limit=2&orderby=date&order=desc",
        headers=_auth_header(admin.id, role="ROLE_ADMIN", user_level="10"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["currentPage"] == 1
    assert len(payload["events"]) == 2


def test_eventboard_returns_admin_fields_and_public_card_fields(client, db_session):
    admin = User(
        username="admin-board@example.com",
        password="not-used-in-this-test",
        role="ROLE_ADMIN",
        user_level="10",
        confirmed=True,
    )
    reviewer = User(
        username="reviewer-board@example.com",
        password="not-used-in-this-test",
        role="ROLE_USER",
        user_level="1",
        confirmed=True,
    )
    station = Station(station_name="harestua")
    cam = Cam(station=station, cam_name="cam1")
    event = Event(
        datetimetag="20240203040506",
        location="Innlandet",
        date=datetime(2024, 2, 3, 4, 5, 6),
        user_confirmed=1,
        camera_confirmed=1,
        track_endheight=45.0,
    )
    db_session.add_all([admin, reviewer, station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            trail_frames=10,
            **_observation_kwargs("harestua:cam1:2024-02-03T04:05:06.000"),
        )
    )
    db_session.add_all(
        [
            UserReview(user_id=admin.id, event_id=event.id, confirmed=1),
            UserReview(user_id=reviewer.id, event_id=event.id, confirmed=0),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/admin/events?page=1&limit=10&orderby=ratings&order=desc",
        headers=_auth_header(admin.id, role="ROLE_ADMIN", user_level="10"),
    )

    assert response.status_code == 200
    item = response.json()["events"][0]
    assert "preview" in item
    assert "times" in item
    assert "cross_station_confirmed" in item
    assert "station_summary" in item
    assert item["ratings"] == 2
    assert item["positive_ratings"] == 1
    assert item["negative_ratings"] == 1
    assert item["classification"]["final_classification"] == "Meteor"
    assert item["classification"]["user_confirmed"] == 1


def test_forms_recaptcha_failure_has_legacy_message_shape(client, monkeypatch):
    monkeypatch.setattr(contact_service, "verify_recaptcha", lambda _token: False)

    contact = client.post(
        "/api/forms/contact",
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
        "/api/forms/meteor-report",
        json={
            "rcToken": "invalid",
            "form": {"navn": "Ada", "epost": "ada@example.com"},
        },
    )
    assert report.status_code == 401
    assert "message" in report.json()
    assert "error" in report.json()


def test_reportmeteor_accepts_multipart_attachments(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(contact_service, "verify_recaptcha", lambda _token: True)

    def fake_send_mail(recipient, subject, html_body, alt_body=None, attachments=None):
        captured["recipient"] = recipient
        captured["subject"] = subject
        captured["html_body"] = html_body
        captured["attachments"] = list(attachments or [])

    monkeypatch.setattr(contact_service, "send_mail", fake_send_mail)

    response = client.post(
        "/api/forms/meteor-report",
        data={
            "rcToken": "valid",
            "navn": "Ada",
            "epost": "ada@example.com",
            "observationTime": "2026-03-15T20:15:00",
            "latitude": "59.91",
            "longitude": "10.75",
            "directionText": "Fra vest mot nord",
        },
        files=[
            ("attachments", ("meteor.jpg", b"binary-image", "image/jpeg")),
        ],
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Observasjon sendt"
    assert captured["attachments"][0]["filename"] == "meteor.jpg"
    assert "Fra vest mot nord" in captured["html_body"]
