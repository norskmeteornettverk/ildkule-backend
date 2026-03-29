from datetime import datetime

from fastapi_app.app.models import Cam, Event, ObservationCamData, Station
from fastapi_app.app.utils import serialization


def test_event_media_uses_local_data_urls_by_default(monkeypatch):
    monkeypatch.setattr(
        serialization.settings, "event_media_source_mode", "local", raising=False
    )
    monkeypatch.setattr(
        serialization.settings, "event_media_base_url", None, raising=False
    )
    monkeypatch.setattr(serialization.settings, "front_url", None, raising=False)

    media = serialization._event_media("20260128232821")

    assert media["thumbnail_url"] == "/data/20260128/232821/thumbnail.jpg"
    assert media["map_image_url"] == "/data/20260128/232821/map.jpg"


def test_event_media_uses_remote_published_paths_when_configured(monkeypatch):
    monkeypatch.setattr(
        serialization.settings, "event_media_source_mode", "remote", raising=False
    )
    monkeypatch.setattr(
        serialization.settings,
        "event_media_base_url",
        "https://norskmeteornettverk.no/meteor",
        raising=False,
    )
    monkeypatch.setattr(serialization.settings, "front_url", None, raising=False)

    event = Event(datetimetag="20260128232821", date=datetime(2026, 1, 28, 23, 28, 21))
    payload = serialization.serialize_event(event)
    media = serialization._event_media(event.datetimetag)

    assert payload["public_url"] == "https://norskmeteornettverk.no/meteor/20260128/232821/"
    assert payload["preview"]["thumbnail_url"] == "https://norskmeteornettverk.no/meteor/20260128/232821/thumbnail.jpg"
    assert media["map_image_url"] == "https://norskmeteornettverk.no/meteor/20260128/232821/en_map.jpg"
    assert media["orbit_svg_url"] == "https://norskmeteornettverk.no/meteor/20260128/232821/en_orbit.svg"
    assert media["report_text_url"] == "https://norskmeteornettverk.no/meteor/20260128/232821/obs_2026-01-28_23:28:21.txt"


def test_observation_media_uses_remote_base_without_local_data_directory(monkeypatch):
    monkeypatch.setattr(
        serialization.settings, "event_media_source_mode", "remote", raising=False
    )
    monkeypatch.setattr(
        serialization.settings,
        "event_media_base_url",
        "https://norskmeteornettverk.no/meteor",
        raising=False,
    )
    monkeypatch.setattr(serialization.settings, "data_directory", None, raising=False)

    event = Event(datetimetag="20260128232821")
    station = Station(station_name="larvik")
    cam = Cam(station=station, cam_name="cam1")
    observation = ObservationCamData(
        observation_key="larvik:cam1:2026-01-28T23:28:21.000",
        source_hash="hash-1",
        event=event,
        cam=cam,
        event_start_utc=datetime(2026, 1, 28, 23, 28, 21),
    )

    media = serialization._observation_media(observation)
    artifacts = serialization._observation_artifacts(observation)

    assert media is not None
    assert (
        media["raw_video_url"]
        == "https://norskmeteornettverk.no/meteor/20260128/232821/larvik/cam1/larvik-20260128232821.mp4"
    )
    assert any(
        artifact["role"] == "raw_video"
        and artifact["url"]
        == "https://norskmeteornettverk.no/meteor/20260128/232821/larvik/cam1/larvik-20260128232821.mp4"
        for artifact in artifacts
    )
