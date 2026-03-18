from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi_app.app.models import Event, ObservationCamData, ObservationTrailPoint
from fastapi_app.app.services.file_mapper import FileToObjectMapper
from fastapi_app.app.utils.orbit_solver import (
    _ObservationOrbitCandidate,
    _PathFitDiagnostics,
    _legacy_stat_orbit,
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
    event_dir: Path
    observed_candidate: Optional[_ObservationOrbitCandidate]
    fallback_payload: dict
    runtime_payload: dict
    truth: OrbitTruth
    observed_errors: Optional[OrbitErrors]
    fallback_errors: Optional[OrbitErrors]
    runtime_errors: Optional[OrbitErrors]


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


def _iter_event_dirs(data_root: Path, date_from: Optional[str], date_to: Optional[str]) -> Iterable[Path]:
    lower_bound = date_from or "00000000"
    upper_bound = date_to or "99999999"
    for date_dir in sorted(entry for entry in data_root.iterdir() if entry.is_dir() and _DATE_DIR_RE.match(entry.name)):
        if date_dir.name < lower_bound or date_dir.name > upper_bound:
            continue
        for event_dir in sorted(entry for entry in date_dir.iterdir() if entry.is_dir()):
            yield event_dir


def _collect_case_results(
    data_root: Path,
    date_from: Optional[str],
    date_to: Optional[str],
    limit: Optional[int],
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for event_dir in _iter_event_dirs(data_root, date_from, date_to):
        tables_path = event_dir / "tables.html"
        if not tables_path.exists():
            continue
        truth = _parse_tables(tables_path)
        if truth is None:
            continue
        event, observations = _load_event_case(data_root, event_dir)
        observed_candidate = _solve_observation_candidate(event, observations)
        fallback_payload = _legacy_stat_orbit(event)
        runtime_payload = build_orbit_payload(
            event,
            observations,
            fallback_factory=_legacy_stat_orbit,
        )
        results.append(
            CaseResult(
                event_dir=event_dir,
                observed_candidate=observed_candidate,
                fallback_payload=fallback_payload,
                runtime_payload=runtime_payload,
                truth=truth,
                observed_errors=_errors_for(
                    observed_candidate.payload if observed_candidate is not None else None,
                    truth,
                ),
                fallback_errors=_errors_for(fallback_payload, truth),
                runtime_errors=_errors_for(runtime_payload, truth),
            )
        )
        if limit is not None and len(results) >= limit:
            break
    return results


def _median_summary(results: list[CaseResult], attribute_name: str) -> Optional[str]:
    errors = [
        getattr(result, attribute_name)
        for result in results
        if getattr(result, attribute_name) is not None
    ]
    if not errors:
        return None
    return (
        f"q={median(item.q for item in errors):.3f} AU, "
        f"e={median(item.e for item in errors):.3f}, "
        f"i={median(item.i for item in errors):.3f} deg, "
        f"node={median(item.node for item in errors):.3f} deg, "
        f"argp={median(item.argp for item in errors):.3f} deg, "
        f"M={median(item.mean_anomaly for item in errors):.3f} deg"
    )


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
        print(f"- {item.event_dir}")
        print(
            "  runtime:",
            f"score={item.runtime_errors.weighted_score():.2f}",
            f"M={item.runtime_errors.mean_anomaly:.2f}",
            f"argp={item.runtime_errors.argp:.2f}",
            f"node={item.runtime_errors.node:.2f}",
        )
        print(
            "  fallback:",
            f"score={item.fallback_errors.weighted_score():.2f}",
            f"M={item.fallback_errors.mean_anomaly:.2f}",
            f"argp={item.fallback_errors.argp:.2f}",
            f"node={item.fallback_errors.node:.2f}",
        )
        if item.observed_candidate is not None and item.observed_candidate.diagnostics is not None:
            diagnostics = item.observed_candidate.diagnostics
            print(
                "  diagnostics:",
                f"tracks={diagnostics.track_count}",
                f"fit_points={diagnostics.fit_point_count}",
                f"median_residual={diagnostics.median_residual_km:.3f} km",
                f"max_residual={diagnostics.max_residual_km:.3f} km",
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate orbit payloads against published tables.html data.",
    )
    parser.add_argument(
        "--data-root",
        required=True,
        help="Path to the published data directory that contains YYYYMMDD/event folders.",
    )
    parser.add_argument("--date-from", help="Optional lower date bound in YYYYMMDD.")
    parser.add_argument("--date-to", help="Optional upper date bound in YYYYMMDD.")
    parser.add_argument("--limit", type=int, help="Optional maximum number of event folders to scan.")
    parser.add_argument(
        "--show-worst",
        type=int,
        default=5,
        help="How many worst runtime-vs-fallback cases to print.",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    results = _collect_case_results(data_root, args.date_from, args.date_to, args.limit)
    if not results:
        print("No orbit validation cases found.")
        return 1

    observed_solved = sum(1 for item in results if item.observed_candidate is not None)
    runtime_better = sum(
        1
        for item in results
        if item.runtime_errors is not None
        and item.fallback_errors is not None
        and item.runtime_errors.weighted_score() < item.fallback_errors.weighted_score()
    )
    runtime_worse = sum(
        1
        for item in results
        if item.runtime_errors is not None
        and item.fallback_errors is not None
        and item.runtime_errors.weighted_score() >= item.fallback_errors.weighted_score()
    )
    stabilized_mean_anomaly = sum(
        1
        for item in results
        if item.observed_candidate is not None
        and item.runtime_payload.get("mean_anomaly_deg") == item.fallback_payload.get("mean_anomaly_deg")
        and item.runtime_payload.get("epoch") == item.fallback_payload.get("epoch")
        and item.runtime_payload.get("perihelion_distance_au") != item.fallback_payload.get("perihelion_distance_au")
    )

    print(f"cases: {len(results)}")
    print(f"observation solves built: {observed_solved}")
    print(f"runtime better than fallback: {runtime_better}")
    print(f"runtime worse than or equal to fallback: {runtime_worse}")
    print(f"runtime reused fallback mean anomaly / epoch: {stabilized_mean_anomaly}")

    observed_summary = _median_summary(results, "observed_errors")
    fallback_summary = _median_summary(results, "fallback_errors")
    runtime_summary = _median_summary(results, "runtime_errors")
    if observed_summary:
        print(f"median observed errors: {observed_summary}")
    if fallback_summary:
        print(f"median fallback errors: {fallback_summary}")
    if runtime_summary:
        print(f"median runtime errors: {runtime_summary}")

    if args.show_worst > 0:
        print("worst runtime cases:")
        _print_worst_cases(results, args.show_worst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
