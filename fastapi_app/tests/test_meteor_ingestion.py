from pathlib import Path
import shutil
from datetime import datetime

import pytest
from PIL import Image
from sqlalchemy import select

from fastapi_app.app.config import get_settings
from fastapi_app.app.models import (
    Cam,
    Event,
    EventResEntry,
    ObservationCamData,
    ObservationTrailPoint,
    Station,
)
from fastapi_app.app.services.file_mapper import FileToObjectMapper


@pytest.fixture(scope="function")
def sample_data_dir(tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data")
    date_dir = base / "20230101"
    event_dir = date_dir / "010101"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    # Create sample files
    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (event_dir / "location.txt").write_text("Oslo, Norway\n", encoding="utf-8")
    (event_dir / "event.stat").write_text(
        "startheight = 110\nendheight = 90\nshower = Geminids Event Shower\n",
        encoding="utf-8",
    )
    (event_dir / "event.res").write_text(
        "10.1  20.2  10.1  20.2  110.0 Start\n30.3  40.4  30.3  40.4  90.0 End\n",
        encoding="utf-8",
    )
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=3",
                "duration=2.5",
                "positions=10,20 11,21 12,22",
                "timestamps=1715471644.000123 1715471644.040456 1715471644.080789",
                "coordinates=60.1,10.2 60.2,10.3 60.3,10.4",
                "ams_coords=60.11,10.21 60.21,10.31 60.31,10.41",
                "gnomonic=1.1,2.1 1.2,2.2 1.3,2.3",
                "brightness=5 6 7",
                "dct=8 9 10",
                "size=11 12 13",
                "frame_brightness=14 15 16",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=60.1",
                "longitude=10.2",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "centroid.txt").write_text(
        "\n".join(
            [
                "0 0.0 10.21 60.11 1.0 STA 2024-05-11 23:54:04.000 UTC",
                "1 0.04 10.31 60.21 1.0 STA 2024-05-11 23:54:04.040 UTC",
                "2 0.08 10.41 60.31 1.0 STA 2024-05-11 23:54:04.080 UTC",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "centroid2.txt").write_text(
        "\n".join(
            [
                "0 0.0 10.22 60.12 1.0 STA 2024-05-11 23:54:04.000 UTC",
                "1 0.04 10.32 60.22 1.0 STA 2024-05-11 23:54:04.040 UTC",
                "2 0.08 10.42 60.32 1.0 STA 2024-05-11 23:54:04.080 UTC",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)
    return str(base)


def test_file_mapper_reads_event(sample_data_dir):
    mapper = FileToObjectMapper(sample_data_dir, "20230101", "20230102")
    records = mapper.map()
    assert len(records) == 1
    record = records[0]

    assert record.event["camera_confirmed"] == 1
    assert record.event["location"] == "Oslo, Norway"
    assert record.event["track_endlat"] == 40.4
    assert len(record.res_entries) == 2
    assert len(record.observations) == 1
    observation = record.observations[0]
    assert observation.values["trail_frames"] == "3"
    assert observation.observation_key == "stationalpha:cam01:2024-05-12T23:54:04.000"
    assert len(observation.trail_points) == 3
    assert observation.values["trail_ams_coords"] == "60.11,10.21 60.21,10.31 60.31,10.41"
    assert observation.values["trail_centroid"].startswith("0 0.0 10.21 60.11 1.0 STA")
    assert observation.values["trail_centroid2"].startswith("0 0.0 10.22 60.12 1.0 STA")
    assert observation.trail_points[0].event_timestamp_us == 1715471644000123
    assert observation.trail_points[0].event_timestamp == pytest.approx(1715471644.000123)
    assert observation.trail_points[0].ams_coord_long == 60.11
    assert observation.trail_points[0].ams_coord_lat == 10.21
    assert observation.trail_points[0].centroid_coord_long == 60.11
    assert observation.trail_points[0].centroid_coord_lat == 10.21
    assert observation.trail_points[0].centroid2_coord_long == 60.12
    assert observation.trail_points[0].centroid2_coord_lat == 10.22

    thumb = Path(sample_data_dir) / "20230101" / "010101" / "thumbnail.jpg"
    assert thumb.exists(), "Thumbnail should be generated for each event"


def test_file_mapper_reads_realistic_non_crossbearing_sample(tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_realistic_single")
    event_dir = base / "20220511" / "214208"
    cam2_dir = event_dir / "larvik" / "cam2"
    cam3_dir = event_dir / "larvik" / "cam3"
    cam2_dir.mkdir(parents=True, exist_ok=True)
    cam3_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (cam2_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames = 30",
                "duration = 1.94",
                "brightness = 47 44 97",
                "dct midpoint = 3",
                "[video]",
                "height = 1536",
                "[config]",
                "minspeedkms = 2.000000",
                "maxspeedkms = 50.000000",
                "spacing correlation = 0.900000",
                "gnomonic correlation = 0.998500",
                "logfile = /event/cam2/metdetect.log",
                "eventdir = /event/cam2/events",
                "brightness = 6",
                "[summary]",
                "latitude = 59.090854",
                "longitude = 10.098182",
                "duration = 1.97",
                "meteor_probability = 0.90302",
            ]
        ),
        encoding="utf-8",
    )
    (cam3_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames = 28",
                "duration = 1.80",
                "[summary]",
                "latitude = 59.090854",
                "longitude = 10.098182",
            ]
        ),
        encoding="utf-8",
    )

    mapper = FileToObjectMapper(base, "20220511", "20220512")
    records = mapper.map()
    assert len(records) == 1
    record = records[0]

    assert record.event["camera_confirmed"] == 0
    assert "location" not in record.event or record.event["location"] is None
    assert len(record.observations) == 2

    first = record.observations[0]
    assert first.station_name == "larvik"
    assert first.cam_name == "cam2"
    assert first.values["trail_frames"] == "30"
    assert first.values["trail_dct_midpoint"] == "3"
    assert first.values["video_heigth"] == "1536"
    assert first.values["config_minspeed_kms"] == "2.000000"
    assert first.values["config_spacing_correlation"] == "0.900000"
    assert first.values["config_log_file"] == "/event/cam2/metdetect.log"
    assert first.values["config_brightness"] == "6"
    assert first.values["summary_duration"] == "1.97"


def test_file_mapper_reads_mixed_ams_coordinates_without_breaking_non_ams_observations(tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_mixed_ams")
    event_dir = base / "20240512" / "235404"
    ams_cam_dir = event_dir / "StationAlpha" / "Cam01"
    plain_cam_dir = event_dir / "StationAlpha" / "Cam02"
    ams_cam_dir.mkdir(parents=True, exist_ok=True)
    plain_cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    ams_payload = "\n".join(
        [
            "[trail]",
            "frames=3",
            "positions=10,20 11,21 12,22",
            "timestamps=1715558044.000 1715558044.040 1715558044.080",
            "coordinates=60.1,10.2 60.2,10.3 60.3,10.4",
            "ams_coords=60.11,10.21 60.21,10.31 60.31,10.41",
            "[video]",
            "start=2024-05-12 23:54:04.000 UTC",
            "[summary]",
            "latitude=60.1",
            "longitude=10.2",
        ]
    )
    plain_payload = "\n".join(
        [
            "[trail]",
            "frames=3",
            "positions=20,30 21,31 22,32",
            "timestamps=1715558044.000 1715558044.040 1715558044.080",
            "coordinates=61.1,11.2 61.2,11.3 61.3,11.4",
            "[video]",
            "start=2024-05-12 23:54:04.000 UTC",
            "[summary]",
            "latitude=61.1",
            "longitude=11.2",
        ]
    )
    (ams_cam_dir / "event.txt").write_text(ams_payload, encoding="utf-8")
    (plain_cam_dir / "event.txt").write_text(plain_payload, encoding="utf-8")

    mapper = FileToObjectMapper(base, "20240512", "20240513")
    records = mapper.map()
    assert len(records) == 1

    observations = {observation.cam_name: observation for observation in records[0].observations}
    assert set(observations) == {"Cam01", "Cam02"}

    ams_observation = observations["Cam01"]
    plain_observation = observations["Cam02"]
    assert ams_observation.values["trail_ams_coords"] == "60.11,10.21 60.21,10.31 60.31,10.41"
    assert plain_observation.values.get("trail_ams_coords") is None
    assert ams_observation.trail_points[0].event_timestamp_us == 1715558044000000
    assert ams_observation.trail_points[0].event_timestamp == pytest.approx(1715558044.0)
    assert ams_observation.trail_points[0].ams_coord_long == 60.11
    assert ams_observation.trail_points[0].ams_coord_lat == 10.21
    assert plain_observation.trail_points[0].ams_coord_long is None
    assert plain_observation.trail_points[0].ams_coord_lat is None


def test_file_mapper_reads_realistic_crossbearing_sample(tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_realistic_cross")
    event_dir = base / "20220103" / "181852"
    larvik_dir = event_dir / "larvik" / "cam4"
    kristiansand_dir = event_dir / "kristiansand" / "cam4"
    larvik_dir.mkdir(parents=True, exist_ok=True)
    kristiansand_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (event_dir / "location.txt").write_text("Agder\n", encoding="utf-8")
    (event_dir / "obs_2022-01-03_18_18_52.stat").write_text(
        "\n".join(
            [
                "[track]",
                "startheight = 96.1 km",
                "endheight = 86.7 km",
                "groundtrack = 24.3 km",
                "course = 162.1 deg",
                "incidence = 20.8 deg",
                "speed = 41.3 km/s",
                "speed_source = average",
                "",
                "[fit]",
                "error = 0.0",
                "quality = 0.31",
                "",
                "[radiant]",
                "ra = 230.92 deg",
                "dec = 50.30 deg",
                "ecl_long = 200.28 deg",
                "ecl_lat = 64.57 deg",
                "shower = kvadrantidene",
                "zenith_attractor = uncorrected",
                "",
                "[date]",
                "timestamp = 1641233933.415000",
            ]
        ),
        encoding="utf-8",
    )
    (event_dir / "obs_2022-01-03_18_18_52.res").write_text(
        "\n".join(
            [
                "  6.3858  58.415143   6.3858  58.4151   96.1 Start",
                "  6.5127  58.207204   6.5127  58.2072   86.7 End",
            ]
        ),
        encoding="utf-8",
    )
    event_payload = "\n".join(
        [
            "[trail]",
            "frames = 12",
            "duration = 0.74",
            "dct midpoint = 3",
            "timestamps = 1641233933.415000 1641233933.455000 1641233933.495000 1641233933.535000 1641233933.575000 1641233933.615000 1641233933.655000 1641233933.695000 1641233933.735000 1641233933.775000 1641233933.815000 1641233933.855000",
            "[video]",
            "height = 1536",
            "[config]",
            "minspeedkms = 2.000000",
            "logfile = /event/cam4/metdetect.log",
            "[summary]",
            "latitude = 59.090854",
            "longitude = 10.098182",
            "duration = 0.62",
        ]
    )
    (larvik_dir / "event.txt").write_text(event_payload, encoding="utf-8")
    (kristiansand_dir / "event.txt").write_text(event_payload, encoding="utf-8")

    mapper = FileToObjectMapper(base, "20220103", "20220104")
    records = mapper.map()
    assert len(records) == 1
    record = records[0]

    assert record.event["camera_confirmed"] == 1
    assert record.event["location"] == "Agder"
    assert record.event["track_startlat"] == 58.415143
    assert record.event["track_endlat"] == 58.207204
    assert record.event["track_startheight"] == "96.1 km"
    assert record.event["radiant_shower"] == "kvadrantidene"
    assert len(record.observations) == 2


def test_file_mapper_marks_crossbearing_when_res_or_stat_exist_without_location(tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_crossbearing_without_location")
    event_dir = base / "20220511" / "000559"
    cam_dir = event_dir / "voksenlia" / "cam1"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (event_dir / "obs_2022-05-11_00_05_59.stat").write_text(
        "startheight = 79.6 km\nendheight = 50.4 km\n",
        encoding="utf-8",
    )
    (event_dir / "obs_2022-05-11_00_05_59.res").write_text(
        "\n".join(
            [
                "9.3920  56.254205   9.3920  56.2542   79.6 Start",
                "9.6251  56.902673   9.6251  56.9027   50.4 End",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames = 2",
                "positions = 10,20 11,21",
                "timestamps = 1652227559.370 1652227559.410",
            ]
        ),
        encoding="utf-8",
    )

    mapper = FileToObjectMapper(base, "20220511", "20220512")
    records = mapper.map()

    assert len(records) == 1
    assert records[0].event["camera_confirmed"] == 1
    assert records[0].event.get("location") is None
    assert len(records[0].res_entries) == 2


def test_file_mapper_supports_sectioned_event_aliases(tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_aliases")
    event_dir = base / "20220511" / "214208"
    cam_dir = event_dir / "larvik" / "cam2"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames = 30",
                "brightness = 47 44 97",
                "dct midpoint = 3",
                "[video]",
                "height = 1536",
                "[config]",
                "minspeedkms = 2.000000",
                "spacing correlation = 0.900000",
                "gnomonic correlation = 0.998500",
                "logfile = /event/cam2/metdetect.log",
                "eventdir = /event/cam2/events",
                "brightness = 6",
                "[summary]",
                "latitude = 59.090854",
                "longitude = 10.098182",
                "duration = 1.97",
            ]
        ),
        encoding="utf-8",
    )

    mapper = FileToObjectMapper(base, "20220511", "20220512")
    records = mapper.map()
    assert len(records) == 1

    observation = records[0].observations[0]
    assert observation.values["trail_frames"] == "30"
    assert observation.values["trail_brightness"] == "47 44 97"
    assert observation.values["trail_dct_midpoint"] == "3"
    assert observation.values["video_heigth"] == "1536"
    assert observation.values["config_minspeed_kms"] == "2.000000"
    assert observation.values["config_spacing_correlation"] == "0.900000"
    assert observation.values["config_gnomonic_correlation"] == "0.998500"
    assert observation.values["config_log_file"] == "/event/cam2/metdetect.log"
    assert observation.values["config_event_dir"] == "/event/cam2/events"
    assert observation.values["config_brightness"] == "6"
    assert observation.values["summary_latitude"] == "59.090854"
    assert observation.values["summary_duration"] == "1.97"


def test_eventload_endpoint_ingests_data(client, db_session, sample_data_dir):
    response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert "Innlasting av data" in payload["message"]

    db_session.expire_all()
    event = db_session.scalars(select(Event)).first()
    assert event is not None
    assert event.datetimetag == "20230101010101"
    assert event.camera_confirmed == 1

    station = db_session.scalars(select(Station)).first()
    cam = db_session.scalars(select(Cam)).first()
    observation = db_session.scalars(select(ObservationCamData)).first()
    res_entries = db_session.scalars(
        select(EventResEntry).order_by(EventResEntry.line_no.asc())
    ).all()
    trail_points = db_session.scalars(
        select(ObservationTrailPoint).order_by(ObservationTrailPoint.frame_index.asc())
    ).all()

    assert station is not None and station.station_name == "StationAlpha"
    assert cam is not None and cam.cam_name == "Cam01"
    assert observation is not None
    assert observation.observation_key == "stationalpha:cam01:2024-05-12T23:54:04.000"
    assert observation.source_hash
    assert str(observation.trail_frames) == "3"
    assert len(res_entries) == 2
    assert res_entries[0].entry_type == "start"
    assert len(trail_points) == 3
    assert trail_points[0].pixel_x == 10.0
    assert observation.trail_ams_coords == "60.11,10.21 60.21,10.31 60.31,10.41"
    assert observation.trail_centroid.startswith("0 0.0 10.21 60.11 1.0 STA")
    assert observation.trail_centroid2.startswith("0 0.0 10.22 60.12 1.0 STA")
    assert trail_points[0].event_timestamp_us == 1715471644000123
    assert trail_points[0].event_timestamp == pytest.approx(1715471644.000123)
    assert trail_points[0].ams_coord_long == 60.11
    assert trail_points[0].ams_coord_lat == 10.21
    assert trail_points[0].centroid_coord_long == 60.11
    assert trail_points[0].centroid_coord_lat == 10.21
    assert trail_points[0].centroid2_coord_long == 60.12
    assert trail_points[0].centroid2_coord_lat == 10.22

    res_response = client.get(f"/api/events/{event.id}/res?limit=10&offset=0")
    assert res_response.status_code == 200
    assert res_response.json()["totalItems"] == 2
    assert res_response.json()["resEntries"][0]["entry_type"] == "start"

    trail_response = client.get(
        f"/api/observations/{observation.id}/trail?limit=10&offset=0"
    )
    assert trail_response.status_code == 200
    assert trail_response.json()["totalItems"] == 3
    assert trail_response.json()["has_ams_coords"] is True
    assert trail_response.json()["has_centroid"] is True
    assert trail_response.json()["has_centroid2"] is True
    first_point = trail_response.json()["trailPoints"][0]
    assert first_point["frame_index"] == 0
    assert first_point["pixel_x"] == 10.0
    assert first_point["pixel_y"] == 20.0
    assert first_point["event_timestamp_us"] == 1715471644000123
    assert first_point["event_timestamp"] == pytest.approx(1715471644.000123)
    assert first_point["coord_long"] == 60.1
    assert first_point["coord_lat"] == 10.2
    assert first_point["ams_coord_long"] == 60.11
    assert first_point["ams_coord_lat"] == 10.21
    assert first_point["centroid_coord_long"] == 60.11
    assert first_point["centroid_coord_lat"] == 10.21
    assert first_point["centroid2_coord_long"] == 60.12
    assert first_point["centroid2_coord_lat"] == 10.22
    assert first_point["gnomonic_x"] == 1.1
    assert first_point["gnomonic_y"] == 2.1
    assert first_point["brightness"] == 5.0
    assert first_point["dct"] == 8.0
    assert first_point["size"] == 11.0
    assert first_point["frame_brightness"] == 14.0


def test_eventload_ingests_centroid_without_centroid2(client, db_session, tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_centroid_only")
    event_dir = base / "20230101" / "010101"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=2",
                "positions=10,20 11,21",
                "timestamps=1715471644.000 1715471644.040",
                "coordinates=60.1,10.2 60.2,10.3",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=60.1",
                "longitude=10.2",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "centroid.txt").write_text(
        "\n".join(
            [
                "0 0.0 10.25 60.15 1.0 STA 2024-05-11 23:54:04.000 UTC",
                "1 0.04 10.35 60.25 1.0 STA 2024-05-11 23:54:04.040 UTC",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert response.status_code == 200, response.text

    observation = db_session.scalars(select(ObservationCamData)).one()
    trail_points = db_session.scalars(
        select(ObservationTrailPoint).order_by(ObservationTrailPoint.frame_index.asc())
    ).all()
    assert observation.trail_centroid is not None
    assert observation.trail_centroid2 is None
    assert trail_points[0].centroid_coord_long == 60.15
    assert trail_points[0].centroid2_coord_long is None

    trail_response = client.get(f"/api/observations/{observation.id}/trail")
    assert trail_response.status_code == 200
    payload = trail_response.json()
    assert payload["has_centroid"] is True
    assert payload["has_centroid2"] is False
    assert payload["trailPoints"][0]["centroid_coord_long"] == 60.15
    assert payload["trailPoints"][0]["centroid2_coord_long"] is None


def test_eventload_matches_centroid_rows_by_timestamp_and_keeps_raw_on_length_mismatch(
    client, db_session, tmp_path_factory
):
    base = tmp_path_factory.mktemp("event_data_centroid_mismatch")
    event_dir = base / "20230101" / "010101"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=2",
                "positions=10,20 11,21",
                "timestamps=1715471644.000 1715471644.040",
                "coordinates=60.1,10.2 60.2,10.3",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=60.1",
                "longitude=10.2",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "centroid.txt").write_text(
        "\n".join(
            [
                "0 0.0 10.25 60.15 1.0 STA 2024-05-11 23:54:04.000 UTC",
                "1 0.04 10.35 60.25 1.0 STA 2024-05-11 23:54:04.040 UTC",
                "2 0.08 10.45 60.35 1.0 STA 2024-05-11 23:54:04.080 UTC",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert response.status_code == 200, response.text

    observation = db_session.scalars(select(ObservationCamData)).one()
    trail_points = db_session.scalars(
        select(ObservationTrailPoint).order_by(ObservationTrailPoint.frame_index.asc())
    ).all()
    assert observation.trail_centroid is not None
    assert len(trail_points) == 2
    assert trail_points[0].centroid_coord_long == 60.15
    assert trail_points[1].centroid_coord_long == 60.25


def test_eventload_clears_centroid_fields_when_file_disappears(
    client, db_session, tmp_path_factory
):
    base = tmp_path_factory.mktemp("event_data_centroid_reload")
    event_dir = base / "20230101" / "010101"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    event_txt = "\n".join(
        [
            "[trail]",
            "frames=2",
            "positions=10,20 11,21",
            "timestamps=1715471644.000 1715471644.040",
            "coordinates=60.1,10.2 60.2,10.3",
            "[video]",
            "start=2024-05-12 23:54:04.000 UTC",
            "[summary]",
            "latitude=60.1",
            "longitude=10.2",
        ]
    )
    (cam_dir / "event.txt").write_text(event_txt, encoding="utf-8")
    centroid_path = cam_dir / "centroid.txt"
    centroid_path.write_text(
        "\n".join(
            [
                "0 0.0 10.25 60.15 1.0 STA 2024-05-11 23:54:04.000 UTC",
                "1 0.04 10.35 60.25 1.0 STA 2024-05-11 23:54:04.040 UTC",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    first = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert first.status_code == 200

    centroid_path.unlink()

    second = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert second.status_code == 200

    db_session.expire_all()
    observation = db_session.scalars(select(ObservationCamData)).one()
    trail_points = db_session.scalars(
        select(ObservationTrailPoint).order_by(ObservationTrailPoint.frame_index.asc())
    ).all()
    assert observation.trail_centroid is None
    assert observation.trail_centroid2 is None
    assert trail_points[0].centroid_coord_long is None
    assert trail_points[0].centroid_coord_lat is None


def test_eventload_accepts_event_folder_suffix_in_datetimetag(
    client, db_session, tmp_path_factory
):
    base = tmp_path_factory.mktemp("event_data_suffix_tag")
    event_dir = base / "20230101" / "010101b"
    cam_dir = event_dir / "StationAlpha" / "Cam01"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=2",
                "positions=10,20 11,21",
                "timestamps=1715471644.000 1715471644.040",
                "coordinates=60.1,10.2 60.2,10.3",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=60.1",
                "longitude=10.2",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "centroid.txt").write_text(
        "\n".join(
            [
                "0 0.0 10.21 60.11 1.0 STA 2024-05-12 23:54:04.000 UTC",
                "1 0.04 10.31 60.21 1.0 STA 2024-05-12 23:54:04.040 UTC",
                "2 0.08 10.41 60.31 1.0 STA 2024-05-12 23:54:04.080 UTC",
            ]
        ),
        encoding="utf-8",
    )
    (cam_dir / "centroid2.txt").write_text(
        "\n".join(
            [
                "0 0.0 10.22 60.12 1.0 STA 2024-05-12 23:54:04.000 UTC",
                "1 0.04 10.32 60.22 1.0 STA 2024-05-12 23:54:04.040 UTC",
                "2 0.08 10.42 60.32 1.0 STA 2024-05-12 23:54:04.080 UTC",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert response.status_code == 200, response.text

    db_session.expire_all()
    event = db_session.scalars(select(Event)).one()
    assert event.datetimetag == "20230101010101b"
    assert event.date.isoformat() == "2023-01-01T01:01:01"


def test_eventload_reloads_same_observation_without_duplicates(client, db_session, tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_reload")
    date_dir = base / "20230101"
    first_event_dir = date_dir / "010101"
    second_event_dir = date_dir / "010202"
    first_cam_dir = first_event_dir / "Gaustatoppen" / "cam3"
    second_cam_dir = second_event_dir / "Gaustatoppen" / "cam3"
    first_cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(first_event_dir / "image.jpg")
    (first_cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=2",
                "positions=100,200 110,210",
                "timestamps=1715550000.000 1715550000.040",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=59.8",
                "longitude=8.6",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    first_response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert first_response.status_code == 200

    original_observation = db_session.scalars(select(ObservationCamData)).one()
    original_event = db_session.scalars(select(Event)).one()

    shutil.rmtree(first_event_dir)
    second_cam_dir.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 600), "white").save(second_event_dir / "image.jpg")
    (second_cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=3",
                "positions=100,200 110,210 120,220",
                "timestamps=1715550000.000 1715550000.040 1715550000.080",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=59.8",
                "longitude=8.6",
            ]
        ),
        encoding="utf-8",
    )

    second_response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert second_response.status_code == 200

    db_session.expire_all()
    observations = db_session.scalars(select(ObservationCamData)).all()
    events = db_session.scalars(select(Event).order_by(Event.id.asc())).all()
    trail_points = db_session.scalars(
        select(ObservationTrailPoint).order_by(ObservationTrailPoint.frame_index.asc())
    ).all()

    assert len(observations) == 1
    assert observations[0].id == original_observation.id
    assert len(events) == 2
    assert observations[0].event_id != original_event.id
    assert observations[0].event.datetimetag == "20230101010202"
    deleted_event = next(event for event in events if event.id == original_event.id)
    active_event = next(event for event in events if event.id != original_event.id)
    assert deleted_event.is_deleted is True
    assert deleted_event.deleted_at is not None
    assert deleted_event.deletion_reason == "missing_from_import"
    assert active_event.is_deleted is False
    assert active_event.deletion_reason is None
    assert observations[0].is_deleted is False
    assert observations[0].deletion_reason is None
    assert len(trail_points) == 3

    visible_listing = client.get("/api/events")
    assert visible_listing.status_code == 200
    returned_ids = [item["id"] for item in visible_listing.json()["events"]]
    assert active_event.id in returned_ids
    assert deleted_event.id not in returned_ids

    deleted_listing = client.get("/api/events?includeDeleted=true")
    assert deleted_listing.status_code == 200
    returned_ids = [item["id"] for item in deleted_listing.json()["events"]]
    assert active_event.id in returned_ids
    assert deleted_event.id in returned_ids


def test_eventload_marks_missing_observation_deleted(client, db_session, tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_missing_observation")
    event_dir = base / "20230101" / "010101"
    first_cam_dir = event_dir / "Gaustatoppen" / "cam3"
    second_cam_dir = event_dir / "Gaustatoppen" / "cam4"
    first_cam_dir.mkdir(parents=True, exist_ok=True)
    second_cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    event_payload = "\n".join(
        [
            "[trail]",
            "frames=2",
            "positions=100,200 110,210",
            "timestamps=1715550000.000 1715550000.040",
            "[video]",
            "start=2024-05-12 23:54:04.000 UTC",
            "[summary]",
            "latitude=59.8",
            "longitude=8.6",
        ]
    )
    (first_cam_dir / "event.txt").write_text(event_payload, encoding="utf-8")
    (second_cam_dir / "event.txt").write_text(
        event_payload.replace("23:54:04.000", "23:54:05.000"),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    first_response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert first_response.status_code == 200

    observations = db_session.scalars(
        select(ObservationCamData).order_by(ObservationCamData.id.asc())
    ).all()
    assert len(observations) == 2

    shutil.rmtree(second_cam_dir)

    second_response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert second_response.status_code == 200

    db_session.expire_all()
    observations = db_session.scalars(
        select(ObservationCamData).order_by(ObservationCamData.id.asc())
    ).all()
    deleted_observation = next(
        observation for observation in observations if observation.cam.cam_name == "cam4"
    )
    active_observation = next(
        observation for observation in observations if observation.cam.cam_name == "cam3"
    )
    assert deleted_observation.is_deleted is True
    assert deleted_observation.deleted_at is not None
    assert deleted_observation.deletion_reason == "missing_from_import"
    assert active_observation.is_deleted is False
    assert active_observation.deletion_reason is None

    event_response = client.get(f"/api/events/{active_observation.event_id}")
    assert event_response.status_code == 200
    returned_cam_names = [
        item["observation_ref"]["cam_name"] for item in event_response.json()["observations"]
    ]
    assert "cam3" in returned_cam_names
    assert "cam4" not in returned_cam_names

    event_response_with_deleted = client.get(
        f"/api/events/{active_observation.event_id}?includeDeleted=true"
    )
    assert event_response_with_deleted.status_code == 200
    returned_cam_names = [
        item["observation_ref"]["cam_name"]
        for item in event_response_with_deleted.json()["observations"]
    ]
    assert "cam3" in returned_cam_names
    assert "cam4" in returned_cam_names


def test_eventload_accepts_suffix_in_event_folder_name(client, db_session, tmp_path_factory):
    base = tmp_path_factory.mktemp("event_data_suffix_tag")
    event_dir = base / "20230101" / "010101b"
    cam_dir = event_dir / "Gaustatoppen" / "cam3"
    cam_dir.mkdir(parents=True, exist_ok=True)

    Image.new("RGB", (800, 600), "white").save(event_dir / "image.jpg")
    (cam_dir / "event.txt").write_text(
        "\n".join(
            [
                "[trail]",
                "frames=2",
                "positions=100,200 110,210",
                "timestamps=1715550000.000 1715550000.040",
                "[video]",
                "start=2024-05-12 23:54:04.000 UTC",
                "[summary]",
                "latitude=59.8",
                "longitude=8.6",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()
    settings.data_directory = str(base)

    response = client.post(
        "/api/admin/event-imports",
        auth=("sys_admin", "secretpassword"),
        json={"date_from": "20230101", "date_to": "20230102"},
    )
    assert response.status_code == 200, response.text

    db_session.expire_all()
    event = db_session.scalars(select(Event)).one()
    assert event.datetimetag == "20230101010101b"
    assert event.date == datetime(2023, 1, 1, 1, 1, 1)

    detail_response = client.get("/api/events/by-path/20230101/010101b")
    assert detail_response.status_code == 200, detail_response.text
    payload = detail_response.json()
    assert payload["datetimetag"] == "20230101010101b"
    assert payload["event_path"] == "20230101/010101b"
