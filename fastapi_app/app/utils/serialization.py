from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE

from ..config import get_settings
from ..models import (
    Cam,
    Event,
    EventResEntry,
    ObservationCamData,
    ObservationTrailPoint,
    Station,
    User,
    UserReview,
)


def _event_path(datetimetag: str) -> str:
    return f"{datetimetag[:8]}/{datetimetag[8:]}"


def _data_url(path: str) -> str:
    return f"/data/{path}"


def _frontend_event_url(datetimetag: str) -> Optional[str]:
    settings = get_settings()
    if not settings.front_url:
        return None
    base_url = settings.front_url.rstrip("/")
    return f"{base_url}/meteor/{datetimetag[:8]}/{datetimetag[8:]}/"


def _event_report_prefix(datetimetag: str) -> str:
    timestamp = datetime.strptime(datetimetag, "%Y%m%d%H%M%S")
    return f"obs_{timestamp.strftime('%Y-%m-%d_%H_%M_%S')}"


def _observation_file_prefix(record: ObservationCamData) -> Optional[str]:
    if not record.cam or not record.cam.station or not record.event_start_utc:
        return None
    station_name = record.cam.station.station_name
    timestamp = record.event_start_utc.strftime("%Y%m%d%H%M%S")
    return f"{station_name}-{timestamp}"


def _event_type(camera_confirmed: Optional[int], track_endheight) -> str:
    if track_endheight is not None and track_endheight < 40:
        return "Meteorittkandidat"
    if camera_confirmed:
        return "Krysspeilet"
    return "Upeilet"


def _event_media(datetimetag: str) -> dict:
    event_path = _event_path(datetimetag)
    report_prefix = _event_report_prefix(datetimetag)
    return {
        "thumbnail_url": _data_url(f"{event_path}/thumbnail.jpg"),
        "image_url": _data_url(f"{event_path}/image.jpg"),
        "map_image_url": _data_url(f"{event_path}/map.jpg"),
        "map_svg_url": _data_url(f"{event_path}/map.svg"),
        "position_vs_time_image_url": _data_url(f"{event_path}/posvstime.jpg"),
        "position_vs_time_svg_url": _data_url(f"{event_path}/posvstime.svg"),
        "speed_acceleration_image_url": _data_url(f"{event_path}/spd_acc.jpg"),
        "speed_acceleration_svg_url": _data_url(f"{event_path}/spd_acc.svg"),
        "orbit_image_url": _data_url(f"{event_path}/orbit.jpg"),
        "orbit_svg_url": _data_url(f"{event_path}/orbit.svg"),
        "height_image_url": _data_url(f"{event_path}/height.jpg"),
        "height_svg_url": _data_url(f"{event_path}/height.svg"),
        "report_text_url": _data_url(f"{event_path}/{report_prefix}.txt"),
        "kml_url": _data_url(f"{event_path}/{report_prefix}.kml"),
        "stations_html_url": _data_url(f"{event_path}/stations.html"),
        "tables_html_url": _data_url(f"{event_path}/tables.html"),
    }


def _observation_media(record: ObservationCamData) -> Optional[dict]:
    if not record.cam or not record.cam.station or not record.event:
        return None
    prefix = _observation_file_prefix(record)
    if not prefix:
        return None
    base_path = (
        f"{_event_path(record.event.datetimetag)}/"
        f"{record.cam.station.station_name}/{record.cam.cam_name}"
    )
    return {
        "fireball_image_url": _data_url(f"{base_path}/fireball.jpg"),
        "raw_image_url": _data_url(f"{base_path}/{prefix}.jpg"),
        "raw_video_url": _data_url(f"{base_path}/{prefix}.mp4"),
        "gnomonic_image_url": _data_url(f"{base_path}/{prefix}-gnomonic.jpg"),
        "gnomonic_video_url": _data_url(f"{base_path}/{prefix}-gnomonic.mp4"),
        "brightness_image_url": _data_url(f"{base_path}/brightness.jpg"),
        "frame_brightness_image_url": _data_url(f"{base_path}/fbrightness.jpg"),
        "size_image_url": _data_url(f"{base_path}/size.jpg"),
        "event_text_url": _data_url(f"{base_path}/event.txt"),
    }


def model_to_dict(instance, exclude: Optional[set[str]] = None) -> dict:
    if instance is None:
        return {}
    exclude = exclude or set()
    mapper = inspect(instance).mapper.column_attrs
    payload = {}
    for column in mapper:
        key = column.key
        if key in exclude:
            continue
        payload[key] = getattr(instance, key)
    return payload


def serialize_user(user: User, ratings: Optional[dict] = None) -> dict:
    payload = model_to_dict(
        user, exclude={"password", "confirm_token", "password_reset_token"}
    )
    payload["user_role"] = payload.get("role")
    payload["roles"] = [payload.get("role")]
    payload["id"] = user.id
    payload["username"] = user.username
    payload["tutorial_completed"] = bool(payload.get("tutorial_completed"))
    payload["confirmed"] = bool(payload.get("confirmed"))
    payload["user_level"] = payload.get("user_level")
    if ratings:
        payload.update(ratings)
    return payload


def serialize_review(review: UserReview) -> dict:
    return model_to_dict(review)


def serialize_cam(cam: Cam) -> dict:
    payload = model_to_dict(cam)
    if cam.station:
        payload["station"] = model_to_dict(cam.station)
    return payload


def serialize_observation(record: ObservationCamData) -> dict:
    payload = model_to_dict(record)
    trail_points_state = inspect(record).attrs.trail_points.loaded_value
    if trail_points_state is not NO_VALUE:
        payload["trail_point_count"] = len(trail_points_state or [])
    if record.cam:
        payload["cam"] = serialize_cam(record.cam)
    media = _observation_media(record)
    if media:
        payload["media"] = media
        payload["gnomonic_video_url"] = media["gnomonic_video_url"]
        payload["fireball_image_url"] = media["fireball_image_url"]
    return payload


def serialize_res_entry(entry: EventResEntry) -> dict:
    return model_to_dict(entry)


def serialize_trail_point(point: ObservationTrailPoint) -> dict:
    return model_to_dict(point)


def serialize_event(
    event: Event,
    include_relationships: bool = False,
    include_deleted: bool = False,
) -> dict:
    payload = model_to_dict(event)
    payload["event_type"] = _event_type(event.camera_confirmed, event.track_endheight)
    payload["cross_station_confirmed"] = bool(event.camera_confirmed)
    payload["event_path"] = _event_path(event.datetimetag)
    payload["public_url"] = _frontend_event_url(event.datetimetag)
    payload["media"] = _event_media(event.datetimetag)
    payload["thumbnail_url"] = payload["media"]["thumbnail_url"]
    payload["image_url"] = payload["media"]["image_url"]
    res_entries_state = inspect(event).attrs.res_entries.loaded_value
    if res_entries_state is not NO_VALUE:
        payload["res_entry_count"] = len(res_entries_state or [])
    if include_relationships:
        observations = event.observation_data or []
        if not include_deleted:
            observations = [record for record in observations if not record.is_deleted]
        payload["observation_cam_data"] = [
            serialize_observation(record) for record in observations
        ]
        payload["user_review"] = [
            serialize_review(review) for review in event.reviews or []
        ]
    return payload


def serialize_event_list(
    events: Iterable[Event],
    include_relationships: bool = False,
    include_deleted: bool = False,
) -> List[dict]:
    return [
        serialize_event(
            event,
            include_relationships=include_relationships,
            include_deleted=include_deleted,
        )
        for event in events
    ]
