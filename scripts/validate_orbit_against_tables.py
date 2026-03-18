from __future__ import annotations

import argparse
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi_app.app.models import Event, ObservationCamData, ObservationTrailPoint
from fastapi_app.app.services.file_mapper import FileToObjectMapper
from fastapi_app.app.utils.orbit_solver import (
    _MAX_OBSERVED_MAX_RESIDUAL_KM,
    _MAX_OBSERVED_MEDIAN_RESIDUAL_KM,
    _MIN_FIT_POINTS,
    _MIN_TRACKS,
    _ObservationOrbitCandidate,
    _legacy_stat_orbit,
    _runtime_payload_from_candidate,
    _solve_observation_candidate,
    _wrapped_angle_delta,
    build_orbit_payload,
)

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_ROW_RE = re.compile(r"<tr><td>([^<]+):</td><td>\s*([^<]+)</td></tr>")
_DATE_DIR_RE = re.compile(r"^\d{8}$")


@dataclass(frozen=True)
class OrbitTruth:
    perihelion_distance_au: float
    eccentricity: float
    inclination_deg: float
    ascending_node_deg: float
    argument_of_perihelion_deg: float
    mean_anomaly_deg: float


@dataclass(frozen=True)
class OrbitErrors:
    q: float
    e: float
    i: float
    node: float
    argp: float
    mean_anomaly: float

    def weighted_score(self) -> float:
        return (
            (self.q / 0.003)
            + (self.e / 0.05)
            + self.i
            + (self.node / 0.3)
            + self.argp
            + (self.mean_anomaly / 3.0)
        )


@dataclass(frozen=True)
class CaseResult:
    track_speed_source: str
    event_dir: Path
    observation_count: int
    usable_station_count: int
    raw_point_count: int
    observed_candidate: Optional[_ObservationOrbitCandidate]
    policy_candidates: dict[str, Optional[_ObservationOrbitCandidate]]
    policy_errors: dict[str, Optional[OrbitErrors]]
    fallback_payload: dict
    runtime_payload: dict
    truth: OrbitTruth
    observed_errors: Optional[OrbitErrors]
    fallback_errors: Optional[OrbitErrors]
    runtime_errors: Optional[OrbitErrors]


@dataclass(frozen=True)
class SkippedCase:
    event_dir: Path
    reason: str
    detail: str


@dataclass(frozen=True)
class ValidationRun:
    results: list[CaseResult]
    skipped: list[SkippedCase]
    found_total: int
    timings: list["CaseTiming"]
    worker_count: int
    wall_seconds: float


@dataclass(frozen=True)
class PolicyEvaluation:
    policy: str
    title: str
    results: list[CaseResult]
    observed_built: int
    observed_rejected: int
    observed_full_accepted: int
    observed_partial_used: int
    observed_any_used: int
    runtime_better: int
    runtime_worse_or_equal: int
    reused_mean_epoch: int


@dataclass(frozen=True)
class CaseTiming:
    event_dir: Path
    tables_seconds: float
    load_seconds: float
    observed_seconds: float
    fallback_seconds: float
    runtime_seconds: float
    total_seconds: float


_POLICY_TITLES = {
    "A": "grunnmodell med asymmetrisk vekting",
    "B": "A + sterkere kutt i sene punkt",
    "C": "B + svak bremsing langs banen",
}
_POLICY_PATH_NAMES = {"A": "policy_a", "B": "policy_b", "C": "policy_c"}


def _coerce_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _NUMBER_RE.search(str(value).replace(",", "."))
    return float(match.group(0)) if match else None


def _parse_tables(path: Path) -> Optional[OrbitTruth]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows = {key.strip(): value.strip() for key, value in _ROW_RE.findall(text)}
    required = (
        "Perihelavstand",
        "Eksentrisitet",
        "Inklinasjon",
        "Knutelengde",
        "Perihelargument",
        "Midlere anomali",
    )
    if not all(key in rows for key in required):
        return None
    return OrbitTruth(
        perihelion_distance_au=float(_coerce_float(rows["Perihelavstand"])),
        eccentricity=float(_coerce_float(rows["Eksentrisitet"])),
        inclination_deg=float(_coerce_float(rows["Inklinasjon"])),
        ascending_node_deg=float(_coerce_float(rows["Knutelengde"])),
        argument_of_perihelion_deg=float(_coerce_float(rows["Perihelargument"])),
        mean_anomaly_deg=float(_coerce_float(rows["Midlere anomali"])),
    )


def _event_from_record(record: dict) -> Event:
    payload = dict(record)
    numeric_fields = (
        "track_startheight",
        "track_endheight",
        "track_groundtrack",
        "track_course",
        "track_incidence",
        "track_speed",
        "fit_error",
        "fit_quality",
        "radiant_ra",
        "radiant_dec",
        "radiant_ecl_long",
        "radiant_ecl_lat",
        "timestamp",
        "track_startlong",
        "track_startlat",
        "track_endlong",
        "track_endlat",
    )
    for field_name in numeric_fields:
        payload[field_name] = _coerce_float(payload.get(field_name))
    return Event(**payload)


def _observation_from_record(record) -> ObservationCamData:
    values = dict(record.values)
    for field_name in ("summary_latitude", "summary_longitude", "summary_elevation"):
        values[field_name] = _coerce_float(values.get(field_name))
    observation = ObservationCamData(
        **{key: value for key, value in values.items() if hasattr(ObservationCamData, key)}
    )
    observation.trail_points = [
        ObservationTrailPoint(
            frame_index=point.frame_index,
            pixel_x=point.pixel_x,
            pixel_y=point.pixel_y,
            event_timestamp=point.event_timestamp,
            coord_long=point.coord_long,
            coord_lat=point.coord_lat,
            ams_coord_long=point.ams_coord_long,
            ams_coord_lat=point.ams_coord_lat,
            gnomonic_x=point.gnomonic_x,
            gnomonic_y=point.gnomonic_y,
            brightness=point.brightness,
            dct=point.dct,
            size=point.size,
            frame_brightness=point.frame_brightness,
        )
        for point in record.trail_points
    ]
    return observation


def _load_event_case(data_root: Path, event_dir: Path) -> tuple[Event, list[ObservationCamData]]:
    date_string = event_dir.parent.name
    mapper = FileToObjectMapper(data_root, date_string, date_string)
    record = mapper._process_event_folder(date_string, event_dir.name, event_dir)
    if record is None:
        raise ValueError(f"Could not parse event folder {event_dir}")
    event = _event_from_record(record.event)
    observations = [_observation_from_record(item) for item in record.observations]
    return event, observations


def _errors_for(payload: Optional[dict], truth: OrbitTruth) -> Optional[OrbitErrors]:
    if payload is None:
        return None
    required = (
        "perihelion_distance_au",
        "eccentricity",
        "inclination_deg",
        "ascending_node_deg",
        "argument_of_perihelion_deg",
        "mean_anomaly_deg",
    )
    if any(payload.get(key) is None for key in required):
        return None
    return OrbitErrors(
        q=abs(float(payload["perihelion_distance_au"]) - truth.perihelion_distance_au),
        e=abs(float(payload["eccentricity"]) - truth.eccentricity),
        i=abs(float(payload["inclination_deg"]) - truth.inclination_deg),
        node=_wrapped_angle_delta(float(payload["ascending_node_deg"]), truth.ascending_node_deg),
        argp=_wrapped_angle_delta(
            float(payload["argument_of_perihelion_deg"]),
            truth.argument_of_perihelion_deg,
        ),
        mean_anomaly=_wrapped_angle_delta(
            float(payload["mean_anomaly_deg"]),
            truth.mean_anomaly_deg,
        ),
    )


def _normalize_policy_key(policy: str) -> str:
    return policy.strip().upper()


def _parse_policy_list(raw_value: Optional[str]) -> list[str]:
    if not raw_value:
        return []
    selected: list[str] = []
    seen: set[str] = set()
    for part in raw_value.split(","):
        policy = _normalize_policy_key(part)
        if not policy:
            continue
        if policy not in _POLICY_TITLES:
            raise ValueError(f"Ukjent policy {policy!r}. Velg en av: A, B, C.")
        if policy in seen:
            continue
        seen.add(policy)
        selected.append(policy)
    return selected


def _truth_is_physically_wild(truth: OrbitTruth) -> bool:
    return not (
        0.0 < truth.perihelion_distance_au < 2.0
        and 0.0 < truth.eccentricity < 1.5
        and 0.0 <= truth.inclination_deg <= 180.0
        and abs(truth.mean_anomaly_deg) <= 720.0
    )


def _candidate_has_full_orbit(candidate: Optional[_ObservationOrbitCandidate]) -> bool:
    if candidate is None:
        return False
    payload = candidate.payload
    required_keys = (
        "perihelion_distance_au",
        "eccentricity",
        "inclination_deg",
        "ascending_node_deg",
        "argument_of_perihelion_deg",
        "mean_anomaly_deg",
    )
    return payload is not None and all(payload.get(key) is not None for key in required_keys)


def _payload_is_physically_wild(payload: dict) -> bool:
    return not (
        0.0 < float(payload["perihelion_distance_au"]) < 2.0
        and 0.0 < float(payload["eccentricity"]) < 1.5
        and 0.0 <= float(payload["inclination_deg"]) <= 180.0
        and abs(float(payload["mean_anomaly_deg"])) <= 720.0
    )


def _observed_candidate_is_usable(candidate: Optional[_ObservationOrbitCandidate]) -> bool:
    if candidate is None or candidate.diagnostics is None:
        return False
    diagnostics = candidate.diagnostics
    payload = candidate.payload
    required_keys = (
        "perihelion_distance_au",
        "eccentricity",
        "inclination_deg",
        "ascending_node_deg",
        "argument_of_perihelion_deg",
        "mean_anomaly_deg",
    )
    if any(payload.get(key) is None for key in required_keys):
        return False
    if diagnostics.track_count < _MIN_TRACKS or diagnostics.fit_point_count < _MIN_FIT_POINTS:
        return False
    if diagnostics.median_residual_km > _MAX_OBSERVED_MEDIAN_RESIDUAL_KM:
        return False
    if diagnostics.max_residual_km > _MAX_OBSERVED_MAX_RESIDUAL_KM:
        return False
    if not (0.0 < float(payload["perihelion_distance_au"]) < 2.0):
        return False
    if not (0.0 < float(payload["eccentricity"]) < 1.5):
        return False
    if not (0.0 <= float(payload["inclination_deg"]) <= 180.0):
        return False
    if abs(float(payload["mean_anomaly_deg"])) > 720.0:
        return False
    return True


def _policy_payload_for_result(result: CaseResult, policy: str) -> dict:
    selected = _normalize_policy_key(policy)
    candidate = result.policy_candidates.get(selected)
    return _runtime_payload_from_candidate(candidate, result.fallback_payload)


def _evaluate_policy(results: list[CaseResult], policy: str) -> PolicyEvaluation:
    selected = _normalize_policy_key(policy)
    title = _POLICY_TITLES[selected]
    policy_cases: list[CaseResult] = []
    for item in results:
        payload = _policy_payload_for_result(item, selected)
        policy_cases.append(
            CaseResult(
                track_speed_source=item.track_speed_source,
                event_dir=item.event_dir,
                observation_count=item.observation_count,
                usable_station_count=item.usable_station_count,
                raw_point_count=item.raw_point_count,
                observed_candidate=item.observed_candidate,
                policy_candidates=item.policy_candidates,
                policy_errors=item.policy_errors,
                fallback_payload=item.fallback_payload,
                runtime_payload=payload,
                truth=item.truth,
                observed_errors=item.policy_errors.get(selected),
                fallback_errors=item.fallback_errors,
                runtime_errors=_errors_for(payload, item.truth),
            )
        )
    observed_built = sum(1 for item in results if item.policy_candidates.get(selected) is not None)
    observed_partial_used = sum(1 for item in policy_cases if _runtime_reused_fallback_mean_epoch(item))
    observed_full_accepted = sum(
        1
        for item in policy_cases
        if _runtime_uses_observed_geometry(item) and not _runtime_reused_fallback_mean_epoch(item)
    )
    observed_any_used = observed_full_accepted + observed_partial_used
    runtime_better = sum(
        1
        for item in policy_cases
        if item.runtime_errors is not None
        and item.fallback_errors is not None
        and item.runtime_errors.weighted_score() < item.fallback_errors.weighted_score()
    )
    runtime_worse_or_equal = sum(
        1
        for item in policy_cases
        if item.runtime_errors is not None
        and item.fallback_errors is not None
        and item.runtime_errors.weighted_score() >= item.fallback_errors.weighted_score()
    )
    observed_rejected = observed_built - observed_full_accepted
    reused_mean_epoch = observed_partial_used
    return PolicyEvaluation(
        policy=selected,
        title=title,
        results=policy_cases,
        observed_built=observed_built,
        observed_rejected=observed_rejected,
        observed_full_accepted=observed_full_accepted,
        observed_partial_used=observed_partial_used,
        observed_any_used=observed_any_used,
        runtime_better=runtime_better,
        runtime_worse_or_equal=runtime_worse_or_equal,
        reused_mean_epoch=reused_mean_epoch,
    )


def _classify_bad_case(result: CaseResult) -> tuple[str, str]:
    observed = result.observed_candidate
    if observed is None:
        return (
            "for få gode punkt",
            "Det ble ikke bygget en egen bane fra punktdataene. Da må API-et bruke den gamle banen.",
        )

    diagnostics = observed.diagnostics
    if diagnostics is None:
        return (
            "tidslinje ser usikker ut",
            "Det finnes en kandidat, men vi mangler nok sporstatistikk til å stole på den.",
        )

    if diagnostics.track_count < _MIN_TRACKS or diagnostics.fit_point_count < _MIN_FIT_POINTS:
        return (
            "for få gode punkt",
            "For få kameraer eller for få brukbare punkt gjør banen for svak.",
        )

    if (
        diagnostics.max_residual_km > max(0.5, diagnostics.median_residual_km * 3.0)
        and diagnostics.max_residual_km > _MAX_OBSERVED_MAX_RESIDUAL_KM
    ):
        return (
            "store avvik i endepunkt",
            "Noen få punkt ligger mye dårligere enn resten. Det ser ut som støy i start eller slutt av sporet.",
        )

    if (
        diagnostics.median_residual_km > _MAX_OBSERVED_MEDIAN_RESIDUAL_KM
        or diagnostics.max_residual_km > _MAX_OBSERVED_MAX_RESIDUAL_KM
    ):
        return (
            "høy residual i hele serien",
            "Mange punkt passer for dårlig til banen. Det tyder på at hele sporserien er for urolig.",
        )

    runtime = result.runtime_errors
    fallback = result.fallback_errors
    if runtime is None or fallback is None:
        return (
            "tidslinje ser usikker ut",
            "Vi mangler nok tall til å sammenligne den nye banen skikkelig mot den gamle banen.",
        )

    if diagnostics.track_count >= 3 and (diagnostics.fit_point_count / diagnostics.track_count) < 8:
        return (
            "kameraer ser ulike segmenter",
            "Kameraene ser trolig ulike deler av løpet. Det gir svak overlapp mellom sporene.",
        )

    speed_source = str(result.track_speed_source or "").lower()
    if speed_source in {"average", "midpoint", "mean"} and (
        runtime.q > fallback.q or runtime.e > fallback.e
    ):
        return (
            "tidslinje ser usikker ut",
            "Grunnfarten ser ut til å komme fra en svak eller gjennomsnittlig kilde. Da blir tidslinjen fort skjev.",
        )

    mean_anomaly_gap = _wrapped_angle_delta(
        float(result.runtime_payload.get("mean_anomaly_deg") or 0.0),
        float(result.fallback_payload.get("mean_anomaly_deg") or 0.0),
    )
    other_gaps = max(runtime.q - fallback.q, runtime.e - fallback.e, runtime.i - fallback.i)
    if mean_anomaly_gap > 8.0 and other_gaps < 0.02:
        return (
            "mean anomaly / epoch driver",
            "Selve baneformen er nær, men midlere anomali eller epoke driver fortsatt for langt.",
        )

    return (
        "tidslinje ser usikker ut",
        "Vi ser ikke én klar feiltype. Dette ser mer ut som en blanding av små tids- og punktfeil.",
    )


def _iter_event_dirs(data_root: Path, date_from: Optional[str], date_to: Optional[str]) -> Iterable[Path]:
    lower_bound = date_from or "00000000"
    upper_bound = date_to or "99999999"
    for date_dir in sorted(
        entry for entry in data_root.iterdir() if entry.is_dir() and _DATE_DIR_RE.match(entry.name)
    ):
        if date_dir.name < lower_bound or date_dir.name > upper_bound:
            continue
        for event_dir in sorted(entry for entry in date_dir.iterdir() if entry.is_dir()):
            yield event_dir


def _process_event_dir(data_root: str, event_dir: str) -> tuple[Optional[CaseResult], Optional[SkippedCase], CaseTiming]:
    root = Path(data_root)
    case_dir = Path(event_dir)
    started = time.perf_counter()
    tables_seconds = 0.0
    load_seconds = 0.0
    observed_seconds = 0.0
    fallback_seconds = 0.0
    runtime_seconds = 0.0

    tables_started = time.perf_counter()
    tables_path = case_dir / "tables.html"
    if not tables_path.exists():
        tables_seconds = time.perf_counter() - tables_started
        return (
            None,
            SkippedCase(
                event_dir=case_dir,
                reason="mangler tables.html",
                detail="Det finnes ingen publisert tabellfil i denne mappen.",
            ),
            CaseTiming(
                event_dir=case_dir,
                tables_seconds=tables_seconds,
                load_seconds=load_seconds,
                observed_seconds=observed_seconds,
                fallback_seconds=fallback_seconds,
                runtime_seconds=runtime_seconds,
                total_seconds=time.perf_counter() - started,
            ),
        )
    truth = _parse_tables(tables_path)
    tables_seconds = time.perf_counter() - tables_started
    if truth is None:
        return (
            None,
            SkippedCase(
                event_dir=case_dir,
                reason="kan ikke lese tables.html",
                detail="Tabellfila mangler feltene som trengs for sammenligning.",
            ),
            CaseTiming(
                event_dir=case_dir,
                tables_seconds=tables_seconds,
                load_seconds=load_seconds,
                observed_seconds=observed_seconds,
                fallback_seconds=fallback_seconds,
                runtime_seconds=runtime_seconds,
                total_seconds=time.perf_counter() - started,
            ),
        )

    load_started = time.perf_counter()
    try:
        event, observations = _load_event_case(root, case_dir)
    except Exception as exc:
        load_seconds = time.perf_counter() - load_started
        return (
            None,
            SkippedCase(
                event_dir=case_dir,
                reason="kan ikke lese event-data",
                detail=str(exc),
            ),
            CaseTiming(
                event_dir=case_dir,
                tables_seconds=tables_seconds,
                load_seconds=load_seconds,
                observed_seconds=observed_seconds,
                fallback_seconds=fallback_seconds,
                runtime_seconds=runtime_seconds,
                total_seconds=time.perf_counter() - started,
            ),
        )
    load_seconds = time.perf_counter() - load_started

    observed_started = time.perf_counter()
    policy_candidates = {
        policy_key: _solve_observation_candidate(
            event,
            observations,
            path_policy=policy_path_name,
        )
        for policy_key, policy_path_name in _POLICY_PATH_NAMES.items()
    }
    observed_seconds = time.perf_counter() - observed_started

    policy_errors = {
        policy_key: _errors_for(
            candidate.payload if candidate is not None else None,
            truth,
        )
        for policy_key, candidate in policy_candidates.items()
    }
    observed_candidate = policy_candidates.get("A")

    fallback_started = time.perf_counter()
    fallback_payload = _legacy_stat_orbit(event)
    fallback_seconds = time.perf_counter() - fallback_started

    runtime_started = time.perf_counter()
    runtime_payload = build_orbit_payload(
        event,
        observations,
        fallback_factory=_legacy_stat_orbit,
    )
    runtime_seconds = time.perf_counter() - runtime_started
    observation_count = len(observations)
    usable_station_count = sum(1 for observation in observations if len(observation.trail_points) >= 2)
    raw_point_count = sum(len(observation.trail_points) for observation in observations)

    result = CaseResult(
        track_speed_source=str(getattr(event, "track_speed_source", "") or ""),
        event_dir=case_dir,
        observation_count=observation_count,
        usable_station_count=usable_station_count,
        raw_point_count=raw_point_count,
        observed_candidate=observed_candidate,
        policy_candidates=policy_candidates,
        policy_errors=policy_errors,
        fallback_payload=fallback_payload,
        runtime_payload=runtime_payload,
        truth=truth,
        observed_errors=policy_errors["A"],
        fallback_errors=_errors_for(fallback_payload, truth),
        runtime_errors=_errors_for(runtime_payload, truth),
    )
    timing = CaseTiming(
        event_dir=case_dir,
        tables_seconds=tables_seconds,
        load_seconds=load_seconds,
        observed_seconds=observed_seconds,
        fallback_seconds=fallback_seconds,
        runtime_seconds=runtime_seconds,
        total_seconds=time.perf_counter() - started,
    )
    return result, None, timing


def _collect_case_results(
    data_root: Path,
    date_from: Optional[str],
    date_to: Optional[str],
    limit: Optional[int],
    workers: int = 1,
) -> ValidationRun:
    if limit is not None and workers > 1:
        workers = 1
    results: list[CaseResult] = []
    skipped: list[SkippedCase] = []
    timings: list[CaseTiming] = []
    event_dirs = list(_iter_event_dirs(data_root, date_from, date_to))
    found_total = len(event_dirs)
    started = time.perf_counter()

    if workers <= 1:
        for event_dir in event_dirs:
            result, skipped_case, timing = _process_event_dir(str(data_root), str(event_dir))
            timings.append(timing)
            if result is not None:
                results.append(result)
                if limit is not None and len(results) >= limit:
                    break
            elif skipped_case is not None:
                skipped.append(skipped_case)
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for result, skipped_case, timing in executor.map(
                _process_event_dir,
                (str(data_root) for _ in event_dirs),
                (str(event_dir) for event_dir in event_dirs),
            ):
                timings.append(timing)
                if result is not None and (limit is None or len(results) < limit):
                    results.append(result)
                elif skipped_case is not None:
                    skipped.append(skipped_case)
    return ValidationRun(
        results=results,
        skipped=skipped,
        found_total=found_total,
        timings=timings,
        worker_count=workers,
        wall_seconds=time.perf_counter() - started,
    )


def _median_summary(results: list[CaseResult], attribute_name: str) -> Optional[str]:
    errors = [
        getattr(result, attribute_name)
        for result in results
        if getattr(result, attribute_name) is not None
    ]
    if not errors:
        return None
    return (
        f"perihelavstand (q)={median(item.q for item in errors):.3f} AU, "
        f"eksentrisitet (e)={median(item.e for item in errors):.3f}, "
        f"inklinasjon (i)={median(item.i for item in errors):.3f} grader, "
        f"knutelengde={median(item.node for item in errors):.3f} grader, "
        f"perihelargument={median(item.argp for item in errors):.3f} grader, "
        f"midlere anomali={median(item.mean_anomaly for item in errors):.3f} grader"
    )


def _runtime_uses_observed_geometry(result: CaseResult) -> bool:
    return result.runtime_payload.get("perihelion_distance_au") != result.fallback_payload.get("perihelion_distance_au")


def _runtime_reused_fallback_mean_epoch(result: CaseResult) -> bool:
    return (
        result.observed_candidate is not None
        and result.runtime_payload.get("mean_anomaly_deg") == result.fallback_payload.get("mean_anomaly_deg")
        and result.runtime_payload.get("epoch") == result.fallback_payload.get("epoch")
        and _runtime_uses_observed_geometry(result)
    )


_FUNNEL_STAGES = (
    (
        "ingen brukbar stasjonsbane",
        "no usable station track",
    ),
    (
        "færre enn to brukbare stasjoner",
        "fewer than two usable stations",
    ),
    (
        "for mange punkt falt bort før tilpassing",
        "too many points dropped before fit",
    ),
    (
        "fart eller retning kunne ikke løses",
        "speed or direction could not be solved",
    ),
    (
        "heliosentrisk bane kunne ikke løses",
        "heliocentric orbit could not be solved",
    ),
    (
        "full ny bane bygget, men fysisk vill",
        "full new orbit built, but physically wild",
    ),
    (
        "full ny bane bygget, men avvist før final API choice",
        "full new orbit built, but rejected before final API choice",
    ),
    (
        "full ny bane akseptert i API-et",
        "full new orbit accepted in API",
    ),
)


def _classify_funnel_stage(result: CaseResult, policy: str) -> str:
    candidate = result.policy_candidates.get(policy)
    if candidate is None:
        if result.raw_point_count == 0 or result.usable_station_count == 0:
            return "ingen brukbar stasjonsbane"
        if result.usable_station_count < 2:
            return "færre enn to brukbare stasjoner"
        if result.raw_point_count < _MIN_FIT_POINTS:
            return "for mange punkt falt bort før tilpassing"
        return "fart eller retning kunne ikke løses"

    if not _candidate_has_full_orbit(candidate):
        return "heliosentrisk bane kunne ikke løses"
    if _payload_is_physically_wild(candidate.payload):
        return "full ny bane bygget, men fysisk vill"
    if _runtime_uses_observed_geometry(result) and not _runtime_reused_fallback_mean_epoch(result):
        return "full ny bane akseptert i API-et"
    return "full ny bane bygget, men avvist før final API choice"


def _count_funnel_stages(results: list[CaseResult], policy: str) -> dict[str, int]:
    counts = {stage: 0 for stage, _ in _FUNNEL_STAGES}
    for result in results:
        stage = _classify_funnel_stage(result, policy)
        counts[stage] += 1
    return counts


def _print_funnel_block(title: str, results: list[CaseResult], policy: str) -> None:
    total = len(results)
    if total == 0:
        print(title)
        print("- ingen data / no data")
        return
    counts = _count_funnel_stages(results, policy)
    print(title)
    for stage, english in _FUNNEL_STAGES:
        count = counts.get(stage, 0)
        percentage = 100.0 * count / total
        suffix = ""
        if stage != "full ny bane akseptert i API-et":
            suffix = " — utelatt her / excluded here"
        print(f"- {stage} / {english}: {count} ({percentage:.1f}%)" + suffix)


def _print_skipped_cases(skipped: list[SkippedCase], count: int) -> None:
    if not skipped:
        print("Hendelser hoppet over: 0")
        return
    print(f"Hendelser hoppet over: {len(skipped)}")
    grouped: dict[str, int] = {}
    for item in skipped:
        grouped[item.reason] = grouped.get(item.reason, 0) + 1
    for reason, total in sorted(grouped.items(), key=lambda item: (-item[1], item[0])):
        print(f"- {reason}: {total}")
    print("Eksempler på hoppede hendelser:")
    for item in skipped[:count]:
        print(f"- {item.event_dir}: {item.reason} ({item.detail})")


def _print_cause_summary(results: list[CaseResult], count: int) -> None:
    bad_cases = [
        item
        for item in results
        if item.runtime_errors is not None
        and item.fallback_errors is not None
        and item.runtime_errors.weighted_score() >= item.fallback_errors.weighted_score()
    ]
    if not bad_cases:
        print("Hendelser der ny bane taper mot gammel bane: 0")
        return
    grouped: dict[str, int] = {}
    reasons: list[tuple[CaseResult, str, str]] = []
    for item in bad_cases:
        reason, detail = _classify_bad_case(item)
        grouped[reason] = grouped.get(reason, 0) + 1
        reasons.append((item, reason, detail))
    print(f"Hendelser der ny bane taper mot gammel bane: {len(bad_cases)}")
    print("Vanlige årsaker:")
    for reason, total in sorted(grouped.items(), key=lambda item: (-item[1], item[0])):
        print(f"- {reason}: {total}")
    print("Eksempler:")
    for item, reason, detail in reasons[:count]:
        print(f"- {item.event_dir}: {reason}")
        print(f"  {detail}")


def _print_worst_cases(results: list[CaseResult], count: int) -> None:
    sortable = [
        result
        for result in results
        if result.runtime_errors is not None and result.fallback_errors is not None
    ]
    sortable.sort(
        key=lambda item: item.runtime_errors.weighted_score() - item.fallback_errors.weighted_score(),
        reverse=True,
    )
    for item in sortable[:count]:
        reason, detail = _classify_bad_case(item)
        print(f"- {item.event_dir}")
        print(
            "  Ny bane-avvik:",
            f"perihelavstand={item.runtime_errors.q:.3f} AU,",
            f"eksentrisitet={item.runtime_errors.e:.3f},",
            f"inklinasjon={item.runtime_errors.i:.3f} grader,",
            f"knutelengde={item.runtime_errors.node:.3f} grader,",
            f"perihelargument={item.runtime_errors.argp:.3f} grader,",
            f"midlere anomali={item.runtime_errors.mean_anomaly:.3f} grader",
        )
        print(
            "  Gammel bane-avvik:",
            f"perihelavstand={item.fallback_errors.q:.3f} AU,",
            f"eksentrisitet={item.fallback_errors.e:.3f},",
            f"inklinasjon={item.fallback_errors.i:.3f} grader,",
            f"knutelengde={item.fallback_errors.node:.3f} grader,",
            f"perihelargument={item.fallback_errors.argp:.3f} grader,",
            f"midlere anomali={item.fallback_errors.mean_anomaly:.3f} grader",
        )
        print(f"  Vurdering: {reason}")
        print(f"  Forklaring: {detail}")
        if item.observed_candidate is not None and item.observed_candidate.diagnostics is not None:
            diagnostics = item.observed_candidate.diagnostics
            print(
                "  Sporgrunnlag:",
                f"kamera-spor brukt={diagnostics.track_count},",
                f"punkt brukt i tilpassing={diagnostics.fit_point_count},",
                f"typisk avvik fra banen={diagnostics.median_residual_km:.3f} km,",
                f"største avvik fra banen={diagnostics.max_residual_km:.3f} km",
            )
            print(
                "  Merk:",
                "Mange punkt er ikke nok i seg selv. Hvis mange punkt drar i samme feil retning, kan resultatet fortsatt bli skjevt.",
            )


def _print_policy_comparison(evaluations: list[PolicyEvaluation]) -> None:
    print("Sammenligning av policyer på de samme krysspeilede hendelsene:")
    for evaluation in evaluations:
        runtime_summary = _median_summary(evaluation.results, "runtime_errors") or "ingen median"
        print(
            f"- Policy {evaluation.policy} ({evaluation.title}):",
            f"ny bane-forsøk={evaluation.observed_built}/{len(evaluation.results)}",
            f"ingen ny bane={len(evaluation.results) - evaluation.observed_built}",
            f"fullt akseptert={evaluation.observed_full_accepted}",
            f"delvis brukt={evaluation.observed_partial_used}",
            f"avvist før final API choice={evaluation.observed_rejected}",
            f"bedre enn gammel bane={evaluation.runtime_better}",
            f"gammel bane bedre eller lik={evaluation.runtime_worse_or_equal}",
            f"delvis brukt i API-et={evaluation.reused_mean_epoch}",
            f"median runtime={runtime_summary}",
        )


def _print_funnel_overview(results: list[CaseResult], policy: str) -> None:
    total = len(results)
    wild_truth = sum(1 for item in results if _truth_is_physically_wild(item.truth))
    sane_results = [item for item in results if not _truth_is_physically_wild(item.truth)]
    attempted = sum(1 for item in results if item.policy_candidates.get(policy) is not None)
    print("Kort funnel / Short funnel:")
    print(f"- Sammenlignbare hendelser / Comparable events: {total} (100.0%)")
    print(
        "- Gamle publiserte tabeller som ser fysisk ville ut / "
        f"Old published tables that look physically wild: {wild_truth} "
        f"({(100.0 * wild_truth / total):.1f}%)"
    )
    print(
        "- Sammenlignbare hendelser uten fysisk ville publiserte tabeller / "
        f"Comparable events without physically wild published tables: {len(sane_results)} "
        f"({(100.0 * len(sane_results) / total):.1f}%)"
    )
    print(
        "- Nytt bane-forsøk på allerede krysspeilede hendelser / "
        f"New orbit attempt on already cross-station solved events: {attempted}/{total} "
        f"({(100.0 * attempted / total):.1f}%)"
    )
    print("")
    _print_funnel_block("Funnel / All comparable events:", results, policy)
    print("")
    _print_funnel_block(
        "Funnel uten fysisk ville publiserte tabeller / Funnel without physically wild published tables:",
        sane_results,
        policy,
    )


def _default_worker_count(profile: str) -> int:
    if profile != "final":
        return 1
    cpu_count = os.cpu_count() or 1
    return max(1, cpu_count - 1)


def _format_seconds(value: float) -> str:
    return f"{value:.2f} s"


def _print_timing_summary(run: ValidationRun, compared_count: int) -> None:
    if not run.timings:
        return
    tables_seconds = sum(item.tables_seconds for item in run.timings)
    load_seconds = sum(item.load_seconds for item in run.timings)
    observed_seconds = sum(item.observed_seconds for item in run.timings)
    fallback_seconds = sum(item.fallback_seconds for item in run.timings)
    runtime_seconds = sum(item.runtime_seconds for item in run.timings)
    print("Tidsbruk:")
    print(f"- veggtid for hele kjøringen: {_format_seconds(run.wall_seconds)}")
    print(f"- worker-prosesser: {run.worker_count}")
    print(
        "- sum per hendelse:",
        f"tables.html={_format_seconds(tables_seconds)},",
        f"innlesing={_format_seconds(load_seconds)},",
        f"ny bane={_format_seconds(observed_seconds)},",
        f"gammel bane={_format_seconds(fallback_seconds)},",
        f"API-valg={_format_seconds(runtime_seconds)}",
    )
    if compared_count > 0:
        print(
            "- snitt per sammenlignet hendelse:",
            f"tables.html={_format_seconds(tables_seconds / compared_count)},",
            f"innlesing={_format_seconds(load_seconds / compared_count)},",
            f"ny bane={_format_seconds(observed_seconds / compared_count)},",
            f"gammel bane={_format_seconds(fallback_seconds / compared_count)},",
            f"API-valg={_format_seconds(runtime_seconds / compared_count)}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sjekk orbit mot publiserte tables.html-filer og skriv en lesbar rapport.",
    )
    parser.add_argument(
        "--data-root",
        required=True,
        help="Mappe med publiserte YYYYMMDD/event-mapper.",
    )
    parser.add_argument("--date-from", help="Nedre datogrense i formatet YYYYMMDD.")
    parser.add_argument("--date-to", help="Øvre datogrense i formatet YYYYMMDD.")
    parser.add_argument(
        "--profile",
        choices=("dev", "final"),
        default="dev",
        help="Velg dev for korte prøvekjøringer eller final for full gjennomgang.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maks antall sammenlignede hendelser. Overstyrer profilen.",
    )
    parser.add_argument(
        "--show-worst",
        type=int,
        help="Hvor mange av de svakeste runtime-hendelsene som skal vises.",
    )
    parser.add_argument(
        "--policy",
        choices=tuple(_POLICY_TITLES.keys()),
        default="A",
        help="Hvilken policy som skal brukes i detaljrapporten. A er dagens runtime.",
    )
    parser.add_argument(
        "--compare-policies",
        default="A,B,C",
        help="Kommaseparert liste med policyer som skal sammenlignes i en kort oversikt.",
    )
    parser.add_argument(
        "--label",
        help="Valgfri etikett for denne kjøringen, for eksempel en iterasjon eller branch.",
    )
    parser.add_argument(
        "--technical",
        action="store_true",
        help="Skriv også en kort teknisk oppsummering til slutt.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Antall worker-prosesser for parallell kjøring. Standard er 1 i dev og nesten alle CPU-kjerner i final.",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    limit = args.limit
    if limit is None and args.profile == "dev":
        limit = 25
    workers = args.workers if args.workers is not None else _default_worker_count(args.profile)
    workers = max(1, workers)
    show_worst = args.show_worst
    if show_worst is None:
        show_worst = 3 if args.profile == "dev" else 10
    selected_policy = _normalize_policy_key(args.policy)
    try:
        compare_policies = _parse_policy_list(args.compare_policies)
    except ValueError as exc:
        parser.error(str(exc))
    if selected_policy not in compare_policies:
        compare_policies.insert(0, selected_policy)
    compare_policies = list(dict.fromkeys(compare_policies))

    print("Kjøring:", "liten utviklingskjøring" if args.profile == "dev" else "stor sluttevaluering")
    if limit is None:
        print("Omfang: alle treff i valgt datoperiode.")
    else:
        print(f"Omfang: de første {limit} sammenlignbare hendelsene i valgt datoperiode.")
    if args.label:
        print(f"Iterasjon: {args.label}")
    print(f"Policy i detaljrapport: {selected_policy} - {_POLICY_TITLES[selected_policy]}")
    print("Policyer i sammenligning:", ", ".join(compare_policies))
    print(f"Parallellitet: {workers} worker-prosesser")
    print(
        "Sammenligning: ny bane er banen fra punktdata. "
        "Den skal prøves på alle krysspeilede hendelser. "
        "Gammel bane er banen fra event-feltene. API-valg er det som faktisk ville blitt sendt ut."
    )
    print(
        "Når rapporten sier bedre eller dårligere, betyr det bare nærmere eller lenger fra tables.html. "
        "Små avvik er normalt. Større avvik kan være greit når den gamle publiserte løsningen selv ser klart feil ut. "
        "tables.html brukes som arbeidsfasit i denne sjekken, ikke som absolutt sannhet."
    )
    print(
        "Mål: På alle krysspeilede hendelser som allerede er løst i dagens løsning, "
        "skal den nye løseren også få prøve seg."
    )
    print(
        "Begreper: perihelavstand (q), eksentrisitet (e), inklinasjon (i), "
        "knutelengde, perihelargument og midlere anomali."
    )

    run = _collect_case_results(data_root, args.date_from, args.date_to, limit, workers=workers)
    results = run.results
    skipped = run.skipped
    if not results:
        print("Fant ingen hendelser som kunne sammenlignes.")
        _print_skipped_cases(skipped, 5)
        return 1

    policy_evaluations = [_evaluate_policy(results, policy) for policy in compare_policies]
    selected_eval = next(evaluation for evaluation in policy_evaluations if evaluation.policy == selected_policy)
    if len(policy_evaluations) > 1:
        _print_policy_comparison(policy_evaluations)

    observed_attempted = selected_eval.observed_built
    observed_rejected = selected_eval.observed_rejected
    observed_full_accepted = selected_eval.observed_full_accepted
    observed_partial_used = selected_eval.observed_partial_used
    observed_any_used = selected_eval.observed_any_used
    fallback_used = len(selected_eval.results) - observed_any_used
    runtime_better = selected_eval.runtime_better
    runtime_worse = selected_eval.runtime_worse_or_equal
    reused_mean_epoch = selected_eval.reused_mean_epoch

    print(f"Hendelser funnet i valgt periode: {run.found_total}")
    print(f"Hendelser sammenlignet: {len(selected_eval.results)}")
    print(
        "Nytt bane-forsøk på allerede krysspeilede hendelser: "
        f"{observed_attempted}/{len(selected_eval.results)}"
    )
    print(f"Ingen ny bane bygget: {len(selected_eval.results) - observed_attempted}")
    print(f"Ny bane bygget, men avvist før final API choice: {observed_rejected}")
    print(f"Ny bane fullt akseptert i API-et: {observed_full_accepted}")
    print(f"Ny bane delvis brukt i API-et (ny bane + gammel M/epoke): {observed_partial_used}")
    print(f"Gammel bane brukt i API-et: {fallback_used}")
    print(f"Ny bane nærmere tables.html enn gammel bane: {runtime_better}")
    print(f"Gammel bane bedre eller like nær tables.html: {runtime_worse}")
    print(
        "Ny bane beholdt geometri, men tok midlere anomali og epoke fra gammel bane: "
        f"{reused_mean_epoch}"
    )
    if args.profile == "final" and len(results) < 1000:
        print(
            "Advarsel: denne sluttevalueringen har under 1000 sammenlignede hendelser. "
            "Resultatet er nyttig, men mindre robust enn ønsket."
        )

    observed_summary = _median_summary(selected_eval.results, "observed_errors")
    fallback_summary = _median_summary(selected_eval.results, "fallback_errors")
    runtime_summary = _median_summary(selected_eval.results, "runtime_errors")
    if observed_summary:
        print(f"Medianfeil mot tables.html for ny bane: {observed_summary}")
    if fallback_summary:
        print(f"Medianfeil mot tables.html for gammel bane: {fallback_summary}")
    if runtime_summary:
        print(f"Medianfeil mot tables.html for API-valg: {runtime_summary}")
    _print_funnel_overview(selected_eval.results, selected_policy)
    _print_timing_summary(run, len(selected_eval.results))

    _print_skipped_cases(skipped, 5)
    _print_cause_summary(selected_eval.results, 5 if args.profile == "dev" else 10)

    if show_worst > 0:
        print("Hendelser der ny bane fortsatt ser svakest ut:")
        _print_worst_cases(selected_eval.results, show_worst)

    if args.technical:
        print("---")
        print("Teknisk kortformat:")
        print(
            f"policy={selected_policy} cases={len(selected_eval.results)} attempted={observed_attempted} "
            f"accepted={observed_full_accepted} partial={observed_partial_used} "
            f"rejected={observed_rejected} "
            f"runtime_better={runtime_better} "
            f"runtime_worse_or_equal={runtime_worse} "
            f"stabilized_M_epoch={reused_mean_epoch}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
