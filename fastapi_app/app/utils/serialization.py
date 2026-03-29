from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pathlib import PurePosixPath
from typing import Iterable, List, Optional
from zoneinfo import ZoneInfo

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
from .orbit_solver import build_orbit_payload, solve_event_orbit


settings = get_settings()
_ASTRONOMICAL_UNIT_KM = 149597870.7
_SOLAR_MU_KM_S2 = 1.32712440018e11
_EARTH_ORBIT_SAMPLE_SECONDS = 3600
_EARTH_OBLIQUITY_DEG = 23.439291


def _event_path(datetimetag: str) -> str:
    return f"{datetimetag[:8]}/{datetimetag[8:]}"


def _event_media_source_mode() -> str:
    raw_value = getattr(settings, "event_media_source_mode", "local")
    if not isinstance(raw_value, str):
        return "local"
    normalized = raw_value.strip().lower()
    return normalized if normalized in {"local", "remote"} else "local"


def _event_media_base_url() -> Optional[str]:
    raw_value = getattr(settings, "event_media_base_url", None)
    if isinstance(raw_value, str) and raw_value.strip():
        return raw_value.rstrip("/")
    return None


def _is_remote_media_mode() -> bool:
    return _event_media_source_mode() == "remote"


def _is_local_media_mode() -> bool:
    return not _is_remote_media_mode()


def _join_url(base_url: str, relative_path: str) -> str:
    return f"{base_url.rstrip('/')}/{relative_path.lstrip('/')}"


def _remote_event_asset_name(file_name: str) -> str:
    remote_names = {
        "map.jpg": "en_map.jpg",
        "map.svg": "en_map.svg",
        "posvstime.jpg": "en_posvstime.jpg",
        "posvstime.svg": "en_posvstime.svg",
        "spd_acc.jpg": "en_spd_acc.jpg",
        "spd_acc.svg": "en_spd_acc.svg",
        "orbit.jpg": "en_orbit.jpg",
        "orbit.svg": "en_orbit.svg",
        "height.jpg": "en_height.jpg",
        "height.svg": "en_height.svg",
    }
    if file_name.startswith("obs_"):
        stem, dot, suffix = file_name.rpartition(".")
        if stem.count("_") >= 3:
            prefix, hour, minute, second = stem.rsplit("_", 3)
            return f"{prefix}_{hour}:{minute}:{second}{dot}{suffix}"
    return remote_names.get(file_name, file_name)


def _remote_relative_path(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) < 3:
        return path
    event_root = "/".join(parts[:2])
    remainder = list(parts[2:])
    if len(remainder) == 1:
        return f"{event_root}/{_remote_event_asset_name(remainder[0])}"
    return path


def _public_media_base_url() -> str:
    configured_base_url = _event_media_base_url()
    if configured_base_url:
        return configured_base_url
    if _is_remote_media_mode() and settings.front_url:
        return f"{settings.front_url.rstrip('/')}/meteor"
    return "/data"


def _data_url(path: str) -> str:
    relative_path = _remote_relative_path(path) if _is_remote_media_mode() else path
    return _join_url(_public_media_base_url(), relative_path)


def _frontend_event_url(datetimetag: str) -> Optional[str]:
    if _is_remote_media_mode():
        return f"{_join_url(_public_media_base_url(), _event_path(datetimetag))}/"
    settings = get_settings()
    if not settings.front_url:
        return None
    base_url = settings.front_url.rstrip("/")
    return f"{base_url}/meteor/{datetimetag[:8]}/{datetimetag[8:]}/"


def _event_report_prefix(datetimetag: str) -> str:
    timestamp = datetime.strptime(datetimetag[:14], "%Y%m%d%H%M%S")
    return f"obs_{timestamp.strftime('%Y-%m-%d_%H_%M_%S')}"


def _observation_file_prefix(record: ObservationCamData) -> Optional[str]:
    if not record.cam or not record.cam.station or not record.event_start_utc:
        return None
    station_name = record.cam.station.station_name
    timestamp = record.event_start_utc.strftime("%Y%m%d%H%M%S")
    return f"{station_name}-{timestamp}"


def _event_type(camera_confirmed: Optional[int], track_endheight) -> str:
    if track_endheight is not None and track_endheight < settings.candidate_max_end_height_km:
        return "Meteorittkandidat"
    if camera_confirmed:
        return "Krysspeilet"
    return "Upeilet"


def _public_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.public_timezone)
    except Exception:
        return timezone(timedelta(hours=1), name=settings.public_timezone)


def _data_file_path(path: str) -> Optional[Path]:
    if not settings.data_directory:
        return None
    return Path(settings.data_directory) / path


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        (left[1] * right[2]) - (left[2] * right[1]),
        (left[2] * right[0]) - (left[0] * right[2]),
        (left[0] * right[1]) - (left[1] * right[0]),
    )


def _vector_length(vector: tuple[float, float, float]) -> float:
    return math.sqrt(_dot(vector, vector))


def _scale(vector: tuple[float, float, float], factor: float) -> tuple[float, float, float]:
    return tuple(component * factor for component in vector)


def _add(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(left, right))


def _subtract(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right))


def _normalize_angle_deg(angle_deg: float) -> float:
    normalized = angle_deg % 360.0
    if normalized < 0:
        normalized += 360.0
    return normalized


def _normalize_signed_angle_deg(angle_deg: float) -> float:
    normalized = _normalize_angle_deg(angle_deg)
    if normalized > 180.0:
        normalized -= 360.0
    return normalized


def _julian_day(value: datetime) -> float:
    utc_value = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    year = utc_value.year
    month = utc_value.month
    day_fraction = (
        utc_value.day
        + (utc_value.hour / 24.0)
        + (utc_value.minute / 1440.0)
        + (utc_value.second / 86400.0)
        + (utc_value.microsecond / 86400000000.0)
    )

    if month <= 2:
        year -= 1
        month += 12

    century = year // 100
    correction = 2 - century + (century // 4)

    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day_fraction
        + correction
        - 1524.5
    )


def _earth_heliocentric_position_au(value: datetime) -> tuple[float, float, float]:
    days_since_j2000 = _julian_day(value) - 2451545.0
    mean_anomaly_deg = _normalize_angle_deg(357.52910 + (0.98560028 * days_since_j2000))
    mean_longitude_deg = _normalize_angle_deg(280.46645 + (0.98564736 * days_since_j2000))
    mean_anomaly = math.radians(mean_anomaly_deg)

    ecliptic_longitude_deg = _normalize_angle_deg(
        mean_longitude_deg
        + (1.9148 * math.sin(mean_anomaly))
        + (0.0200 * math.sin(2 * mean_anomaly))
        + (0.0003 * math.sin(3 * mean_anomaly))
    )
    radius_au = (
        1.00014
        - (0.01671 * math.cos(mean_anomaly))
        - (0.00014 * math.cos(2 * mean_anomaly))
    )
    ecliptic_longitude = math.radians(ecliptic_longitude_deg)

    return (
        -radius_au * math.cos(ecliptic_longitude),
        -radius_au * math.sin(ecliptic_longitude),
        0.0,
    )


def _earth_heliocentric_velocity_kms(value: datetime) -> tuple[float, float, float]:
    delta = timedelta(seconds=_EARTH_ORBIT_SAMPLE_SECONDS)
    before = _earth_heliocentric_position_au(value - delta)
    after = _earth_heliocentric_position_au(value + delta)
    derivative_au_per_second = _scale(
        _subtract(after, before),
        1.0 / (2.0 * _EARTH_ORBIT_SAMPLE_SECONDS),
    )
    return _scale(derivative_au_per_second, _ASTRONOMICAL_UNIT_KM)


def _ecliptic_radiant(event: Event) -> Optional[tuple[float, float]]:
    if event.radiant_ecl_long is not None and event.radiant_ecl_lat is not None:
        return (event.radiant_ecl_long, event.radiant_ecl_lat)
    if event.radiant_ra is None or event.radiant_dec is None:
        return None

    obliquity = math.radians(_EARTH_OBLIQUITY_DEG)
    right_ascension = math.radians(event.radiant_ra)
    declination = math.radians(event.radiant_dec)

    ecliptic_longitude = math.atan2(
        (math.sin(right_ascension) * math.cos(obliquity))
        + (math.tan(declination) * math.sin(obliquity)),
        math.cos(right_ascension),
    )
    ecliptic_latitude = math.asin(
        (math.sin(declination) * math.cos(obliquity))
        - (math.cos(declination) * math.sin(obliquity) * math.sin(right_ascension))
    )
    return (
        _normalize_angle_deg(math.degrees(ecliptic_longitude)),
        math.degrees(ecliptic_latitude),
    )


def _fallback_orbit_payload(event: Event) -> dict:
    if event.track_speed is None or event.date is None:
        return {
            "perihelion_distance_au": None,
            "eccentricity": None,
            "inclination_deg": None,
            "ascending_node_deg": None,
            "argument_of_perihelion_deg": None,
            "mean_anomaly_deg": None,
            "epoch": None,
        }

    radiant = _ecliptic_radiant(event)
    if radiant is None:
        return {
            "perihelion_distance_au": None,
            "eccentricity": None,
            "inclination_deg": None,
            "ascending_node_deg": None,
            "argument_of_perihelion_deg": None,
            "mean_anomaly_deg": None,
            "epoch": None,
        }

    radiant_longitude = math.radians(radiant[0])
    radiant_latitude = math.radians(radiant[1])
    radiant_unit = (
        math.cos(radiant_latitude) * math.cos(radiant_longitude),
        math.cos(radiant_latitude) * math.sin(radiant_longitude),
        math.sin(radiant_latitude),
    )

    geocentric_velocity = _scale(radiant_unit, -float(event.track_speed))
    heliocentric_velocity = _add(
        _earth_heliocentric_velocity_kms(event.date),
        geocentric_velocity,
    )
    position_au = _earth_heliocentric_position_au(event.date)
    position_km = _scale(position_au, _ASTRONOMICAL_UNIT_KM)

    radius_km = _vector_length(position_km)
    speed_kms = _vector_length(heliocentric_velocity)
    if radius_km == 0 or speed_kms == 0:
        return {
            "perihelion_distance_au": None,
            "eccentricity": None,
            "inclination_deg": None,
            "ascending_node_deg": None,
            "argument_of_perihelion_deg": None,
            "mean_anomaly_deg": None,
            "epoch": None,
        }

    angular_momentum = _cross(position_km, heliocentric_velocity)
    angular_momentum_norm = _vector_length(angular_momentum)
    if angular_momentum_norm == 0:
        return {
            "perihelion_distance_au": None,
            "eccentricity": None,
            "inclination_deg": None,
            "ascending_node_deg": None,
            "argument_of_perihelion_deg": None,
            "mean_anomaly_deg": None,
            "epoch": None,
        }

    eccentricity_vector = _subtract(
        _scale(_cross(heliocentric_velocity, angular_momentum), 1.0 / _SOLAR_MU_KM_S2),
        _scale(position_km, 1.0 / radius_km),
    )
    eccentricity = _vector_length(eccentricity_vector)
    node_vector = _cross((0.0, 0.0, 1.0), angular_momentum)
    node_norm = _vector_length(node_vector)

    inclination_deg = math.degrees(
        math.acos(max(-1.0, min(1.0, angular_momentum[2] / angular_momentum_norm)))
    )
    ascending_node_deg = (
        _normalize_angle_deg(math.degrees(math.atan2(node_vector[1], node_vector[0])))
        if node_norm > 0
        else 0.0
    )

    if node_norm > 0 and eccentricity > 1e-9:
        argument_of_perihelion_deg = _normalize_angle_deg(
            math.degrees(
                math.atan2(
                    _dot(_cross(node_vector, eccentricity_vector), angular_momentum)
                    / (node_norm * angular_momentum_norm),
                    _dot(node_vector, eccentricity_vector) / node_norm,
                )
            )
        )
    else:
        argument_of_perihelion_deg = 0.0

    specific_energy = (speed_kms * speed_kms / 2.0) - (_SOLAR_MU_KM_S2 / radius_km)
    if abs(1.0 - eccentricity) < 1e-6 or specific_energy == 0:
        return {
            "perihelion_distance_au": round((angular_momentum_norm**2 / _SOLAR_MU_KM_S2) / (1.0 + eccentricity) / _ASTRONOMICAL_UNIT_KM, 6),
            "eccentricity": round(eccentricity, 6),
            "inclination_deg": round(inclination_deg, 3),
            "ascending_node_deg": round(ascending_node_deg, 3),
            "argument_of_perihelion_deg": round(argument_of_perihelion_deg, 3),
            "mean_anomaly_deg": None,
            "epoch": event.date.replace(tzinfo=timezone.utc).isoformat() if event.date.tzinfo is None else event.date.astimezone(timezone.utc).isoformat(),
        }

    perihelion_distance_au = (
        (angular_momentum_norm * angular_momentum_norm) / _SOLAR_MU_KM_S2 / (1.0 + eccentricity)
    ) / _ASTRONOMICAL_UNIT_KM

    true_anomaly = math.atan2(
        _dot(_cross(eccentricity_vector, position_km), angular_momentum)
        / (angular_momentum_norm * max(eccentricity, 1e-9)),
        _dot(eccentricity_vector, position_km) / (max(eccentricity, 1e-9) * radius_km),
    )

    mean_anomaly_deg = None
    if eccentricity < 1.0:
        eccentric_anomaly = 2.0 * math.atan2(
            math.sqrt(1.0 - eccentricity) * math.sin(true_anomaly / 2.0),
            math.sqrt(1.0 + eccentricity) * math.cos(true_anomaly / 2.0),
        )
        mean_anomaly_deg = _normalize_angle_deg(
            math.degrees(eccentric_anomaly - (eccentricity * math.sin(eccentric_anomaly)))
        )
    elif eccentricity > 1.0:
        hyperbolic_factor = math.sqrt((eccentricity - 1.0) / (eccentricity + 1.0))
        hyperbolic_argument = hyperbolic_factor * math.tan(true_anomaly / 2.0)
        hyperbolic_argument = max(-0.999999, min(0.999999, hyperbolic_argument))
        hyperbolic_anomaly = 2.0 * math.atanh(hyperbolic_argument)
        mean_anomaly_deg = math.degrees(
            (eccentricity * math.sinh(hyperbolic_anomaly)) - hyperbolic_anomaly
        )

    epoch_value = event.date.astimezone(timezone.utc) if event.date.tzinfo else event.date.replace(tzinfo=timezone.utc)

    return {
        "perihelion_distance_au": round(perihelion_distance_au, 6),
        "eccentricity": round(eccentricity, 6),
        "inclination_deg": round(inclination_deg, 3),
        "ascending_node_deg": round(ascending_node_deg, 3),
        "argument_of_perihelion_deg": round(argument_of_perihelion_deg, 3),
        "mean_anomaly_deg": round(mean_anomaly_deg, 3) if mean_anomaly_deg is not None else None,
        "epoch": epoch_value.isoformat(),
    }


def _orbit_payload(
    event: Event,
    observations: Optional[Iterable[ObservationCamData]] = None,
) -> dict:
    return build_orbit_payload(event, observations or [], fallback_factory=solve_event_orbit)


def _artifact(
    *,
    artifact_id: str,
    role: str,
    artifact_type: str,
    level: str,
    path: str,
    language: Optional[str] = None,
    interactive: bool = False,
    primary_action: str = "open",
    downloadable: bool = True,
    visibility: str = "public",
    observation_ref: Optional[str] = None,
    require_existing: bool = False,
) -> Optional[dict]:
    full_path = _data_file_path(path)
    if (
        require_existing
        and _is_local_media_mode()
        and full_path is not None
        and not full_path.exists()
    ):
        return None
    return {
        "id": artifact_id,
        "role": role,
        "type": artifact_type,
        "level": level,
        "language": language,
        "url": _data_url(path),
        "interactive": interactive,
        "primary_action": primary_action,
        "downloadable": downloadable,
        "visibility": visibility,
        "observation_ref": observation_ref,
    }


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


def _event_artifacts(datetimetag: str) -> List[dict]:
    event_path = _event_path(datetimetag)
    report_prefix = _event_report_prefix(datetimetag)
    artifacts = [
        _artifact(
            artifact_id=f"{datetimetag}:thumbnail",
            role="preview_thumbnail",
            artifact_type="image",
            level="event",
            path=f"{event_path}/thumbnail.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:image",
            role="event_preview",
            artifact_type="image",
            level="event",
            path=f"{event_path}/image.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:map",
            role="trajectory_map",
            artifact_type="image",
            level="event",
            path=f"{event_path}/map.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:height",
            role="height_profile",
            artifact_type="image",
            level="event",
            path=f"{event_path}/height.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:speed",
            role="speed_acceleration",
            artifact_type="image",
            level="event",
            path=f"{event_path}/spd_acc.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:position_time",
            role="position_vs_time",
            artifact_type="image",
            level="event",
            path=f"{event_path}/posvstime.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:orbit",
            role="heliocentric_orbit",
            artifact_type="image",
            level="event",
            path=f"{event_path}/orbit.jpg",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:kml",
            role="kml",
            artifact_type="text",
            level="event",
            path=f"{event_path}/{report_prefix}.kml",
            primary_action="download",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:report",
            role="dynamic_analysis_report",
            artifact_type="text",
            level="event",
            path=f"{event_path}/{report_prefix}.txt",
            primary_action="download",
        ),
        _artifact(
            artifact_id=f"{datetimetag}:stations_html",
            role="station_analysis",
            artifact_type="interactive",
            level="event",
            path=f"{event_path}/stations.html",
            interactive=True,
        ),
        _artifact(
            artifact_id=f"{datetimetag}:tables_html",
            role="analysis_tables",
            artifact_type="interactive",
            level="event",
            path=f"{event_path}/tables.html",
            interactive=True,
        ),
    ]
    return [artifact for artifact in artifacts if artifact is not None]


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


def _observation_artifacts(record: ObservationCamData) -> List[dict]:
    if not record.cam or not record.cam.station or not record.event:
        return []
    prefix = _observation_file_prefix(record)
    if not prefix:
        return []
    base_path = (
        f"{_event_path(record.event.datetimetag)}/"
        f"{record.cam.station.station_name}/{record.cam.cam_name}"
    )
    observation_ref = record.observation_key
    artifacts = [
        _artifact(
            artifact_id=f"{observation_ref}:preview",
            role="observation_preview",
            artifact_type="image",
            level="observation",
            path=f"{base_path}/fireball.jpg",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:raw_image",
            role="raw_image",
            artifact_type="image",
            level="observation",
            path=f"{base_path}/{prefix}.jpg",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:raw_video",
            role="raw_video",
            artifact_type="video",
            level="observation",
            path=f"{base_path}/{prefix}.mp4",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:gnomonic_image",
            role="processed_image",
            artifact_type="image",
            level="observation",
            path=f"{base_path}/{prefix}-gnomonic.jpg",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:gnomonic_video",
            role="processed_video",
            artifact_type="video",
            level="observation",
            path=f"{base_path}/{prefix}-gnomonic.mp4",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:brightness",
            role="brightness_graph",
            artifact_type="image",
            level="observation",
            path=f"{base_path}/brightness.jpg",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:frame_brightness",
            role="frame_brightness_graph",
            artifact_type="image",
            level="observation",
            path=f"{base_path}/fbrightness.jpg",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:size",
            role="size_graph",
            artifact_type="image",
            level="observation",
            path=f"{base_path}/size.jpg",
            observation_ref=observation_ref,
        ),
        _artifact(
            artifact_id=f"{observation_ref}:event_text",
            role="observation_text",
            artifact_type="text",
            level="observation",
            path=f"{base_path}/event.txt",
            primary_action="download",
            observation_ref=observation_ref,
        ),
    ]
    return [artifact for artifact in artifacts if artifact is not None]


def _final_classification(user_confirmed: Optional[int]) -> str:
    if user_confirmed == 1:
        return "Meteor"
    if user_confirmed == 0:
        return "Ikke meteor"
    return "Usikker"


def _candidate_payload(event: Event) -> dict:
    threshold_end = settings.candidate_max_end_height_km
    threshold_speed = settings.candidate_max_speed_kms
    end_height = event.track_endheight
    speed = event.track_speed
    is_candidate = bool(
        end_height is not None
        and end_height <= threshold_end
        and (speed is None or speed <= threshold_speed)
    )
    return {
        "is_candidate": is_candidate,
        "max_end_height_km": threshold_end,
        "max_speed_kms": threshold_speed,
    }


def _times_payload(dt: Optional[datetime]) -> dict:
    if dt is None:
        return {"utc": None, "local": None, "timezone": settings.public_timezone}
    utc_dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(_public_timezone())
    return {
        "utc": utc_dt.isoformat(),
        "local": local_dt.isoformat(),
        "timezone": settings.public_timezone,
    }


def _observation_identity(record: ObservationCamData) -> dict:
    station_name = None
    cam_name = None
    if record.cam:
        cam_name = record.cam.cam_name
        if record.cam.station:
            station_name = record.cam.station.station_name
    return {
        "id": record.id,
        "observation_key": record.observation_key,
        "station_name": station_name,
        "cam_name": cam_name,
        "event_start_utc": record.event_start_utc.isoformat() if record.event_start_utc else None,
    }


def _preview_payload(event: Event, artifacts: List[dict]) -> dict:
    preview_artifact = next((artifact for artifact in artifacts if artifact["role"] == "preview_thumbnail"), None)
    main_artifact = next((artifact for artifact in artifacts if artifact["role"] == "event_preview"), None)
    return {
        "type": "image" if preview_artifact or main_artifact else None,
        "thumbnail_url": preview_artifact["url"] if preview_artifact else None,
        "image_url": main_artifact["url"] if main_artifact else None,
        "has_preview": bool(preview_artifact or main_artifact),
    }


def _event_title(event: Event) -> str:
    base = _event_type(event.camera_confirmed, event.track_endheight)
    if event.location:
        return f"{base} over {event.location}"
    if event.date:
        return f"{base} {event.date.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    return base


def _station_summary(observations: List[ObservationCamData]) -> dict:
    station_names: List[str] = []
    camera_labels: List[str] = []
    for record in observations:
        if not record.cam:
            continue
        if record.cam.station and record.cam.station.station_name:
            station_names.append(record.cam.station.station_name)
        if record.cam.station and record.cam.station.station_name and record.cam.cam_name:
            camera_labels.append(f"{record.cam.station.station_name}/{record.cam.cam_name}")
        elif record.cam.cam_name:
            camera_labels.append(record.cam.cam_name)

    station_names = sorted(set(station_names))
    camera_labels = sorted(set(camera_labels))
    return {
        "station_count": len(station_names),
        "observation_count": len(observations),
        "stations": station_names,
        "cameras": camera_labels,
        "label": ", ".join(camera_labels[:3]) if camera_labels else None,
    }


def _technical_validity(event: Event) -> dict:
    proper_triangulation = None
    if (
        event.track_speed is not None
        and event.track_endheight is not None
        and event.track_startheight is not None
    ):
        proper_triangulation = bool(
            event.track_speed > 0
            and event.track_speed < 1000
            and event.track_endheight > 0
            and event.track_startheight > 0
            and event.track_startheight < 1000
            and event.track_startheight > event.track_endheight
        )
    return {
        "is_valid": event.is_deleted is False and event.user_confirmed != 0,
        "is_deleted": bool(event.is_deleted),
        "source_bad_detection": None,
        "proper_triangulation": proper_triangulation,
    }


def _analysis_payload(event: Event, observations: List[ObservationCamData], event_artifacts: List[dict]) -> dict:
    station_points = []
    for record in observations:
        station_name = record.cam.station.station_name if record.cam and record.cam.station else None
        station_points.append(
            {
                "observation_key": record.observation_key,
                "station_name": station_name,
                "cam_name": record.cam.cam_name if record.cam else None,
                "station_lat": record.summary_latitude,
                "station_lng": record.summary_longitude,
                "station_elevation_m": record.summary_elevation,
                "start_lat": None,
                "start_lng": None,
                "end_lat": None,
                "end_lng": None,
            }
        )

    geometry_points = None
    if (
        event.track_startlat is not None
        and event.track_startlong is not None
        and event.track_startheight is not None
        and event.track_endlat is not None
        and event.track_endlong is not None
        and event.track_endheight is not None
    ):
        sample_steps = 16
        geometry_points = []
        for step_index in range(sample_steps + 1):
            fraction = step_index / sample_steps
            geometry_points.append(
                {
                    "step_index": step_index,
                    "fraction": fraction,
                    "lat": event.track_startlat
                    + ((event.track_endlat - event.track_startlat) * fraction),
                    "lng": event.track_startlong
                    + ((event.track_endlong - event.track_startlong) * fraction),
                    "height_km": event.track_startheight
                    + ((event.track_endheight - event.track_startheight) * fraction),
                }
            )

    return {
        "atmospheric_path": {
            "start_height_km": event.track_startheight,
            "end_height_km": event.track_endheight,
            "start_lat": event.track_startlat,
            "start_lng": event.track_startlong,
            "end_lat": event.track_endlat,
            "end_lng": event.track_endlong,
            "course_deg": event.track_course,
            "incidence_deg": event.track_incidence,
            "speed_kms": event.track_speed,
            "speed_source": event.track_speed_source,
            "geometry_points": geometry_points,
            "station_points": station_points,
        },
        "radiant": {
            "ra": event.radiant_ra,
            "dec": event.radiant_dec,
            "shower": event.radiant_shower,
            "zenith_attractor": event.radiant_zenith_attractor,
        },
        "orbit": _orbit_payload(event, observations),
        "artifacts": event_artifacts,
    }


def _ai_score(observations: List[ObservationCamData]) -> Optional[float]:
    scores = [
        float(record.summary_meteor_probability)
        for record in observations
        if record.summary_meteor_probability is not None
    ]
    if not scores:
        return None
    return max(scores)


def _prune_observation_public_payload(payload: dict) -> dict:
    for key in (
        "cam",
        "media",
        "gnomonic_video_url",
        "fireball_image_url",
        "source_hash",
        "cam_id",
        "event_id",
        "trail_centroid",
        "trail_centroid2",
    ):
        payload.pop(key, None)
    return payload


def _prune_event_public_payload(payload: dict) -> dict:
    for key in (
        "camera_confirmed",
        "user_confirmed",
        "media",
        "thumbnail_url",
        "image_url",
        "observation_cam_data",
        "user_review",
    ):
        payload.pop(key, None)
    return payload


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
    payload["identifier"] = user.username
    payload.pop("username", None)
    payload["tutorial_completed"] = bool(payload.get("tutorial_completed"))
    payload["account_confirmed"] = bool(payload.get("confirmed"))
    payload.pop("confirmed", None)
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
    payload["has_ams_coords"] = bool(getattr(record, "trail_ams_coords", None))
    if record.cam:
        payload["cam"] = serialize_cam(record.cam)
    media = _observation_media(record)
    if media:
        payload["media"] = media
        payload["gnomonic_video_url"] = media["gnomonic_video_url"]
        payload["fireball_image_url"] = media["fireball_image_url"]
    artifacts = _observation_artifacts(record)
    payload["observation_ref"] = _observation_identity(record)
    payload["artifacts"] = artifacts
    payload["preview"] = {
        "thumbnail_url": media["fireball_image_url"] if media else None,
        "open_url": media["raw_video_url"] if media else None,
        "type": "video" if media and media.get("raw_video_url") else "image",
    }
    return _prune_observation_public_payload(payload)


def serialize_res_entry(entry: EventResEntry) -> dict:
    return model_to_dict(entry)


def serialize_trail_point(point: ObservationTrailPoint) -> dict:
    payload = model_to_dict(point)
    payload["event_timestamp"] = point.event_timestamp
    return payload


def serialize_event(
    event: Event,
    include_relationships: bool = False,
    include_deleted: bool = False,
) -> dict:
    payload = model_to_dict(event)
    observations = []
    if include_relationships:
        observations = event.observation_data or []
        if not include_deleted:
            observations = [record for record in observations if not record.is_deleted]
    event_artifacts = _event_artifacts(event.datetimetag)
    station_summary = _station_summary(observations)
    times = _times_payload(event.date)
    candidate = _candidate_payload(event)
    payload["event_type"] = _event_type(event.camera_confirmed, event.track_endheight)
    payload["cross_station_confirmed"] = bool(event.camera_confirmed)
    payload["event_path"] = _event_path(event.datetimetag)
    payload["public_url"] = _frontend_event_url(event.datetimetag)
    payload["media"] = _event_media(event.datetimetag)
    payload["thumbnail_url"] = payload["media"]["thumbnail_url"]
    payload["image_url"] = payload["media"]["image_url"]
    payload["event_artifacts"] = event_artifacts
    payload["preview"] = _preview_payload(event, event_artifacts)
    payload["candidate"] = candidate
    payload["final_classification"] = _final_classification(event.user_confirmed)
    payload["times"] = times
    payload["title"] = _event_title(event)
    payload["title_basis"] = {
        "event_type": payload["event_type"],
        "location": event.location,
        "cross_station_confirmed": payload["cross_station_confirmed"],
    }
    payload["station_summary"] = station_summary
    payload["station_count"] = station_summary["station_count"]
    payload["observation_count"] = station_summary["observation_count"]
    payload["shower"] = event.radiant_shower
    payload["ai_score"] = _ai_score(observations)
    payload["technical_validity"] = _technical_validity(event)
    payload["header"] = {
        "id": event.id,
        "event_path": payload["event_path"],
        "title": payload["title"],
        "location": event.location,
        "times": times,
        "cross_station_confirmed": payload["cross_station_confirmed"],
    }
    payload["summary_basis"] = {
        "location": event.location,
        "station_summary": station_summary,
        "shower": event.radiant_shower,
        "candidate": candidate,
    }
    payload["classification"] = {
        "final_classification": payload["final_classification"],
        "cross_station_confirmed": payload["cross_station_confirmed"],
        "user_confirmed": event.user_confirmed,
    }
    res_entries_state = inspect(event).attrs.res_entries.loaded_value
    if res_entries_state is not NO_VALUE:
        payload["res_entry_count"] = len(res_entries_state or [])
        payload["analysis"] = _analysis_payload(event, observations, event_artifacts)
    if include_relationships:
        payload["observation_cam_data"] = [
            serialize_observation(record) for record in observations
        ]
        payload["observations"] = payload["observation_cam_data"]
        payload["user_review"] = [
            serialize_review(review) for review in event.reviews or []
        ]
    else:
        payload["analysis"] = _analysis_payload(event, observations, event_artifacts)
    return _prune_event_public_payload(payload)


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
