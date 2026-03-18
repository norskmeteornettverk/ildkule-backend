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


def test_insight_reports_use_current_norwegian_wire_keys(client, db_session):
    station = Station(station_name="sorreisa")
    cam = Cam(station=station, cam_name="cam2")
    event = Event(
        datetimetag="20211102010101",
        date=datetime(2021, 11, 2, 1, 1, 1),
        user_confirmed=1,
        camera_confirmed=1,
        track_startheight=60.0,
        track_endheight=20.0,
        track_speed=22.0,
        track_endlat=61.1,
        track_endlong=10.2,
        track_startlat=62.2,
        track_startlong=11.3,
        radiant_ra=13.5,
        radiant_dec=-1.2,
        radiant_ecl_lat=4.5,
        radiant_ecl_long=44.4,
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            trail_frames=10,
            summary_meteor_probability=87.5,
            **_observation_kwargs("sorreisa:cam2:2021-11-02T01:01:01.000"),
        )
    )
    db_session.commit()

    cam_report = client.get("/api/insights/cam")
    assert cam_report.status_code == 200
    cam_row = cam_report.json()[0]
    assert set(cam_row) == {
        "Stasjonsnavn",
        "Kameranavn",
        "ForsteObservasjonsTidspunkt",
        "SisteObervasjonsTidspunkt",
        "DagerMedObservasjoner",
        "DagerSidenSisteObservasjon",
        "Kameraopptak",
        "Hendelser",
        "Krysspeilede",
        "Meteorittkandidater",
    }
    assert cam_row["Stasjonsnavn"] == "Sorreisa"
    assert cam_row["Kameranavn"] == "cam2"
    assert cam_row["Hendelser"] == 1
    assert cam_row["Krysspeilede"] == 1
    assert cam_row["Meteorittkandidater"] == 1

    station_report = client.get("/api/insights/station")
    assert station_report.status_code == 200
    station_row = station_report.json()[0]
    assert set(station_row) == {
        "Stasjonsnavn",
        "ForsteObservasjonsTidspunkt",
        "SisteObervasjonsTidspunkt",
        "DagerMedObservasjoner",
        "DagerSidenSisteObservasjon",
        "Kameraopptak",
        "Hendelser",
        "Krysspeilede",
        "Meteorittkandidater",
    }
    assert station_row["Stasjonsnavn"] == "Sorreisa"
    assert station_row["Hendelser"] == 1

    total_report = client.get("/api/insights/total")
    assert total_report.status_code == 200
    total_rows = total_report.json()
    assert len(total_rows) == 1
    total_row = total_rows[0]
    assert set(total_row) == {
        "ForsteObservasjonsTidspunkt",
        "SisteObervasjonsTidspunkt",
        "DagerMedObservasjoner",
        "DagerSidenSisteObservasjon",
        "Kameraopptak",
        "Hendelser",
        "Krysspeilede",
        "Meteorittkandidater",
    }
    assert total_row["Hendelser"] == 1
    assert total_row["Krysspeilede"] == 1

    coordinates = client.get("/api/insights/coordinates")
    assert coordinates.status_code == 200
    coordinate_row = coordinates.json()[0]
    assert "station_cam" in coordinate_row
    assert "number_of_stations" in coordinate_row
    assert "StationCam" not in coordinate_row
    assert "NumberOfStations" not in coordinate_row
    assert coordinate_row["station_cam"] == "cam2@sorreisa"
    assert coordinate_row["number_of_stations"] == 1
    assert coordinate_row["ai_score"] == 87.5


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
    assert item["datetimetag"] == "20240203040506"
    assert item["date"] == "2024-02-03T04:05:06"
    assert item["camera_confirmed"] == 1
    assert item["user_confirmed"] == 1
    assert "preview" in item
    assert "times" in item
    assert "cross_station_confirmed" in item
    assert "station_summary" in item
    assert item["ratings"] == 2
    assert item["positive_ratings"] == 1
    assert item["negative_ratings"] == 1
    assert item["classification"]["final_classification"] == "Meteor"
    assert item["classification"]["user_confirmed"] == 1


def test_coordinates_report_supports_filters_and_legacy_aliases(client, db_session):
    station_a = Station(station_name="alta")
    station_b = Station(station_name="larvik")
    cam_a = Cam(station=station_a, cam_name="cam9")
    cam_b = Cam(station=station_b, cam_name="cam2")
    matching = Event(
        datetimetag="20240102030405",
        location="Finnmark",
        date=datetime(2024, 1, 2, 3, 4, 5),
        camera_confirmed=1,
        track_startlat=70.4,
        track_startlong=24.2,
        track_startheight=90.0,
        track_endlat=69.9,
        track_endlong=23.3,
        track_endheight=22.0,
        track_speed=20.0,
        radiant_ra=12.3,
        radiant_dec=-1.2,
        radiant_ecl_lat=4.5,
        radiant_ecl_long=44.4,
    )
    non_matching = Event(
        datetimetag="20240302030405",
        location="Vestfold",
        date=datetime(2024, 3, 2, 3, 4, 5),
        camera_confirmed=0,
        track_startlat=60.4,
        track_startlong=10.2,
        track_startheight=80.0,
        track_endlat=59.9,
        track_endlong=10.3,
        track_endheight=55.0,
        track_speed=28.0,
        radiant_ra=10.0,
        radiant_dec=-5.0,
        radiant_ecl_lat=2.0,
        radiant_ecl_long=20.0,
    )
    db_session.add_all([station_a, station_b, cam_a, cam_b, matching, non_matching])
    db_session.commit()
    db_session.add_all(
        [
            ObservationCamData(
                event_id=matching.id,
                cam_id=cam_a.id,
                summary_meteor_probability=73.2,
                **_observation_kwargs("alta:cam9:2024-01-02T03:04:05.000"),
            ),
            ObservationCamData(
                event_id=non_matching.id,
                cam_id=cam_b.id,
                summary_meteor_probability=12.0,
                **_observation_kwargs("larvik:cam2:2024-03-02T03:04:05.000"),
            ),
        ]
    )
    db_session.commit()

    filtered = client.get(
        "/api/insights/coordinates",
        params={
            "from_date": "2024-01-01",
            "to_date": "2024-01-31",
            "stations": "alta",
            "cross_station_confirmed": "true",
            "candidate": "true",
        },
    )
    assert filtered.status_code == 200
    payload = filtered.json()
    assert [row["id"] for row in payload] == [matching.id]

    legacy = client.post(
        "/api/insight/coordinates",
        json={
            "from_date": "2024-01-01",
            "to_date": "2024-01-31",
            "stations": ["alta"],
            "cross_station_confirmed": True,
            "candidate": True,
        },
    )
    assert legacy.status_code == 200
    legacy_row = legacy.json()[0]
    assert legacy_row["StationCam"] == "cam9@alta"
    assert legacy_row["NumberOfStations"] == 1
    assert legacy_row["ProperTriangulation"] == "1"
    assert legacy_row["SourceBadDetection"] == "0"
    assert round(legacy_row["MeteorScoreHighest"], 3) == 0.732

    report_alias = client.get("/api/report/coordinates")
    assert report_alias.status_code == 200
    assert "StationCam" in report_alias.json()[0]


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
