from datetime import datetime

from fastapi_app.app.models import Cam, Event, ObservationCamData, Station, User
from fastapi_app.app.security import create_access_token
from fastapi_app.app.services import user_service


def _observation_kwargs(key: str) -> dict:
    return {
        "observation_key": key,
        "source_hash": f"hash-{key}",
    }


def _auth_header(user: User) -> dict:
    token = create_access_token(
        {
            "username": user.username,
            "user_id": user.id,
            "role": user.role,
            "user_level": user.user_level,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_login_and_user_reads(client, db_session, monkeypatch):
    monkeypatch.setattr(user_service, "verify_password", lambda plain, stored: plain == stored)
    user = User(
        username="test@example.com",
        password="test",
        role="ROLE_USER",
        user_level="1",
        tutorial_completed=False,
        confirmed=True,
    )
    db_session.add(user)
    db_session.commit()

    login = client.post(
        "/api/login",
        json={"username": "test@example.com", "password": "test"},
    )
    assert login.status_code == 200
    payload = login.json()
    assert "accessToken" in payload
    assert payload["id"] == user.id

    headers = {"Authorization": f"Bearer {payload['accessToken']}"}

    get_user = client.get(f"/api/user/{user.id}", headers=headers)
    assert get_user.status_code == 200
    assert get_user.json()["id"] == user.id

    get_details = client.get(f"/api/user/{user.id}/details", headers=headers)
    assert get_details.status_code == 200
    assert get_details.json()["username"] == "test@example.com"

    get_users = client.get("/api/users", headers=headers)
    assert get_users.status_code == 200
    assert isinstance(get_users.json().get("users"), list)


def test_password_reset_request_shape(client, db_session, monkeypatch):
    monkeypatch.setattr(user_service, "send_mail", lambda *args, **kwargs: None)
    db_session.add(
        User(
            username="reset@example.com",
            password="irrelevant",
            role="ROLE_USER",
            user_level="1",
            confirmed=True,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/passwordresetrequest",
        json={"email": "reset@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_tutorialcomplete_authorization_and_update(client, db_session):
    owner = User(
        username="owner@example.com",
        password="na",
        role="ROLE_USER",
        user_level="0",
        tutorial_completed=False,
        confirmed=True,
    )
    other = User(
        username="other@example.com",
        password="na",
        role="ROLE_USER",
        user_level="0",
        tutorial_completed=False,
        confirmed=True,
    )
    db_session.add_all([owner, other])
    db_session.commit()

    forbidden = client.put(
        f"/api/user/{owner.id}/tutorialcomplete",
        headers=_auth_header(other),
        json={"tutorialComplete": True},
    )
    assert forbidden.status_code == 403

    ok = client.put(
        f"/api/user/{owner.id}/tutorialcomplete",
        headers=_auth_header(owner),
        json={"tutorialComplete": True},
    )
    assert ok.status_code == 200
    assert ok.json()["tutorial_completed"] is True
    assert ok.json()["user_level"] == "1"


def test_event_list_search_filter_and_get(client, db_session):
    station = Station(station_name="larvik")
    cam = Cam(station=station, cam_name="cam1")
    event_a = Event(
        datetimetag="20211101010101",
        location="Viken",
        date=datetime(2021, 11, 1, 1, 1, 1),
        user_confirmed=1,
        camera_confirmed=1,
        track_endheight=45.0,
    )
    event_b = Event(
        datetimetag="20230101010101",
        location="Oslo",
        date=datetime(2023, 1, 1, 1, 1, 1),
        user_confirmed=1,
        track_endheight=15.0,
    )
    db_session.add_all([station, cam, event_a, event_b])
    db_session.commit()

    db_session.add(
        ObservationCamData(
            event_id=event_a.id,
            cam_id=cam.id,
            trail_frames=12,
            **_observation_kwargs("larvik:cam1:2021-11-01T01:01:01.000"),
        )
    )
    db_session.commit()

    listed = client.get("/api/events?page=1&limit=1&orderby=date&order=asc")
    assert listed.status_code == 200
    assert listed.json()["currentPage"] == 1
    assert len(listed.json()["events"]) == 1

    page2 = client.get("/api/events?page=2&limit=1")
    assert page2.status_code == 200
    assert page2.json()["currentPage"] == 2

    searched = client.get("/api/events?searchTerm=Viken")
    assert searched.status_code == 200
    assert isinstance(searched.json().get("events"), list)

    filtered = client.get(
        "/api/events?stationName=larvik&year=2021&eventType=Krysspeilet"
    )
    assert filtered.status_code == 200
    assert isinstance(filtered.json(), dict)
    assert len(filtered.json()["events"]) >= 1

    get_one = client.get(f"/api/event/{event_a.id}")
    assert get_one.status_code == 200
    assert get_one.json()["id"] == event_a.id
    assert get_one.json()["event_path"] == "20211101/010101"
    assert get_one.json()["event_type"] == "Krysspeilet"
    assert get_one.json()["thumbnail_url"].endswith("/data/20211101/010101/thumbnail.jpg")
    assert get_one.json()["media"]["image_url"].endswith("/data/20211101/010101/image.jpg")

    get_by_tag = client.get("/api/event/20211101/010101")
    assert get_by_tag.status_code == 200
    assert get_by_tag.json()["id"] == event_a.id


def test_event_filter_options_and_coordinate_report(client, db_session):
    station = Station(station_name="larvik")
    cam = Cam(station=station, cam_name="cam1")
    event = Event(
        datetimetag="20240102030405",
        date=datetime(2024, 1, 2, 3, 4, 5),
        user_confirmed=1,
        camera_confirmed=1,
        track_endheight=55.0,
        track_endlat=59.1,
        track_endlong=10.2,
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            trail_frames=10,
            **_observation_kwargs("larvik:cam1:2024-01-02T03:04:05.000"),
        )
    )
    db_session.commit()

    filter_options = client.get("/api/events/filters")
    assert filter_options.status_code == 200
    payload = filter_options.json()
    assert "2024" in payload["years"]
    assert "larvik" in payload["stations"]
    assert "Krysspeilet" in payload["eventTypes"]

    coordinates = client.get("/api/report/coordinates")
    assert coordinates.status_code == 200
    assert coordinates.json()[0]["lat"] == 59.1
    assert coordinates.json()[0]["lng"] == 10.2


def test_insight_cam_and_station(client, db_session):
    station = Station(station_name="sorreisa")
    cam = Cam(station=station, cam_name="cam2")
    event = Event(
        datetimetag="20211102010101",
        date=datetime(2021, 11, 2, 1, 1, 1),
        user_confirmed=1,
        track_startheight=60.0,
        track_endheight=50.0,
    )
    db_session.add_all([station, cam, event])
    db_session.commit()
    db_session.add(
        ObservationCamData(
            event_id=event.id,
            cam_id=cam.id,
            trail_frames=10,
            **_observation_kwargs("sorreisa:cam2:2021-11-02T01:01:01.000"),
        )
    )
    db_session.commit()

    cam_report = client.get("/api/insight/cam")
    assert cam_report.status_code == 200
    assert isinstance(cam_report.json(), list)
    assert "Kameranavn" in cam_report.json()[0]

    station_report = client.get("/api/insight/station")
    assert station_report.status_code == 200
    assert isinstance(station_report.json(), list)
    assert "Stasjonsnavn" in station_report.json()[0]
