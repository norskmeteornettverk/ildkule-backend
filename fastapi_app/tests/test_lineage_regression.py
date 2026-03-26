from datetime import datetime

import pytest
from PIL import Image
from sqlalchemy import func, select

from fastapi_app.app.config import get_settings
from fastapi_app.app.models import Cam, Event, EventResEntry, ObservationCamData, ObservationTrailPoint, Station


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
        "/api/admin/event-imports",
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

    event_response = client.get(f"/api/events/{event.id}")
    assert event_response.status_code == 200
    payload = event_response.json()
    assert payload["location"] is None
    assert payload["cross_station_confirmed"] is False

    res_response = client.get(f"/api/events/{event.id}/res?limit=10&offset=0")
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
    event_response = client.get(f"/api/events/{event.id}")
    assert event_response.status_code == 200
    observation_payload = event_response.json()["observations"][0]
    assert observation_payload["trail_frames"] is None
    assert observation_payload["summary_latitude"] is None
    assert observation_payload["summary_longitude"] is None
    assert observation_payload["trail_point_count"] == 0

    trail_response = client.get(f"/api/observations/{observation.id}/trail?limit=10&offset=0")
    assert trail_response.status_code == 200
    assert trail_response.json()["totalItems"] == 0
    assert trail_response.json()["trailPoints"] == []


def test_event_detail_and_trail_response_expose_ams_coordinates(client, db_session):
    station = Station(station_name="sorreisa")
    cam = Cam(station=station, cam_name="cam2")
    event = Event(
        datetimetag="20240512235404",
        date=datetime(2024, 5, 12, 23, 54, 4),
        user_confirmed=1,
        camera_confirmed=1,
        track_startheight=80.0,
        track_endheight=45.0,
        track_speed=21.5,
        track_speed_source="average",
        is_deleted=False,
        radiant_ra=13.5,
        radiant_dec=-1.2,
        radiant_ecl_lat=4.5,
        radiant_ecl_long=44.4,
        radiant_zenith_attractor="uncorrected",
    )
    db_session.add_all([station, cam, event])
    db_session.commit()

    observation = ObservationCamData(
        event_id=event.id,
        cam_id=cam.id,
        trail_frames=2,
        trail_ams_coords="60.11,10.21 60.21,10.31",
        trail_positions="10,20 11,21",
        trail_timestamps="1715558044.000 1715558044.040",
        trail_coordinates="60.1,10.2 60.2,10.3",
        observation_key="sorreisa:cam2:2024-05-12T23:54:04.000",
        source_hash="hash-sorreisa:cam2:2024-05-12T23:54:04.000",
    )
    db_session.add(observation)
    db_session.commit()
    db_session.add_all(
        [
            ObservationTrailPoint(
                observation_id=observation.id,
                frame_index=0,
                pixel_x=10.0,
                pixel_y=20.0,
                event_timestamp_us=1715558044000000,
                coord_long=60.1,
                coord_lat=10.2,
                ams_coord_long=60.11,
                ams_coord_lat=10.21,
            ),
            ObservationTrailPoint(
                observation_id=observation.id,
                frame_index=1,
                pixel_x=11.0,
                pixel_y=21.0,
                event_timestamp_us=1715558044040000,
                coord_long=60.2,
                coord_lat=10.3,
                ams_coord_long=60.21,
                ams_coord_lat=10.31,
            ),
        ]
    )
    db_session.commit()

    event_response = client.get(f"/api/events/{event.id}")
    assert event_response.status_code == 200
    observation_payload = event_response.json()["observations"][0]
    assert observation_payload["trail_point_count"] == 2

    trail_response = client.get(f"/api/observations/{observation.id}/trail?limit=10&offset=0")
    assert trail_response.status_code == 200
    assert trail_response.json()["totalItems"] == 2
    assert trail_response.json()["has_ams_coords"] is True
    first_point = trail_response.json()["trailPoints"][0]
    assert first_point["frame_index"] == 0
    assert first_point["pixel_x"] == 10.0
    assert first_point["pixel_y"] == 20.0
    assert first_point["event_timestamp_us"] == 1715558044000000
    assert first_point["event_timestamp"] == pytest.approx(1715558044.0)
    assert first_point["coord_long"] == 60.1
    assert first_point["coord_lat"] == 10.2
    assert first_point["ams_coord_long"] == 60.11
    assert first_point["ams_coord_lat"] == 10.21
    assert "gnomonic_x" in first_point
    assert "gnomonic_y" in first_point
    assert "brightness" in first_point
    assert "dct" in first_point
    assert "size" in first_point
    assert "frame_brightness" in first_point
    assert first_point["gnomonic_x"] is None
    assert first_point["gnomonic_y"] is None
    assert first_point["brightness"] is None
    assert first_point["dct"] is None
    assert first_point["size"] is None
    assert first_point["frame_brightness"] is None
