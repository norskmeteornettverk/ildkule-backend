from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Optional, Sequence

import numpy as np
from astropy import units as u
from astropy.coordinates import (
    CartesianRepresentation,
    EarthLocation,
    GCRS,
    ITRS,
    SkyCoord,
    get_body_barycentric_posvel,
    solar_system_ephemeris,
)
from astropy.time import Time
from astropy.utils import iers

from ..models import Event, ObservationCamData, ObservationTrailPoint

iers.conf.auto_download = False

_ASTRONOMICAL_UNIT_KM = 149597870.7
_SOLAR_MU_KM_S2 = 1.32712440018e11
_EARTH_MU_KM_S2 = 398600.4418
_EARTH_ORBIT_SAMPLE_SECONDS = 3600
_EARTH_OBLIQUITY_DEG = 23.439291
_MIN_TRACKS = 2
_MIN_FIT_POINTS = 4
_MIN_ORBIT_SPEED_KMS = 5.0
_MAX_ORBIT_SPEED_KMS = 100.0
_MAX_OBSERVED_MEAN_ANOMALY_DELTA_DEG = 15.0
_MAX_OBSERVED_MEDIAN_RESIDUAL_KM = 0.3
_MAX_OBSERVED_MAX_RESIDUAL_KM = 0.8
_MAX_STABLE_Q_DELTA_AU = 0.01
_MAX_STABLE_ECCENTRICITY_DELTA = 0.12
_MAX_STABLE_INCLINATION_DELTA_DEG = 3.0
_MAX_STABLE_NODE_DELTA_DEG = 2.0
_MAX_STABLE_ARGUMENT_DELTA_DEG = 4.0


@dataclass(frozen=True)
class _TrackPoint:
    timestamp: float
    los_ecef: np.ndarray


@dataclass(frozen=True)
class _ObservationTrack:
    site_ecef: np.ndarray
    points: Sequence[_TrackPoint]


@dataclass(frozen=True)
class _PathFitDiagnostics:
    track_count: int
    fit_point_count: int
    median_residual_km: float
    max_residual_km: float


@dataclass(frozen=True)
class _ObservationOrbitCandidate:
    payload: dict
    diagnostics: Optional[_PathFitDiagnostics]


def _utc_datetime(value: datetime | float) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _normalize_angle_deg(angle_deg: float) -> float:
    normalized = angle_deg % 360.0
    if normalized < 0:
        normalized += 360.0
    return normalized


def _dot(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.dot(left, right))


def _cross(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.cross(left, right)


def _vector_length(vector: np.ndarray) -> float:
    return float(np.linalg.norm(vector))


def _unit(vector: np.ndarray) -> Optional[np.ndarray]:
    norm = _vector_length(vector)
    if norm == 0:
        return None
    return vector / norm


def _empty_orbit_payload() -> dict:
    return {
        "perihelion_distance_au": None,
        "eccentricity": None,
        "inclination_deg": None,
        "ascending_node_deg": None,
        "argument_of_perihelion_deg": None,
        "mean_anomaly_deg": None,
        "epoch": None,
    }


def _wrapped_angle_delta(left: float, right: float) -> float:
    delta = abs((left - right) % 360.0)
    return min(delta, 360.0 - delta)


def _equatorial_to_ecliptic(vector: np.ndarray) -> np.ndarray:
    obliquity = math.radians(_EARTH_OBLIQUITY_DEG)
    rotation = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(obliquity), math.sin(obliquity)],
            [0.0, -math.sin(obliquity), math.cos(obliquity)],
        ],
        dtype=float,
    )
    return rotation @ vector


def _is_reasonable_observed_payload(
    observed: dict,
    fallback: dict,
    diagnostics: Optional[_PathFitDiagnostics] = None,
) -> bool:
    if any(observed.get(key) is None for key in ("perihelion_distance_au", "eccentricity", "inclination_deg", "ascending_node_deg", "argument_of_perihelion_deg", "mean_anomaly_deg")):
        return False
    if not (0.0 < float(observed["perihelion_distance_au"]) < 2.0):
        return False
    if not (0.0 < float(observed["eccentricity"]) < 1.5):
        return False
    if not (0.0 <= float(observed["inclination_deg"]) <= 180.0):
        return False
    if abs(float(observed["mean_anomaly_deg"])) > 720.0:
        return False
    if diagnostics is None:
        return False
    if diagnostics.track_count < _MIN_TRACKS or diagnostics.fit_point_count < _MIN_FIT_POINTS:
        return False
    if diagnostics.median_residual_km > _MAX_OBSERVED_MEDIAN_RESIDUAL_KM:
        return False
    if diagnostics.max_residual_km > _MAX_OBSERVED_MAX_RESIDUAL_KM:
        return False

    if any(fallback.get(key) is None for key in ("perihelion_distance_au", "eccentricity", "inclination_deg", "ascending_node_deg", "argument_of_perihelion_deg")):
        return True
    if abs(float(observed["perihelion_distance_au"]) - float(fallback["perihelion_distance_au"])) > 0.05:
        return False
    if abs(float(observed["eccentricity"]) - float(fallback["eccentricity"])) > 0.35:
        return False
    if abs(float(observed["inclination_deg"]) - float(fallback["inclination_deg"])) > 15.0:
        return False
    if _wrapped_angle_delta(float(observed["ascending_node_deg"]), float(fallback["ascending_node_deg"])) > 15.0:
        return False
    if _wrapped_angle_delta(float(observed["argument_of_perihelion_deg"]), float(fallback["argument_of_perihelion_deg"])) > 20.0:
        return False
    if (
        observed.get("mean_anomaly_deg") is not None
        and fallback.get("mean_anomaly_deg") is not None
        and _wrapped_angle_delta(float(observed["mean_anomaly_deg"]), float(fallback["mean_anomaly_deg"]))
        > _MAX_OBSERVED_MEAN_ANOMALY_DELTA_DEG
    ):
        return False
    return True


def _can_stabilize_mean_anomaly(
    observed: dict,
    fallback: dict,
    diagnostics: Optional[_PathFitDiagnostics],
) -> bool:
    if diagnostics is None:
        return False
    if diagnostics.track_count < _MIN_TRACKS or diagnostics.fit_point_count < _MIN_FIT_POINTS:
        return False
    if diagnostics.median_residual_km > _MAX_OBSERVED_MEDIAN_RESIDUAL_KM:
        return False
    if diagnostics.max_residual_km > _MAX_OBSERVED_MAX_RESIDUAL_KM:
        return False
    required_keys = (
        "perihelion_distance_au",
        "eccentricity",
        "inclination_deg",
        "ascending_node_deg",
        "argument_of_perihelion_deg",
        "mean_anomaly_deg",
    )
    if any(observed.get(key) is None or fallback.get(key) is None for key in required_keys):
        return False
    if (
        abs(float(observed["perihelion_distance_au"]) - float(fallback["perihelion_distance_au"]))
        > _MAX_STABLE_Q_DELTA_AU
    ):
        return False
    if (
        abs(float(observed["eccentricity"]) - float(fallback["eccentricity"]))
        > _MAX_STABLE_ECCENTRICITY_DELTA
    ):
        return False
    if (
        abs(float(observed["inclination_deg"]) - float(fallback["inclination_deg"]))
        > _MAX_STABLE_INCLINATION_DELTA_DEG
    ):
        return False
    if (
        _wrapped_angle_delta(
            float(observed["ascending_node_deg"]),
            float(fallback["ascending_node_deg"]),
        )
        > _MAX_STABLE_NODE_DELTA_DEG
    ):
        return False
    if (
        _wrapped_angle_delta(
            float(observed["argument_of_perihelion_deg"]),
            float(fallback["argument_of_perihelion_deg"]),
        )
        > _MAX_STABLE_ARGUMENT_DELTA_DEG
    ):
        return False
    return (
        _wrapped_angle_delta(
            float(observed["mean_anomaly_deg"]),
            float(fallback["mean_anomaly_deg"]),
        )
        > _MAX_OBSERVED_MEAN_ANOMALY_DELTA_DEG
    )


def _stabilize_observed_payload(
    observed: dict,
    fallback: dict,
    diagnostics: Optional[_PathFitDiagnostics],
) -> dict:
    if not _can_stabilize_mean_anomaly(observed, fallback, diagnostics):
        return observed
    stabilized = dict(observed)
    stabilized["mean_anomaly_deg"] = fallback["mean_anomaly_deg"]
    stabilized["epoch"] = fallback["epoch"]
    return stabilized


def _state_to_payload(position_km: np.ndarray, velocity_kms: np.ndarray, when: datetime) -> dict:
    radius_km = _vector_length(position_km)
    speed_kms = _vector_length(velocity_kms)
    if radius_km == 0 or speed_kms == 0:
        return _empty_orbit_payload()

    angular_momentum = _cross(position_km, velocity_kms)
    angular_momentum_norm = _vector_length(angular_momentum)
    if angular_momentum_norm == 0:
        return _empty_orbit_payload()

    eccentricity_vector = ((_cross(velocity_kms, angular_momentum) / _SOLAR_MU_KM_S2) - (position_km / radius_km))
    eccentricity = _vector_length(eccentricity_vector)
    node_vector = _cross(np.array([0.0, 0.0, 1.0]), angular_momentum)
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
    perihelion_distance_au = (
        (angular_momentum_norm * angular_momentum_norm) / _SOLAR_MU_KM_S2 / (1.0 + eccentricity)
    ) / _ASTRONOMICAL_UNIT_KM

    if abs(1.0 - eccentricity) < 1e-6 or specific_energy == 0:
        return {
            "perihelion_distance_au": round(perihelion_distance_au, 6),
            "eccentricity": round(eccentricity, 6),
            "inclination_deg": round(inclination_deg, 3),
            "ascending_node_deg": round(ascending_node_deg, 3),
            "argument_of_perihelion_deg": round(argument_of_perihelion_deg, 3),
            "mean_anomaly_deg": None,
            "epoch": _utc_datetime(when).isoformat(),
        }

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

    return {
        "perihelion_distance_au": round(perihelion_distance_au, 6),
        "eccentricity": round(eccentricity, 6),
        "inclination_deg": round(inclination_deg, 3),
        "ascending_node_deg": round(ascending_node_deg, 3),
        "argument_of_perihelion_deg": round(argument_of_perihelion_deg, 3),
        "mean_anomaly_deg": round(mean_anomaly_deg, 3) if mean_anomaly_deg is not None else None,
        "epoch": _utc_datetime(when).isoformat(),
    }


def _julian_day(value: datetime) -> float:
    utc_value = _utc_datetime(value)
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


def _earth_heliocentric_position_au(value: datetime) -> np.ndarray:
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

    return np.array(
        [
            -radius_au * math.cos(ecliptic_longitude),
            -radius_au * math.sin(ecliptic_longitude),
            0.0,
        ],
        dtype=float,
    )


def _earth_heliocentric_velocity_kms(value: datetime) -> np.ndarray:
    delta = timedelta(seconds=_EARTH_ORBIT_SAMPLE_SECONDS)
    before = _earth_heliocentric_position_au(value - delta)
    after = _earth_heliocentric_position_au(value + delta)
    derivative_au_per_second = (after - before) / (2.0 * _EARTH_ORBIT_SAMPLE_SECONDS)
    return derivative_au_per_second * _ASTRONOMICAL_UNIT_KM


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


def _legacy_stat_orbit(event: Event) -> dict:
    if event.track_speed is None or event.date is None:
        return _empty_orbit_payload()

    radiant = _ecliptic_radiant(event)
    if radiant is None:
        return _empty_orbit_payload()

    radiant_longitude = math.radians(radiant[0])
    radiant_latitude = math.radians(radiant[1])
    radiant_unit = np.array(
        [
            math.cos(radiant_latitude) * math.cos(radiant_longitude),
            math.cos(radiant_latitude) * math.sin(radiant_longitude),
            math.sin(radiant_latitude),
        ],
        dtype=float,
    )
    heliocentric_velocity = _earth_heliocentric_velocity_kms(event.date) + (radiant_unit * -float(event.track_speed))
    position_km = _earth_heliocentric_position_au(event.date) * _ASTRONOMICAL_UNIT_KM
    return _state_to_payload(position_km, heliocentric_velocity, event.date)


def _point_direction(point: ObservationTrailPoint) -> Optional[tuple[float, float]]:
    if point.ams_coord_long is not None and point.ams_coord_lat is not None:
        return (point.ams_coord_long, point.ams_coord_lat)
    if point.coord_long is not None and point.coord_lat is not None:
        return (point.coord_long, point.coord_lat)
    return None


def _los_ecef_from_horizontal(latitude_deg: float, longitude_deg: float, azimuth_deg: float, altitude_deg: float) -> Optional[np.ndarray]:
    latitude_rad = math.radians(latitude_deg)
    longitude_rad = math.radians(longitude_deg)
    azimuth_rad = math.radians(azimuth_deg)
    altitude_rad = math.radians(altitude_deg)

    east = math.cos(altitude_rad) * math.sin(azimuth_rad)
    north = math.cos(altitude_rad) * math.cos(azimuth_rad)
    up = math.sin(altitude_rad)

    los_ecef = np.array(
        [
            (-math.sin(longitude_rad) * east)
            - (math.sin(latitude_rad) * math.cos(longitude_rad) * north)
            + (math.cos(latitude_rad) * math.cos(longitude_rad) * up),
            (math.cos(longitude_rad) * east)
            - (math.sin(latitude_rad) * math.sin(longitude_rad) * north)
            + (math.cos(latitude_rad) * math.sin(longitude_rad) * up),
            (math.cos(latitude_rad) * north) + (math.sin(latitude_rad) * up),
        ],
        dtype=float,
    )
    return _unit(los_ecef)


def _build_track(record: ObservationCamData) -> Optional[_ObservationTrack]:
    if record.summary_latitude is None or record.summary_longitude is None or not record.trail_points:
        return None

    location = EarthLocation.from_geodetic(
        lon=float(record.summary_longitude) * u.deg,
        lat=float(record.summary_latitude) * u.deg,
        height=float(record.summary_elevation or 0) * u.m,
    )
    site_ecef = np.array(
        [component.to_value(u.km) for component in location.to_geocentric()],
        dtype=float,
    )
    points = []
    for point in sorted(record.trail_points, key=lambda item: (item.event_timestamp or float("inf"), item.frame_index)):
        if point.event_timestamp is None:
            continue
        direction = _point_direction(point)
        if direction is None:
            continue
        los_ecef = _los_ecef_from_horizontal(
            float(record.summary_latitude),
            float(record.summary_longitude),
            float(direction[0]),
            float(direction[1]),
        )
        if los_ecef is None:
            continue
        points.append(_TrackPoint(timestamp=float(point.event_timestamp), los_ecef=los_ecef))
    if len(points) < 2:
        return None
    return _ObservationTrack(site_ecef=site_ecef, points=points)


def _fit_plane_normal(track: _ObservationTrack) -> Optional[np.ndarray]:
    matrix = np.asarray([point.los_ecef for point in track.points], dtype=float)
    if matrix.shape[0] < 2:
        return None
    _, _, vh = np.linalg.svd(matrix)
    return _unit(vh[-1])


def _fit_trajectory_direction(tracks: Sequence[_ObservationTrack]) -> Optional[np.ndarray]:
    normals = [normal for normal in (_fit_plane_normal(track) for track in tracks) if normal is not None]
    if len(normals) < _MIN_TRACKS:
        return None
    _, _, vh = np.linalg.svd(np.asarray(normals, dtype=float))
    return _unit(vh[-1])


def _fit_line_anchor(direction: np.ndarray, tracks: Sequence[_ObservationTrack]) -> Optional[np.ndarray]:
    matrix = np.zeros((3, 3), dtype=float)
    target = np.zeros(3, dtype=float)
    for track in tracks:
        for point in track.points:
            normal = _unit(np.cross(direction, point.los_ecef))
            if normal is None:
                continue
            projector = np.outer(normal, normal)
            matrix += projector
            target += projector @ track.site_ecef
    if np.linalg.matrix_rank(matrix) < 2:
        return None
    return np.linalg.lstsq(matrix, target, rcond=None)[0]


def _trajectory_scalar(anchor: np.ndarray, direction: np.ndarray, track: _ObservationTrack, point: _TrackPoint) -> Optional[float]:
    delta = anchor - track.site_ecef
    dot_du = _dot(direction, point.los_ecef)
    denominator = 1.0 - (dot_du * dot_du)
    if abs(denominator) < 1e-9:
        return None
    return ((dot_du * _dot(point.los_ecef, delta)) - _dot(direction, delta)) / denominator


def _path_endpoints_ecef(event: Event) -> Optional[tuple[np.ndarray, np.ndarray]]:
    if (
        event.track_startlat is None
        or event.track_startlong is None
        or event.track_startheight is None
        or event.track_endlat is None
        or event.track_endlong is None
        or event.track_endheight is None
    ):
        return None
    start = EarthLocation.from_geodetic(
        lon=float(event.track_startlong) * u.deg,
        lat=float(event.track_startlat) * u.deg,
        height=float(event.track_startheight) * u.km,
    )
    end = EarthLocation.from_geodetic(
        lon=float(event.track_endlong) * u.deg,
        lat=float(event.track_endlat) * u.deg,
        height=float(event.track_endheight) * u.km,
    )
    return (
        np.array([component.to_value(u.km) for component in start.to_geocentric()], dtype=float),
        np.array([component.to_value(u.km) for component in end.to_geocentric()], dtype=float),
    )


def _project_path_scalar(
    path_start: np.ndarray,
    path_direction: np.ndarray,
    track: _ObservationTrack,
    point: _TrackPoint,
) -> Optional[tuple[float, float]]:
    delta = path_start - track.site_ecef
    dot_du = _dot(path_direction, point.los_ecef)
    denominator = 1.0 - (dot_du * dot_du)
    if abs(denominator) < 1e-9:
        return None
    scalar = ((dot_du * _dot(point.los_ecef, delta)) - _dot(path_direction, delta)) / denominator
    ray_distance = (_dot(point.los_ecef, delta) - (dot_du * _dot(path_direction, delta))) / denominator
    if ray_distance < 0:
        return None
    path_point = path_start + (path_direction * scalar)
    ray_point = track.site_ecef + (point.los_ecef * ray_distance)
    residual_km = _vector_length(path_point - ray_point)
    return scalar, residual_km


def _fit_path_state(
    event: Event,
    tracks: Sequence[_ObservationTrack],
) -> Optional[tuple[np.ndarray, np.ndarray, datetime, _PathFitDiagnostics]]:
    endpoints = _path_endpoints_ecef(event)
    if endpoints is None:
        return None
    path_start, path_end = endpoints
    path_vector = path_end - path_start
    path_length_km = _vector_length(path_vector)
    path_direction = _unit(path_vector)
    if path_direction is None or path_length_km == 0:
        return None

    samples: list[tuple[float, float, float]] = []
    contributing_tracks: set[int] = set()
    for track_index, track in enumerate(tracks):
        for point in track.points:
            projection = _project_path_scalar(path_start, path_direction, track, point)
            if projection is None:
                continue
            scalar_km, residual_km = projection
            if residual_km > 8.0:
                continue
            if scalar_km < (-0.15 * path_length_km) or scalar_km > (1.2 * path_length_km):
                continue
            samples.append((point.timestamp, scalar_km, residual_km))
            contributing_tracks.add(track_index)
    if len(samples) < _MIN_FIT_POINTS or len(contributing_tracks) < _MIN_TRACKS:
        return None

    design_rows = []
    target_scalars = []
    weights = []
    timestamps = []
    for track_index, track in enumerate(tracks):
        for point in track.points:
            projection = _project_path_scalar(path_start, path_direction, track, point)
            if projection is None:
                continue
            scalar_km, residual_km = projection
            if residual_km > 8.0:
                continue
            if scalar_km < (-0.15 * path_length_km) or scalar_km > (1.2 * path_length_km):
                continue
            row = [0.0]
            for intercept_index in range(len(tracks)):
                row.append(1.0 if intercept_index == track_index else 0.0)
            design_rows.append(row)
            target_scalars.append(scalar_km)
            weights.append(1.0 / max(residual_km, 0.25))
            timestamps.append(float(point.timestamp))
    if len(target_scalars) < _MIN_FIT_POINTS:
        return None

    design = np.asarray(design_rows, dtype=float)
    targets = np.asarray(target_scalars, dtype=float)
    weight_vector = np.asarray(weights, dtype=float)
    weight_sum = float(weight_vector.sum())
    if weight_sum == 0:
        return None
    time_center = float(np.sum(weight_vector * np.asarray(timestamps, dtype=float)) / weight_sum)
    design[:, 0] = np.asarray(timestamps, dtype=float) - time_center
    weighted_design = design * weight_vector[:, None]
    weighted_targets = targets * weight_vector
    solution, _, _, _ = np.linalg.lstsq(weighted_design, weighted_targets, rcond=None)
    speed_kms = float(solution[0])
    if speed_kms < 0:
        path_direction = -path_direction
        targets = -targets
        solution, _, _, _ = np.linalg.lstsq(weighted_design, targets * weight_vector, rcond=None)
        speed_kms = float(solution[0])
    if speed_kms < _MIN_ORBIT_SPEED_KMS or speed_kms > _MAX_ORBIT_SPEED_KMS:
        return None
    intercepts = np.asarray(solution[1:], dtype=float)
    start_timestamps = [
        time_center - (intercept / speed_kms)
        for intercept in intercepts
        if math.isfinite(intercept)
    ]
    if not start_timestamps:
        return None
    start_timestamp = min(start_timestamps)
    if not math.isfinite(start_timestamp):
        return None
    diagnostics = _PathFitDiagnostics(
        track_count=len(contributing_tracks),
        fit_point_count=len(target_scalars),
        median_residual_km=float(np.median([item[2] for item in samples])),
        max_residual_km=float(np.max([item[2] for item in samples])),
    )
    return path_start, path_direction * speed_kms, _utc_datetime(start_timestamp), diagnostics


def _fit_observed_state(event: Event, tracks: Sequence[_ObservationTrack]) -> Optional[tuple[np.ndarray, np.ndarray, datetime]]:
    direction = _fit_trajectory_direction(tracks)
    if direction is None:
        return None

    if (
        event.track_startlat is not None
        and event.track_startlong is not None
        and event.track_startheight is not None
        and event.track_endlat is not None
        and event.track_endlong is not None
        and event.track_endheight is not None
    ):
        start_ecef = np.array(
            [
                component.to_value(u.km)
                for component in EarthLocation.from_geodetic(
                    lon=float(event.track_startlong) * u.deg,
                    lat=float(event.track_startlat) * u.deg,
                    height=float(event.track_startheight) * u.km,
                ).to_geocentric()
            ],
            dtype=float,
        )
        end_ecef = np.array(
            [
                component.to_value(u.km)
                for component in EarthLocation.from_geodetic(
                    lon=float(event.track_endlong) * u.deg,
                    lat=float(event.track_endlat) * u.deg,
                    height=float(event.track_endheight) * u.km,
                ).to_geocentric()
            ],
            dtype=float,
        )
        if np.dot(direction, end_ecef - start_ecef) < 0:
            direction = -direction

    anchor = _fit_line_anchor(direction, tracks)
    if anchor is None:
        return None

    design_rows = []
    observed_scalars = []
    timestamps = []
    for track_index, track in enumerate(tracks):
        for point in track.points:
            scalar = _trajectory_scalar(anchor, direction, track, point)
            if scalar is None:
                continue
            timestamps.append(float(point.timestamp))
            row = [0.0]
            for intercept_index in range(len(tracks)):
                row.append(1.0 if intercept_index == track_index else 0.0)
            design_rows.append(row)
            observed_scalars.append(scalar)
    if len(observed_scalars) < _MIN_FIT_POINTS:
        return None

    design = np.asarray(design_rows, dtype=float)
    targets = np.asarray(observed_scalars, dtype=float)
    time_center = min(timestamps)
    design[:, 0] = np.asarray(timestamps, dtype=float) - time_center
    solution, _, _, _ = np.linalg.lstsq(design, targets, rcond=None)
    speed_kms = float(solution[0])
    if speed_kms < 0:
        direction = -direction
        targets = -targets
        solution, _, _, _ = np.linalg.lstsq(design, targets, rcond=None)
        speed_kms = float(solution[0])
    if speed_kms < _MIN_ORBIT_SPEED_KMS or speed_kms > _MAX_ORBIT_SPEED_KMS:
        return None

    if event.track_startlat is not None and event.track_startlong is not None and event.track_startheight is not None:
        start_point = np.array(
            [
                component.to_value(u.km)
                for component in EarthLocation.from_geodetic(
                    lon=float(event.track_startlong) * u.deg,
                    lat=float(event.track_startlat) * u.deg,
                    height=float(event.track_startheight) * u.km,
                ).to_geocentric()
            ],
            dtype=float,
        )
    else:
        intercepts = solution[1:]
        start_point = anchor + (direction * float(np.min(intercepts)))

    when = _utc_datetime(event.date) if event.date is not None else _utc_datetime(0.0)
    return (start_point, direction * speed_kms, when)


def _earth_heliocentric_state(when: datetime) -> tuple[np.ndarray, np.ndarray]:
    time = Time(_utc_datetime(when))
    with solar_system_ephemeris.set("builtin"):
        earth_pos, earth_vel = get_body_barycentric_posvel("earth", time)
        sun_pos, sun_vel = get_body_barycentric_posvel("sun", time)
    position = (earth_pos.xyz - sun_pos.xyz).to_value(u.km)
    velocity = (earth_vel.xyz - sun_vel.xyz).to_value(u.km / u.s)
    return (np.array(position, dtype=float), np.array(velocity, dtype=float))


def _incoming_hyperbolic_excess(position_km: np.ndarray, velocity_kms: np.ndarray) -> Optional[np.ndarray]:
    radius_km = _vector_length(position_km)
    speed_kms = _vector_length(velocity_kms)
    if radius_km == 0 or speed_kms == 0:
        return None
    specific_energy = (speed_kms * speed_kms / 2.0) - (_EARTH_MU_KM_S2 / radius_km)
    if specific_energy <= 0:
        return None

    h_vec = _cross(position_km, velocity_kms)
    h_norm = _vector_length(h_vec)
    if h_norm == 0:
        return None
    e_vec = ((_cross(velocity_kms, h_vec) / _EARTH_MU_KM_S2) - (position_km / radius_km))
    eccentricity = _vector_length(e_vec)
    if eccentricity <= 1.0:
        return None

    p_hat = _unit(e_vec)
    h_hat = _unit(h_vec)
    if p_hat is None or h_hat is None:
        return None
    q_hat = _unit(_cross(h_hat, p_hat))
    if q_hat is None:
        return None

    v_inf_mag = math.sqrt(2.0 * specific_energy)
    f_inf = math.acos(-1.0 / eccentricity)
    candidates = []
    for branch in (-f_inf, f_inf):
        velocity = (-math.sin(branch) * p_hat) + ((eccentricity + math.cos(branch)) * q_hat)
        unit_velocity = _unit(velocity)
        if unit_velocity is not None:
            candidates.append(unit_velocity * v_inf_mag)
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: _dot(candidate, velocity_kms))


def _solve_observation_candidate(
    event: Event,
    observations: Iterable[ObservationCamData],
) -> Optional[_ObservationOrbitCandidate]:
    if not event.camera_confirmed or event.date is None:
        return None
    tracks = [track for track in (_build_track(record) for record in observations) if track is not None]
    if len(tracks) < _MIN_TRACKS:
        return None

    diagnostics = None
    observed_state = _fit_path_state(event, tracks)
    if observed_state is None:
        observed_state = _fit_observed_state(event, tracks)
    if observed_state is None:
        return None
    if len(observed_state) == 4:
        position_ecef_km, observed_velocity_kms, when, diagnostics = observed_state
    else:
        position_ecef_km, observed_velocity_kms, when = observed_state
    obstime = Time(_utc_datetime(when))
    start_itrs = SkyCoord(
        ITRS(
            representation_type=CartesianRepresentation,
            x=position_ecef_km[0] * u.km,
            y=position_ecef_km[1] * u.km,
            z=position_ecef_km[2] * u.km,
            obstime=obstime,
        )
    )
    end_itrs = SkyCoord(
        ITRS(
            representation_type=CartesianRepresentation,
            x=(position_ecef_km[0] + observed_velocity_kms[0]) * u.km,
            y=(position_ecef_km[1] + observed_velocity_kms[1]) * u.km,
            z=(position_ecef_km[2] + observed_velocity_kms[2]) * u.km,
            obstime=obstime,
        )
    )
    start_gcrs = start_itrs.transform_to(GCRS(obstime=obstime))
    end_gcrs = end_itrs.transform_to(GCRS(obstime=obstime))
    position_gcrs_km = np.array(start_gcrs.cartesian.xyz.to_value(u.km), dtype=float)
    observed_velocity_gcrs_kms = (
        np.array(end_gcrs.cartesian.xyz.to_value(u.km), dtype=float) - position_gcrs_km
    )

    v_inf_kms = _incoming_hyperbolic_excess(position_gcrs_km, observed_velocity_gcrs_kms)
    if v_inf_kms is None:
        return None

    earth_position_km, earth_velocity_kms = _earth_heliocentric_state(when)
    heliocentric_position_km = _equatorial_to_ecliptic(earth_position_km + position_gcrs_km)
    heliocentric_velocity_kms = _equatorial_to_ecliptic(earth_velocity_kms + v_inf_kms)
    return _ObservationOrbitCandidate(
        payload=_state_to_payload(heliocentric_position_km, heliocentric_velocity_kms, when),
        diagnostics=diagnostics,
    )


def solve_observation_orbit(event: Event, observations: Iterable[ObservationCamData]) -> Optional[dict]:
    candidate = _solve_observation_candidate(event, observations)
    return candidate.payload if candidate is not None else None


def solve_event_orbit(event: Event, observations: Optional[Iterable[ObservationCamData]] = None) -> dict:
    if observations:
        observed_payload = solve_observation_orbit(event, observations)
        if observed_payload is not None:
            return observed_payload
    return _legacy_stat_orbit(event)


def build_orbit_payload(
    event: Event,
    observations: Iterable[ObservationCamData],
    fallback_factory: Optional[Callable[[Event], dict]] = None,
) -> dict:
    fallback_payload = fallback_factory(event) if fallback_factory is not None else _legacy_stat_orbit(event)
    candidate = _solve_observation_candidate(event, observations)
    observed_payload = (
        _stabilize_observed_payload(candidate.payload, fallback_payload, candidate.diagnostics)
        if candidate is not None
        else None
    )
    if observed_payload is not None and _is_reasonable_observed_payload(
        observed_payload,
        fallback_payload,
        candidate.diagnostics if candidate is not None else None,
    ):
        return observed_payload
    return fallback_payload
