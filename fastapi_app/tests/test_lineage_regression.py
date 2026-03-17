from PIL import Image
from sqlalchemy import func, select

from fastapi_app.app.config import get_settings
from fastapi_app.app.models import Event, EventResEntry, ObservationCamData, ObservationTrailPoint


def _write_event_txt(path, *, include_trail: bool = True, include_summary: bool = True) -> None:
    lines: list[str] = []
    if include_trail:
        lines.extend(
            [
                "[trail]",
                "frames=3",
                "duration=2.5",
                "positions=10,20 11,21 12,22",
                "timestamps=1715471644.000 1715471644.040 1715471644.080",
                "coordinates=60.1,10.2 60.2,10.3 60.3,10.4",
                "gnomonic=1.1,2.1 1.2,2.2 1.3,2.3",
                "brightness=5 6 7",
                "dct=8 9 10",
                "size=11 12 13",
                "frame_brightness=14 15 16",
            ]
        )
    lines.extend(
        [
            "[video]",
            "start=2024-05-12 23:54:04.000 UTC",
        ]
    )
    if include_summary:
        lines.extend(
            [
                "[summary]",
                "latitude=60.1",
                "longitude=10.2",
                "duration=2.5",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _post_eventload(client):
    return client.post(
        "/api/eventload",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )


def test_reimport_clears_missing_event_source_fields(client, db_session, tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_event_reset")
    event_dir = base / "20230101" / "010101"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (event_dir / "location.txt").write_text("Oslo, Norway\n", encoding="utf-8")
    (event_dir / "event.stat").write_text(
        "\n".join(
            [
                "[track]",
                "startheight = 110 km",
                "endheight = 90 km",
                "[radiant]",
                "shower = Geminids",
            ]
        ),
        encoding="utf-8",
    )
    (event_dir / "event.res").write_text(
        "10.1  20.2  10.1  20.2  110.0 Start\n30.3  40.4  30.3  40.4  90.0 End\n",
        encoding="utf-8",
    )
    _write_event_txt(cam_dir / "event.txt")

    settings = get_settings()
    settings.data_directory = str(base)

    first = _post_eventload(client)
    assert first.status_code == 200, first.text

    event = db_session.scalars(select(Event)).one()
    assert event.location == "Oslo, Norway"
    assert event.track_startheight == 110.0
    assert event.track_endheight == 90.0
    assert event.track_endlat == 40.4
    assert event.radiant_shower == "Geminids"

    (event_dir / "location.txt").unlink()
    (event_dir / "event.stat").unlink()
    (event_dir / "event.res").unlink()

    second = _post_eventload(client)
    assert second.status_code == 200, second.text

    db_session.expire_all()
    event = db_session.scalars(select(Event)).one()
    assert event.location is None
    assert event.track_startheight is None
    assert event.track_endheight is None
    assert event.track_endlat is None
    assert event.track_endlong is None
    assert event.radiant_shower is None
    assert event.camera_confirmed == 0
    res_entry_count = db_session.scalar(
        select(func.count()).select_from(EventResEntry)
    )
    assert res_entry_count == 0

    event_response = client.get(f"/api/event/{event.id}")
    assert event_response.status_code == 200
    payload = event_response.json()
    assert payload["location"] is None
    assert payload["cross_station_confirmed"] is False

    res_response = client.get(f"/api/event/{event.id}/res?limit=10&offset=0")
    assert res_response.status_code == 200
    assert res_response.json()["totalItems"] == 0
    assert res_response.json()["resEntries"] == []


def test_reimport_clears_missing_observation_source_fields(client, db_session, tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_observation_reset")
    event_dir = base / "20230101" / "010101"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    _write_event_txt(cam_dir / "event.txt")

    settings = get_settings()
    settings.data_directory = str(base)

    first = _post_eventload(client)
    assert first.status_code == 200, first.text

    observation = db_session.scalars(select(ObservationCamData)).one()
    assert observation.trail_frames == 3
    assert observation.summary_latitude == 60.1
    assert observation.trail_positions == "10,20 11,21 12,22"
    assert db_session.scalars(select(ObservationTrailPoint)).all()

    _write_event_txt(cam_dir / "event.txt", include_trail=False, include_summary=False)

    second = _post_eventload(client)
    assert second.status_code == 200, second.text

    db_session.expire_all()
    observation = db_session.scalars(select(ObservationCamData)).one()
    trail_points = db_session.scalars(select(ObservationTrailPoint)).all()

    assert observation.trail_frames is None
    assert observation.trail_duration is None
    assert observation.trail_positions is None
    assert observation.trail_timestamps is None
    assert observation.summary_latitude is None
    assert observation.summary_longitude is None
    assert observation.summary_duration is None
    assert trail_points == []

    event = db_session.scalars(select(Event)).one()
    event_response = client.get(f"/api/event/{event.id}")
    assert event_response.status_code == 200
    observation_payload = event_response.json()["observations"][0]
    assert observation_payload["trail_frames"] is None
    assert observation_payload["summary_latitude"] is None
    assert observation_payload["summary_longitude"] is None
    assert observation_payload["trail_point_count"] == 0

    trail_response = client.get(f"/api/observation/{observation.id}/trail?limit=10&offset=0")
    assert trail_response.status_code == 200
    assert trail_response.json()["totalItems"] == 0
    assert trail_response.json()["trailPoints"] == []
