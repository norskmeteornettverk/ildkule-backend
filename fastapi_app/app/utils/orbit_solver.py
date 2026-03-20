from __future__ import annotations

import math
from dataclasses import dataclass, replace
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
_MAX_ORBIT_SPEED_KMS = 150.0
_MAX_OBSERVED_MEAN_ANOMALY_DELTA_DEG = 15.0
_MAX_OBSERVED_MEDIAN_RESIDUAL_KM = 0.3
_MAX_OBSERVED_MAX_RESIDUAL_KM = 0.8
_MAX_STABLE_Q_DELTA_AU = 0.12
_MAX_STABLE_ECCENTRICITY_DELTA = 0.6
_MAX_STABLE_INCLINATION_DELTA_DEG = 20.0
_MAX_STABLE_NODE_DELTA_DEG = 30.0
_MAX_STABLE_ARGUMENT_DELTA_DEG = 30.0
_LATE_SERIES_START = 0.7
_VERY_LATE_SERIES_START = 0.85
_LATE_SPEED_DROP_RATIO = 0.78
_MAX_REASONABLE_DECELERATION_KMS2 = 2.5
_MIN_REASONABLE_DECELERATION_KMS2 = -20.0
_TIMING_TRACK_SOFT_OFFSET_SECONDS = 0.12
_TIMING_TRACK_HARD_OFFSET_SECONDS = 0.25
_TIMING_SPREAD_SOFT_SECONDS = 0.22
_TIMING_SPREAD_HARD_SECONDS = 0.45
_TIMING_SPREAD_RELAXED_SECONDS = 1.2
_STRONG_OBSERVED_TRACKS = 3
_STRONG_OBSERVED_FIT_POINTS = 8
_RELAXED_OBSERVED_FIT_POINTS = 20
_RICH_OBSERVED_TRACKS = 3
_RICH_OBSERVED_FIT_POINTS = 30
_RICH_OBSERVED_TIMING_SPREAD_SECONDS = 2.0
_VERY_RICH_OBSERVED_TRACKS = 4
_VERY_RICH_OBSERVED_FIT_POINTS = 100
_VERY_RICH_OBSERVED_TIMING_SPREAD_SECONDS = 1.0
_AUTO_PATH_POLICY = "auto"
_RUNTIME_PATH_POLICY = _AUTO_PATH_POLICY


@dataclass(frozen=True)
class _TrackPoint:
    timestamp: float
    los_ecef: np.ndarray
    edge_distance: int
    uses_ams: bool


@dataclass(frozen=True)
class _ObservationTrack:
    site_ecef: np.ndarray
    points: Sequence[_TrackPoint]


@dataclass(frozen=True)
class _ProjectedPathSample:
    track_index: int
    timestamp: float
    scalar_km: float
    residual_km: float
    edge_distance: int
    series_fraction: float = 0.0
    local_speed_kms: Optional[float] = None
    track_reference_speed_kms: Optional[float] = None
    uses_ams: bool = False
    is_marginal: bool = False


@dataclass(frozen=True)
class _PathFitDiagnostics:
    track_count: int
    fit_point_count: int
    median_residual_km: float
    max_residual_km: float
    policy_name: str = "unknown"
    timing_spread_seconds: float = 0.0
    late_point_fraction: float = 0.0


@dataclass(frozen=True)
class _ObservationOrbitCandidate:
    payload: dict
    diagnostics: Optional[_PathFitDiagnostics]


def _allowed_fit_thresholds(diagnostics: Optional[_PathFitDiagnostics]) -> tuple[float, float]:
    if diagnostics is None:
        return (_MAX_OBSERVED_MEDIAN_RESIDUAL_KM, _MAX_OBSERVED_MAX_RESIDUAL_KM)
    if (
        diagnostics.track_count >= _VERY_RICH_OBSERVED_TRACKS
        and diagnostics.fit_point_count >= _VERY_RICH_OBSERVED_FIT_POINTS
        and diagnostics.timing_spread_seconds <= _VERY_RICH_OBSERVED_TIMING_SPREAD_SECONDS
        and diagnostics.late_point_fraction <= 0.35
    ):
        return (1.1, 2.4)
    if (
        diagnostics.track_count >= _STRONG_OBSERVED_TRACKS
        and diagnostics.fit_point_count >= _STRONG_OBSERVED_FIT_POINTS
        and diagnostics.timing_spread_seconds <= _TIMING_SPREAD_SOFT_SECONDS
        and diagnostics.late_point_fraction <= 0.65
    ):
        return (0.55, 1.5)
    # Rich multi-station events can still be stable even when the full visible path
    # spans longer than the tighter timing windows used for short tracks.
    if (
        diagnostics.track_count >= _RICH_OBSERVED_TRACKS
        and diagnostics.fit_point_count >= _RICH_OBSERVED_FIT_POINTS
        and diagnostics.timing_spread_seconds <= _RICH_OBSERVED_TIMING_SPREAD_SECONDS
        and diagnostics.late_point_fraction <= 0.35
    ):
        return (1.1, 1.5)
    if (
        diagnostics.fit_point_count >= _RELAXED_OBSERVED_FIT_POINTS
        and diagnostics.timing_spread_seconds <= _TIMING_SPREAD_RELAXED_SECONDS
    ):
        return (0.5, 1.1)
    return (_MAX_OBSERVED_MEDIAN_RESIDUAL_KM, _MAX_OBSERVED_MAX_RESIDUAL_KM)


def _allowed_geometry_deltas(diagnostics: Optional[_PathFitDiagnostics]) -> tuple[float, float, float, float, float]:
    if diagnostics is None:
        return (
            _MAX_STABLE_Q_DELTA_AU,
            _MAX_STABLE_ECCENTRICITY_DELTA,
            _MAX_STABLE_INCLINATION_DELTA_DEG,
            _MAX_STABLE_NODE_DELTA_DEG,
            _MAX_STABLE_ARGUMENT_DELTA_DEG,
        )
    if (
        diagnostics.track_count >= _STRONG_OBSERVED_TRACKS
        and diagnostics.fit_point_count >= _STRONG_OBSERVED_FIT_POINTS
        and diagnostics.timing_spread_seconds <= _TIMING_SPREAD_SOFT_SECONDS
        and diagnostics.late_point_fraction <= 0.6
    ):
        return (0.5, 1.05, 70.0, 150.0, 150.0)
    return (
        0.35,
        0.95,
        45.0,
        120.0,
        120.0,
    )


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
    allowed_median_residual_km, allowed_max_residual_km = _allowed_fit_thresholds(diagnostics)
    if diagnostics.median_residual_km > allowed_median_residual_km:
        return False
    if diagnostics.max_residual_km > allowed_max_residual_km:
        return False
    if any(fallback.get(key) is None for key in ("perihelion_distance_au", "eccentricity", "inclination_deg", "ascending_node_deg", "argument_of_perihelion_deg")):
        return True
    max_q_delta_au, max_e_delta, max_i_delta_deg, max_node_delta_deg, max_argp_delta_deg = _allowed_geometry_deltas(diagnostics)
    if abs(float(observed["perihelion_distance_au"]) - float(fallback["perihelion_distance_au"])) > max_q_delta_au:
        return False
    if abs(float(observed["eccentricity"]) - float(fallback["eccentricity"])) > max_e_delta:
        return False
    if abs(float(observed["inclination_deg"]) - float(fallback["inclination_deg"])) > max_i_delta_deg:
        return False
    if _wrapped_angle_delta(float(observed["ascending_node_deg"]), float(fallback["ascending_node_deg"])) > max_node_delta_deg:
        return False
    if _wrapped_angle_delta(float(observed["argument_of_perihelion_deg"]), float(fallback["argument_of_perihelion_deg"])) > max_argp_delta_deg:
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
    allowed_median_residual_km, allowed_max_residual_km = _allowed_fit_thresholds(diagnostics)
    if diagnostics.median_residual_km > allowed_median_residual_km:
        return False
    if diagnostics.max_residual_km > allowed_max_residual_km:
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
    max_q_delta_au, max_e_delta, max_i_delta_deg, max_node_delta_deg, max_argp_delta_deg = _allowed_geometry_deltas(diagnostics)
    if (
        abs(float(observed["perihelion_distance_au"]) - float(fallback["perihelion_distance_au"]))
        > max_q_delta_au
    ):
        return False
    if (
        abs(float(observed["eccentricity"]) - float(fallback["eccentricity"]))
        > max_e_delta
    ):
        return False
    if (
        abs(float(observed["inclination_deg"]) - float(fallback["inclination_deg"]))
        > max_i_delta_deg
    ):
        return False
    if (
        _wrapped_angle_delta(
            float(observed["ascending_node_deg"]),
            float(fallback["ascending_node_deg"]),
        )
        > max_node_delta_deg
    ):
        return False
    if (
        _wrapped_angle_delta(
            float(observed["argument_of_perihelion_deg"]),
            float(fallback["argument_of_perihelion_deg"]),
        )
        > max_argp_delta_deg
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


def _runtime_payload_from_candidate(
    candidate: Optional[_ObservationOrbitCandidate],
    fallback_payload: dict,
) -> dict:
    if candidate is None:
        return fallback_payload
    observed_payload = _stabilize_observed_payload(
        candidate.payload,
        fallback_payload,
        candidate.diagnostics,
    )
    if _is_reasonable_observed_payload(
        observed_payload,
        fallback_payload,
        candidate.diagnostics,
    ):
        return observed_payload
    return fallback_payload


def _runtime_payload_from_candidates(
    candidates: Sequence[_ObservationOrbitCandidate],
    fallback_payload: dict,
) -> dict:
    for candidate in candidates:
        observed_payload = _stabilize_observed_payload(
            candidate.payload,
            fallback_payload,
            candidate.diagnostics,
        )
        if _is_reasonable_observed_payload(
            observed_payload,
            fallback_payload,
            candidate.diagnostics,
        ):
            return observed_payload
    return fallback_payload


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
    if point.centroid2_coord_long is not None and point.centroid2_coord_lat is not None:
        return (point.centroid2_coord_long, point.centroid2_coord_lat)
    if point.ams_coord_long is not None and point.ams_coord_lat is not None:
        return (point.ams_coord_long, point.ams_coord_lat)
    if point.centroid_coord_long is not None and point.centroid_coord_lat is not None:
        return (point.centroid_coord_long, point.centroid_coord_lat)
    if point.coord_long is not None and point.coord_lat is not None:
        return (point.coord_long, point.coord_lat)
    return None


def _point_uses_ams(point: ObservationTrailPoint) -> bool:
    return point.ams_coord_long is not None and point.ams_coord_lat is not None


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
    raw_points: list[tuple[float, np.ndarray, bool]] = []
    for point in sorted(record.trail_points, key=lambda item: (item.event_timestamp or float("inf"), item.frame_index)):
        if point.event_timestamp is None:
            continue
        direction = _point_direction(point)
        if direction is None:
            continue
        uses_ams = _point_uses_ams(point)
        los_ecef = _los_ecef_from_horizontal(
            float(record.summary_latitude),
            float(record.summary_longitude),
            float(direction[0]),
            float(direction[1]),
        )
        if los_ecef is None:
            continue
        raw_points.append((float(point.event_timestamp), los_ecef, uses_ams))
    if len(raw_points) < 2:
        return None
    point_count = len(raw_points)
    points = [
        _TrackPoint(
            timestamp=timestamp,
            los_ecef=los_ecef,
            edge_distance=min(index, point_count - index - 1),
            uses_ams=uses_ams,
        )
        for index, (timestamp, los_ecef, uses_ams) in enumerate(raw_points)
    ]
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


def _sample_line_scalar_and_residual(
    line_anchor: np.ndarray,
    line_direction: np.ndarray,
    track: _ObservationTrack,
    point: _TrackPoint,
) -> Optional[tuple[float, float]]:
    delta = line_anchor - track.site_ecef
    dot_du = _dot(line_direction, point.los_ecef)
    denominator = 1.0 - (dot_du * dot_du)
    if abs(denominator) < 1e-9:
        return None
    scalar = ((dot_du * _dot(point.los_ecef, delta)) - _dot(line_direction, delta)) / denominator
    ray_distance = (_dot(point.los_ecef, delta) - (dot_du * _dot(line_direction, delta))) / denominator
    if ray_distance < 0:
        return None
    line_point = line_anchor + (line_direction * scalar)
    ray_point = track.site_ecef + (point.los_ecef * ray_distance)
    return scalar, _vector_length(line_point - ray_point)


def _trim_endpoint_outliers(samples: Sequence[_ProjectedPathSample]) -> list[_ProjectedPathSample]:
    trimmed = list(samples)
    while len(trimmed) > (_MIN_FIT_POINTS + 1):
        changed = False
        if (
            len(trimmed) >= 3
            and trimmed[0].residual_km > max(0.55, trimmed[1].residual_km * 2.2)
        ):
            trimmed = trimmed[1:]
            changed = True
        if (
            len(trimmed) >= 3
            and trimmed[-1].residual_km > max(0.32, trimmed[-2].residual_km * 1.5)
        ):
            trimmed = trimmed[:-1]
            changed = True
        if not changed:
            break
    return trimmed


def _estimate_local_speed_kms(
    previous_sample: Optional[_ProjectedPathSample],
    current_sample: _ProjectedPathSample,
    next_sample: Optional[_ProjectedPathSample],
) -> Optional[float]:
    candidates: list[float] = []
    for neighbour in (previous_sample, next_sample):
        if neighbour is None:
            continue
        delta_time = abs(current_sample.timestamp - neighbour.timestamp)
        if delta_time <= 1e-6:
            continue
        candidates.append(abs(current_sample.scalar_km - neighbour.scalar_km) / delta_time)
    if not candidates:
        return None
    return float(np.median(np.asarray(candidates, dtype=float)))


def _track_reference_speed_kms(samples: Sequence[_ProjectedPathSample]) -> Optional[float]:
    early_samples = [
        sample.local_speed_kms
        for sample in samples
        if sample.local_speed_kms is not None and sample.series_fraction <= 0.4
    ]
    if not early_samples:
        early_samples = [sample.local_speed_kms for sample in samples if sample.local_speed_kms is not None]
    if not early_samples:
        return None
    return float(np.median(np.asarray(early_samples, dtype=float)))


def _enrich_track_samples(track_samples: Sequence[_ProjectedPathSample]) -> list[_ProjectedPathSample]:
    if not track_samples:
        return []
    enriched: list[_ProjectedPathSample] = []
    last_index = len(track_samples) - 1
    for index, sample in enumerate(track_samples):
        previous_sample = track_samples[index - 1] if index > 0 else None
        next_sample = track_samples[index + 1] if index < last_index else None
        series_fraction = 0.0 if last_index <= 0 else index / last_index
        enriched.append(
            _ProjectedPathSample(
                track_index=sample.track_index,
                timestamp=sample.timestamp,
                scalar_km=sample.scalar_km,
                residual_km=sample.residual_km,
                edge_distance=sample.edge_distance,
                series_fraction=series_fraction,
                local_speed_kms=_estimate_local_speed_kms(previous_sample, sample, next_sample),
                track_reference_speed_kms=None,
                uses_ams=sample.uses_ams,
                is_marginal=sample.is_marginal,
            )
        )
    reference_speed_kms = _track_reference_speed_kms(enriched)
    return [
        _ProjectedPathSample(
            track_index=sample.track_index,
            timestamp=sample.timestamp,
            scalar_km=sample.scalar_km,
            residual_km=sample.residual_km,
            edge_distance=sample.edge_distance,
            series_fraction=sample.series_fraction,
            local_speed_kms=sample.local_speed_kms,
            track_reference_speed_kms=reference_speed_kms,
            uses_ams=sample.uses_ams,
            is_marginal=sample.is_marginal,
        )
        for sample in enriched
    ]


def _collect_projected_path_samples(
    path_start: np.ndarray,
    path_direction: np.ndarray,
    path_length_km: float,
    tracks: Sequence[_ObservationTrack],
) -> list[_ProjectedPathSample]:
    per_track: list[list[_ProjectedPathSample]] = []
    for track_index, track in enumerate(tracks):
        track_samples: list[_ProjectedPathSample] = []
        for point in track.points:
            projection = _project_path_scalar(path_start, path_direction, track, point)
            if projection is None:
                continue
            scalar_km, residual_km = projection
            is_marginal = False
            if residual_km > 12.0:
                continue
            if scalar_km < (-0.3 * path_length_km) or scalar_km > (1.35 * path_length_km):
                continue
            if residual_km > 8.0 or scalar_km < (-0.15 * path_length_km) or scalar_km > (1.2 * path_length_km):
                is_marginal = True
            track_samples.append(
                _ProjectedPathSample(
                    track_index=track_index,
                    timestamp=point.timestamp,
                    scalar_km=scalar_km,
                    residual_km=residual_km,
                    edge_distance=point.edge_distance,
                    series_fraction=0.0,
                    local_speed_kms=None,
                    track_reference_speed_kms=None,
                    uses_ams=point.uses_ams,
                    is_marginal=is_marginal,
                )
            )
        per_track.append(_enrich_track_samples(_trim_endpoint_outliers(track_samples)))
    return [
        sample
        for track_samples in per_track
        for sample in track_samples
    ]



def _fit_track_geometry_state(
    event: Event,
    tracks: Sequence[_ObservationTrack],
    preferred_policy_name: Optional[str] = _RUNTIME_PATH_POLICY,
) -> Optional[tuple[np.ndarray, np.ndarray, datetime, _PathFitDiagnostics]]:
    direction = _fit_trajectory_direction(tracks)
    if direction is None:
        return None
    def collect_samples(direction_vector: np.ndarray) -> Optional[tuple[np.ndarray, list[_ProjectedPathSample], set[int]]]:
        anchor = _fit_line_anchor(direction_vector, tracks)
        if anchor is None:
            return None
        per_track_samples: list[list[_ProjectedPathSample]] = []
        for track_index, track in enumerate(tracks):
            track_samples: list[_ProjectedPathSample] = []
            for point in track.points:
                sample_geometry = _sample_line_scalar_and_residual(anchor, direction_vector, track, point)
                if sample_geometry is None:
                    continue
                scalar_km, residual_km = sample_geometry
                if residual_km > 18.0:
                    continue
                track_samples.append(
                    _ProjectedPathSample(
                        track_index=track_index,
                        timestamp=point.timestamp,
                        scalar_km=scalar_km,
                        residual_km=residual_km,
                        edge_distance=point.edge_distance,
                        uses_ams=point.uses_ams,
                        is_marginal=residual_km > 8.0,
                    )
                )
            per_track_samples.append(_enrich_track_samples(_trim_endpoint_outliers(track_samples)))
        samples = [
            sample
            for track_samples in per_track_samples
            for sample in track_samples
        ]
        contributing_tracks = {sample.track_index for sample in samples}
        if len(samples) < _MIN_FIT_POINTS or len(contributing_tracks) < _MIN_TRACKS:
            return None
        return anchor, samples, contributing_tracks

    collected = collect_samples(direction)
    if collected is None:
        return None
    anchor, samples, contributing_tracks = collected

    scalar_series = np.asarray([sample.scalar_km for sample in samples], dtype=float)
    time_series = np.asarray([sample.timestamp for sample in samples], dtype=float)
    if scalar_series.size >= 2 and float(np.cov(time_series, scalar_series, bias=True)[0, 1]) < 0.0:
        direction = -direction
        collected = collect_samples(direction)
        if collected is None:
            return None
        anchor, samples, contributing_tracks = collected

    selected = _select_best_path_model(samples, len(tracks), preferred_policy_name)
    if selected is None:
        return None
    solved_model, samples = selected
    contributing_tracks = {sample.track_index for sample in samples}

    start_timestamps = _start_timestamps_for_model(solved_model, samples)
    if not start_timestamps:
        return None
    start_timestamp = min(start_timestamps)
    start_speed_kms = solved_model.speed_kms
    if start_speed_kms < _MIN_ORBIT_SPEED_KMS or start_speed_kms > _MAX_ORBIT_SPEED_KMS:
        return None
    late_point_fraction = (
        sum(1 for sample in samples if sample.series_fraction >= _LATE_SERIES_START) / len(samples)
        if samples
        else 0.0
    )
    diagnostics = _PathFitDiagnostics(
        track_count=len(contributing_tracks),
        fit_point_count=len(samples),
        median_residual_km=float(np.median([sample.residual_km for sample in samples])),
        max_residual_km=float(np.max([sample.residual_km for sample in samples])),
        policy_name=solved_model.policy_name,
        timing_spread_seconds=solved_model.timing_spread_seconds,
        late_point_fraction=late_point_fraction,
    )

    start_point = anchor + (direction * float(np.min(solved_model.intercepts)))
    return start_point, direction * start_speed_kms, _utc_datetime(start_timestamp), diagnostics


def _sample_weight(sample: _ProjectedPathSample) -> float:
    residual_weight = 1.0 / max(sample.residual_km, 0.15)
    if sample.is_marginal:
        residual_weight *= 0.18
    if sample.edge_distance <= 0:
        residual_weight *= 0.35
    elif sample.edge_distance == 1:
        residual_weight *= 0.7
    return residual_weight


@dataclass(frozen=True)
class _PathModelSolution:
    policy_name: str
    speed_kms: float
    intercepts: np.ndarray
    time_center: float
    scalar_residual_median_km: float
    scalar_residual_max_km: float
    acceleration_kms2: float = 0.0
    timing_spread_seconds: float = math.inf


def _sample_weight_for_policy(
    sample: _ProjectedPathSample,
    policy_name: str,
    track_weight_scale: float = 1.0,
) -> float:
    weight = _sample_weight(sample)
    if sample.uses_ams:
        weight *= 1.08
    if policy_name in {"policy_b", "policy_c"}:
        if sample.series_fraction >= _VERY_LATE_SERIES_START:
            weight *= 0.12
        elif sample.series_fraction >= _LATE_SERIES_START:
            weight *= 0.32
        if (
            sample.local_speed_kms is not None
            and sample.track_reference_speed_kms is not None
            and sample.track_reference_speed_kms > 0
            and sample.series_fraction >= _LATE_SERIES_START
            and sample.local_speed_kms < (sample.track_reference_speed_kms * _LATE_SPEED_DROP_RATIO)
        ):
            weight *= 0.22
    return weight * track_weight_scale


def _should_trim_late_sample(sample: _ProjectedPathSample, policy_name: str) -> bool:
    if policy_name not in {"policy_b", "policy_c"}:
        return False
    if sample.series_fraction < _LATE_SERIES_START:
        return False
    if sample.local_speed_kms is None or sample.track_reference_speed_kms is None:
        return False
    return (
        (
            sample.local_speed_kms < (sample.track_reference_speed_kms * _LATE_SPEED_DROP_RATIO)
            and sample.residual_km > 0.25
        )
        or (
            sample.series_fraction >= _VERY_LATE_SERIES_START
            and sample.local_speed_kms < (sample.track_reference_speed_kms * 0.88)
            and sample.residual_km > 0.18
        )
    )


def _filter_samples_for_policy(
    samples: Sequence[_ProjectedPathSample],
    policy_name: str,
) -> list[_ProjectedPathSample]:
    filtered = [sample for sample in samples if not _should_trim_late_sample(sample, policy_name)]
    surviving_tracks = {sample.track_index for sample in filtered}
    if len(filtered) < _MIN_FIT_POINTS or len(surviving_tracks) < _MIN_TRACKS:
        return list(samples)
    return filtered


def _predicted_scalar(sample: _ProjectedPathSample, solved_model: _PathModelSolution) -> float:
    sample_dt = sample.timestamp - solved_model.time_center
    return (
        (solved_model.speed_kms * sample_dt)
        + (0.5 * solved_model.acceleration_kms2 * sample_dt * sample_dt)
        + float(solved_model.intercepts[sample.track_index])
    )


def _track_start_timestamps_for_model(
    solved_model: _PathModelSolution,
    samples: Sequence[_ProjectedPathSample],
) -> dict[int, float]:
    per_track_min_dt: dict[int, float] = {}
    for sample in samples:
        sample_dt = sample.timestamp - solved_model.time_center
        current = per_track_min_dt.get(sample.track_index)
        if current is None or sample_dt < current:
            per_track_min_dt[sample.track_index] = sample_dt

    start_timestamps: dict[int, float] = {}
    for track_index, intercept in enumerate(solved_model.intercepts):
        if not math.isfinite(intercept):
            continue
        if abs(solved_model.acceleration_kms2) < 1e-9:
            start_timestamps[track_index] = solved_model.time_center - (intercept / solved_model.speed_kms)
            continue

        a = 0.5 * solved_model.acceleration_kms2
        b = solved_model.speed_kms
        c = float(intercept)
        discriminant = (b * b) - (4.0 * a * c)
        if discriminant < 0:
            continue
        root_term = math.sqrt(discriminant)
        candidate_offsets = [(-b - root_term) / (2.0 * a), (-b + root_term) / (2.0 * a)]
        min_dt = per_track_min_dt.get(track_index, 0.0)
        chosen_offset = min(
            candidate_offsets,
            key=lambda offset: (
                0 if offset <= min_dt else 1,
                abs(offset - min_dt),
            ),
        )
        start_timestamps[track_index] = solved_model.time_center + chosen_offset
    return start_timestamps


def _timing_spread_seconds(
    solved_model: _PathModelSolution,
    samples: Sequence[_ProjectedPathSample],
) -> float:
    start_timestamps = list(_track_start_timestamps_for_model(solved_model, samples).values())
    if len(start_timestamps) < 2:
        return 0.0
    return float(max(start_timestamps) - min(start_timestamps))


def _estimate_track_weight_scales(
    samples: Sequence[_ProjectedPathSample],
    solved_model: _PathModelSolution,
) -> dict[int, float]:
    start_timestamp_map = _track_start_timestamps_for_model(solved_model, samples)
    if len(start_timestamp_map) < _MIN_TRACKS:
        return {}

    median_start_timestamp = float(np.median(np.asarray(list(start_timestamp_map.values()), dtype=float)))
    scalar_residuals = [
        abs(sample.scalar_km - _predicted_scalar(sample, solved_model))
        for sample in samples
    ]
    global_scalar_median = float(np.median(np.asarray(scalar_residuals, dtype=float))) if scalar_residuals else 0.0
    per_track_scalar_residuals: dict[int, list[float]] = {}
    per_track_late_fraction: dict[int, list[float]] = {}
    for sample in samples:
        per_track_scalar_residuals.setdefault(sample.track_index, []).append(
            abs(sample.scalar_km - _predicted_scalar(sample, solved_model))
        )
        per_track_late_fraction.setdefault(sample.track_index, []).append(sample.series_fraction)

    track_weight_scales: dict[int, float] = {}
    for track_index, start_timestamp in start_timestamp_map.items():
        start_offset = abs(start_timestamp - median_start_timestamp)
        scale = 1.0
        if start_offset > _TIMING_TRACK_SOFT_OFFSET_SECONDS:
            scale *= 0.72
        if start_offset > _TIMING_TRACK_HARD_OFFSET_SECONDS:
            scale *= 0.42

        track_scalar_median = float(
            np.median(np.asarray(per_track_scalar_residuals.get(track_index, [0.0]), dtype=float))
        )
        if track_scalar_median > max(0.35, global_scalar_median * 1.3):
            scale *= 0.65

        track_series = per_track_late_fraction.get(track_index, [])
        if track_series:
            median_series_fraction = float(np.median(np.asarray(track_series, dtype=float)))
            if median_series_fraction >= _LATE_SERIES_START:
                scale *= 0.78
            if median_series_fraction >= _VERY_LATE_SERIES_START:
                scale *= 0.6

        if scale < 0.98:
            track_weight_scales[track_index] = scale
    return track_weight_scales


def _solve_linear_path_model(
    samples: Sequence[_ProjectedPathSample],
    track_count: int,
    policy_name: str,
    track_weight_scales: Optional[dict[int, float]] = None,
) -> Optional[_PathModelSolution]:
    if len(samples) < _MIN_FIT_POINTS:
        return None

    design_rows = []
    target_scalars = []
    weights = []
    timestamps = []
    for sample in samples:
        row = [0.0]
        for intercept_index in range(track_count):
            row.append(1.0 if intercept_index == sample.track_index else 0.0)
        design_rows.append(row)
        target_scalars.append(sample.scalar_km)
        weights.append(
            _sample_weight_for_policy(
                sample,
                policy_name,
                float((track_weight_scales or {}).get(sample.track_index, 1.0)),
            )
        )
        timestamps.append(sample.timestamp)

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
    intercepts = np.asarray(solution[1:], dtype=float)
    if speed_kms < 0:
        speed_kms = -speed_kms
        intercepts = -intercepts
    if speed_kms < _MIN_ORBIT_SPEED_KMS or speed_kms > _MAX_ORBIT_SPEED_KMS:
        return None
    scalar_residuals = []
    for sample in samples:
        predicted_scalar = (speed_kms * (sample.timestamp - time_center)) + float(intercepts[sample.track_index])
        scalar_residuals.append(abs(sample.scalar_km - predicted_scalar))
    return _PathModelSolution(
        policy_name=policy_name,
        speed_kms=speed_kms,
        intercepts=intercepts,
        time_center=time_center,
        scalar_residual_median_km=float(np.median(scalar_residuals)),
        scalar_residual_max_km=float(np.max(scalar_residuals)),
        timing_spread_seconds=_timing_spread_seconds(
            _PathModelSolution(
                policy_name=policy_name,
                speed_kms=speed_kms,
                intercepts=intercepts,
                time_center=time_center,
                scalar_residual_median_km=float(np.median(scalar_residuals)),
                scalar_residual_max_km=float(np.max(scalar_residuals)),
            ),
            samples,
        ),
    )


def _solve_quadratic_path_model(
    samples: Sequence[_ProjectedPathSample],
    track_count: int,
    track_weight_scales: Optional[dict[int, float]] = None,
) -> Optional[_PathModelSolution]:
    if len(samples) < (_MIN_FIT_POINTS + 2):
        return None

    design_rows = []
    target_scalars = []
    weights = []
    timestamps = []
    for sample in samples:
        row = [0.0, 0.0]
        for intercept_index in range(track_count):
            row.append(1.0 if intercept_index == sample.track_index else 0.0)
        design_rows.append(row)
        target_scalars.append(sample.scalar_km)
        weights.append(
            _sample_weight_for_policy(
                sample,
                "policy_c",
                float((track_weight_scales or {}).get(sample.track_index, 1.0)),
            )
        )
        timestamps.append(sample.timestamp)

    design = np.asarray(design_rows, dtype=float)
    targets = np.asarray(target_scalars, dtype=float)
    weight_vector = np.asarray(weights, dtype=float)
    weight_sum = float(weight_vector.sum())
    if weight_sum == 0:
        return None
    time_center = float(np.sum(weight_vector * np.asarray(timestamps, dtype=float)) / weight_sum)
    dt = np.asarray(timestamps, dtype=float) - time_center
    design[:, 0] = dt
    design[:, 1] = 0.5 * dt * dt
    weighted_design = design * weight_vector[:, None]
    weighted_targets = targets * weight_vector
    solution, _, _, _ = np.linalg.lstsq(weighted_design, weighted_targets, rcond=None)
    speed_kms = float(solution[0])
    acceleration_kms2 = float(solution[1])
    intercepts = np.asarray(solution[2:], dtype=float)
    if speed_kms < _MIN_ORBIT_SPEED_KMS or speed_kms > _MAX_ORBIT_SPEED_KMS:
        return None
    if acceleration_kms2 < _MIN_REASONABLE_DECELERATION_KMS2 or acceleration_kms2 > _MAX_REASONABLE_DECELERATION_KMS2:
        return None
    scalar_residuals = []
    for sample in samples:
        sample_dt = sample.timestamp - time_center
        predicted_scalar = (
            (speed_kms * sample_dt)
            + (0.5 * acceleration_kms2 * sample_dt * sample_dt)
            + float(intercepts[sample.track_index])
        )
        scalar_residuals.append(abs(sample.scalar_km - predicted_scalar))
    return _PathModelSolution(
        policy_name="policy_c",
        speed_kms=speed_kms,
        intercepts=intercepts,
        time_center=time_center,
        scalar_residual_median_km=float(np.median(scalar_residuals)),
        scalar_residual_max_km=float(np.max(scalar_residuals)),
        acceleration_kms2=acceleration_kms2,
        timing_spread_seconds=_timing_spread_seconds(
            _PathModelSolution(
                policy_name="policy_c",
                speed_kms=speed_kms,
                intercepts=intercepts,
                time_center=time_center,
                scalar_residual_median_km=float(np.median(scalar_residuals)),
                scalar_residual_max_km=float(np.max(scalar_residuals)),
                acceleration_kms2=acceleration_kms2,
            ),
            samples,
        ),
    )


def _trim_temporal_outliers(
    samples: Sequence[_ProjectedPathSample],
    solved_model: Optional[_PathModelSolution] = None,
    *,
    speed_kms: Optional[float] = None,
    intercepts: Optional[np.ndarray] = None,
    time_center: Optional[float] = None,
    acceleration_kms2: float = 0.0,
) -> list[_ProjectedPathSample]:
    if solved_model is None:
        if speed_kms is None or intercepts is None or time_center is None:
            raise TypeError("Either solved_model or speed/intercepts/time_center must be provided")
        solved_model = _PathModelSolution(
            policy_name="compat",
            speed_kms=float(speed_kms),
            intercepts=np.asarray(intercepts, dtype=float),
            time_center=float(time_center),
            scalar_residual_median_km=0.0,
            scalar_residual_max_km=0.0,
            acceleration_kms2=float(acceleration_kms2),
        )
    scalar_residuals = []
    for sample in samples:
        predicted_scalar = _predicted_scalar(sample, solved_model)
        scalar_residuals.append(abs(sample.scalar_km - predicted_scalar))
    if not scalar_residuals:
        return list(samples)

    median_scalar_residual = float(np.median(scalar_residuals))
    robust_scale = max(0.35, median_scalar_residual * 1.4826)
    allowed_scalar_residual = max(0.9, robust_scale * 3.0)
    trimmed = [
        sample
        for sample, scalar_residual in zip(samples, scalar_residuals)
        if scalar_residual <= allowed_scalar_residual
    ]
    surviving_tracks = {sample.track_index for sample in trimmed}
    if len(trimmed) < _MIN_FIT_POINTS or len(surviving_tracks) < _MIN_TRACKS:
        return list(samples)
    return trimmed


def _start_timestamps_for_model(
    solved_model: _PathModelSolution,
    samples: Sequence[_ProjectedPathSample],
) -> list[float]:
    return list(_track_start_timestamps_for_model(solved_model, samples).values())


def _select_best_path_model(
    samples: Sequence[_ProjectedPathSample],
    track_count: int,
    preferred_policy_name: Optional[str] = _RUNTIME_PATH_POLICY,
) -> Optional[tuple[_PathModelSolution, list[_ProjectedPathSample]]]:
    candidates: list[tuple[_PathModelSolution, list[_ProjectedPathSample]]] = []
    for policy_name in ("policy_a", "policy_b"):
        filtered_samples = _filter_samples_for_policy(samples, policy_name)
        solved_model = _solve_linear_path_model(filtered_samples, track_count, policy_name)
        if solved_model is None:
            continue
        track_weight_scales = _estimate_track_weight_scales(filtered_samples, solved_model)
        if track_weight_scales:
            solved_model = _solve_linear_path_model(
                filtered_samples,
                track_count,
                policy_name,
                track_weight_scales=track_weight_scales,
            )
            if solved_model is None:
                continue
        refined_samples = _trim_temporal_outliers(filtered_samples, solved_model)
        if refined_samples != list(filtered_samples):
            track_weight_scales = _estimate_track_weight_scales(refined_samples, solved_model)
            solved_model = _solve_linear_path_model(
                refined_samples,
                track_count,
                policy_name,
                track_weight_scales=track_weight_scales or None,
            )
            if solved_model is None:
                continue
        candidates.append((solved_model, list(refined_samples)))

    policy_c_samples = _filter_samples_for_policy(samples, "policy_c")
    quadratic_model = _solve_quadratic_path_model(policy_c_samples, track_count)
    if quadratic_model is not None:
        track_weight_scales = _estimate_track_weight_scales(policy_c_samples, quadratic_model)
        if track_weight_scales:
            quadratic_model = _solve_quadratic_path_model(
                policy_c_samples,
                track_count,
                track_weight_scales=track_weight_scales,
            )
        if quadratic_model is not None:
            refined_samples = _trim_temporal_outliers(policy_c_samples, quadratic_model)
            if refined_samples != list(policy_c_samples):
                track_weight_scales = _estimate_track_weight_scales(refined_samples, quadratic_model)
                quadratic_model = _solve_quadratic_path_model(
                    refined_samples,
                    track_count,
                    track_weight_scales=track_weight_scales or None,
                )
            if quadratic_model is not None:
                candidates.append((quadratic_model, list(refined_samples)))

    if not candidates:
        return None

    def candidate_key(item: tuple[_PathModelSolution, list[_ProjectedPathSample]]) -> tuple[float, float, float, int]:
        solved_model, candidate_samples = item
        late_sample_count = sum(1 for sample in candidate_samples if sample.series_fraction >= _LATE_SERIES_START)
        timing_penalty = max(0.0, solved_model.timing_spread_seconds - _TIMING_TRACK_SOFT_OFFSET_SECONDS)
        acceleration_penalty = 0.0
        if solved_model.policy_name == "policy_c":
            acceleration_penalty = max(0.0, solved_model.acceleration_kms2) * 0.45
            acceleration_penalty += max(0.0, abs(solved_model.acceleration_kms2) - 0.75) * 0.08
        return (
            solved_model.scalar_residual_median_km + (solved_model.scalar_residual_max_km * 0.2),
            timing_penalty,
            acceleration_penalty,
            late_sample_count,
        )

    candidates.sort(key=candidate_key)
    if preferred_policy_name not in {None, _AUTO_PATH_POLICY}:
        for solved_model, candidate_samples in candidates:
            if solved_model.policy_name != preferred_policy_name:
                continue
            return solved_model, candidate_samples
    return candidates[0]


def _fit_path_state(
    event: Event,
    tracks: Sequence[_ObservationTrack],
    preferred_policy_name: Optional[str] = _RUNTIME_PATH_POLICY,
) -> Optional[tuple[np.ndarray, np.ndarray, datetime, _PathFitDiagnostics]]:
    return _fit_track_geometry_state(event, tracks, preferred_policy_name)


def _fit_observed_state(
    event: Event,
    tracks: Sequence[_ObservationTrack],
) -> Optional[tuple[np.ndarray, np.ndarray, datetime, _PathFitDiagnostics]]:
    return _fit_track_geometry_state(event, tracks, "reserve")


def _earth_heliocentric_state(when: datetime) -> tuple[np.ndarray, np.ndarray]:
    time = Time(_utc_datetime(when))
    with solar_system_ephemeris.set("builtin"):
        earth_pos, earth_vel = get_body_barycentric_posvel("earth", time)
        sun_pos, sun_vel = get_body_barycentric_posvel("sun", time)
    position = (earth_pos.xyz - sun_pos.xyz).to_value(u.km)
    velocity = (earth_vel.xyz - sun_vel.xyz).to_value(u.km / u.s)
    return (np.array(position, dtype=float), np.array(velocity, dtype=float))


def _incoming_hyperbolic_excess(position_km: np.ndarray, velocity_kms: np.ndarray) -> Optional[np.ndarray]:
    candidates = _incoming_hyperbolic_excess_candidates(position_km, velocity_kms)
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: _dot(candidate, velocity_kms))


def _incoming_hyperbolic_excess_candidates(position_km: np.ndarray, velocity_kms: np.ndarray) -> list[np.ndarray]:
    radius_km = _vector_length(position_km)
    speed_kms = _vector_length(velocity_kms)
    if radius_km == 0 or speed_kms == 0:
        return []
    specific_energy = (speed_kms * speed_kms / 2.0) - (_EARTH_MU_KM_S2 / radius_km)
    if specific_energy <= 0:
        return []

    h_vec = _cross(position_km, velocity_kms)
    h_norm = _vector_length(h_vec)
    if h_norm == 0:
        return []
    e_vec = ((_cross(velocity_kms, h_vec) / _EARTH_MU_KM_S2) - (position_km / radius_km))
    eccentricity = _vector_length(e_vec)
    if eccentricity <= 1.0:
        return []

    p_hat = _unit(e_vec)
    h_hat = _unit(h_vec)
    if p_hat is None or h_hat is None:
        return []
    q_hat = _unit(_cross(h_hat, p_hat))
    if q_hat is None:
        return []

    v_inf_mag = math.sqrt(2.0 * specific_energy)
    f_inf = math.acos(-1.0 / eccentricity)
    candidates = []
    for branch in (-f_inf, f_inf):
        velocity = (-math.sin(branch) * p_hat) + ((eccentricity + math.cos(branch)) * q_hat)
        unit_velocity = _unit(velocity)
        if unit_velocity is not None:
            candidates.append(unit_velocity * v_inf_mag)
    return sorted(candidates, key=lambda candidate: _dot(candidate, velocity_kms), reverse=True)


def _candidate_variants_from_state(
    observed_state: tuple,
) -> list[_ObservationOrbitCandidate]:
    diagnostics = None
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

    earth_position_km, earth_velocity_kms = _earth_heliocentric_state(when)
    heliocentric_position_km = _equatorial_to_ecliptic(earth_position_km + position_gcrs_km)
    candidates: list[_ObservationOrbitCandidate] = []
    for v_inf_kms in _incoming_hyperbolic_excess_candidates(position_gcrs_km, observed_velocity_gcrs_kms):
        heliocentric_velocity_kms = _equatorial_to_ecliptic(earth_velocity_kms + v_inf_kms)
        candidates.append(
            _ObservationOrbitCandidate(
                payload=_state_to_payload(heliocentric_position_km, heliocentric_velocity_kms, when),
                diagnostics=diagnostics,
            )
        )
    return candidates


def _candidate_from_state(
    observed_state: tuple,
) -> Optional[_ObservationOrbitCandidate]:
    candidates = _candidate_variants_from_state(observed_state)
    return candidates[0] if candidates else None


def _iter_state_variants(observed_state: tuple) -> list[tuple]:
    variants = [observed_state]
    if len(observed_state) == 4:
        position_ecef_km, observed_velocity_kms, when, diagnostics = observed_state
        reversed_state = (position_ecef_km, -observed_velocity_kms, when, diagnostics)
    else:
        position_ecef_km, observed_velocity_kms, when = observed_state
        reversed_state = (position_ecef_km, -observed_velocity_kms, when)
    variants.append(reversed_state)
    return variants


def _iter_observation_candidates(
    event: Event,
    observations: Iterable[ObservationCamData],
    path_policy: Optional[str] = _RUNTIME_PATH_POLICY,
) -> list[_ObservationOrbitCandidate]:
    if not event.camera_confirmed or event.date is None:
        return []
    tracks = [track for track in (_build_track(record) for record in observations) if track is not None]
    if len(tracks) < _MIN_TRACKS:
        return []

    if path_policy not in {None, _AUTO_PATH_POLICY}:
        policy_order = [path_policy]
    else:
        policy_order = ["policy_a", "policy_b", "policy_c", "reserve"]

    candidates: list[_ObservationOrbitCandidate] = []
    seen_payloads: set[tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[float], Optional[str]]] = set()
    for policy_name in policy_order:
        observed_state = (
            _fit_observed_state(event, tracks)
            if policy_name == "reserve"
            else _fit_path_state(event, tracks, preferred_policy_name=policy_name)
        )
        if observed_state is None:
            continue
        for state_variant in _iter_state_variants(observed_state):
            for candidate in _candidate_variants_from_state(state_variant):
                payload_signature = (
                    candidate.payload.get("perihelion_distance_au"),
                    candidate.payload.get("eccentricity"),
                    candidate.payload.get("inclination_deg"),
                    candidate.payload.get("ascending_node_deg"),
                    candidate.payload.get("argument_of_perihelion_deg"),
                    candidate.payload.get("mean_anomaly_deg"),
                    candidate.payload.get("epoch"),
                )
                if payload_signature in seen_payloads:
                    continue
                seen_payloads.add(payload_signature)
                candidates.append(candidate)
    return candidates


def _solve_observation_candidate(
    event: Event,
    observations: Iterable[ObservationCamData],
    path_policy: Optional[str] = _RUNTIME_PATH_POLICY,
) -> Optional[_ObservationOrbitCandidate]:
    candidates = _iter_observation_candidates(event, observations, path_policy=path_policy)
    fallback_payload = _legacy_stat_orbit(event)
    for candidate in candidates:
        if _is_reasonable_observed_payload(
            candidate.payload,
            fallback_payload,
            candidate.diagnostics,
        ):
            return candidate
    return candidates[0] if candidates else None


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
    *,
    path_policy: Optional[str] = _RUNTIME_PATH_POLICY,
) -> dict:
    observation_records = tuple(observations)
    fallback_payload = fallback_factory(event) if fallback_factory is not None else _legacy_stat_orbit(event)
    if path_policy in {None, _AUTO_PATH_POLICY}:
        candidates = [
            candidate
            for candidate in (
                _solve_observation_candidate(event, observation_records, path_policy=policy_name)
                for policy_name in ("policy_a", "policy_b", "policy_c", "reserve")
            )
            if candidate is not None
        ]
        return _runtime_payload_from_candidates(candidates, fallback_payload)
    candidate = _solve_observation_candidate(event, observation_records, path_policy=path_policy)
    return _runtime_payload_from_candidate(candidate, fallback_payload)
