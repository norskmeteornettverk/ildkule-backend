from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import argparse
import re
from pathlib import Path
from typing import Optional

from tools_common import find_event_dir, load_event_lookup, print_json, resolve_data_root

from fastapi_app.app.utils.orbit_solver import (
    _MIN_FIT_POINTS,
    _MIN_TRACKS,
    _ObservationOrbitCandidate,
    _PathFitDiagnostics,
    _build_track,
    _can_stabilize_mean_anomaly,
    _is_reasonable_observed_payload,
    _legacy_stat_orbit,
    _runtime_payload_from_candidate,
    _solve_observation_candidate,
    _stabilize_observed_payload,
    _wrapped_angle_delta,
    build_orbit_payload,
)


_ROW_RE = re.compile(r"<tr><td>([^<]+):</td><td>\s*([^<]+)</td></tr>")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _coerce_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _NUMBER_RE.search(str(value).replace(",", "."))
    return float(match.group(0)) if match else None


def _parse_tables_truth(event_dir: Optional[Path]) -> Optional[dict[str, float]]:
    if event_dir is None:
        return None
    path = event_dir / "tables.html"
    if not path.exists():
        return None
    rows = {key.strip(): value.strip() for key, value in _ROW_RE.findall(path.read_text(encoding="utf-8", errors="ignore"))}
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
    return {
        "perihelion_distance_au": float(_coerce_float(rows["Perihelavstand"])),
        "eccentricity": float(_coerce_float(rows["Eksentrisitet"])),
        "inclination_deg": float(_coerce_float(rows["Inklinasjon"])),
        "ascending_node_deg": float(_coerce_float(rows["Knutelengde"])),
        "argument_of_perihelion_deg": float(_coerce_float(rows["Perihelargument"])),
        "mean_anomaly_deg": float(_coerce_float(rows["Midlere anomali"])),
    }


def _payload_is_physical(payload: Optional[dict]) -> bool:
    if not payload:
        return False
    required = (
        "perihelion_distance_au",
        "eccentricity",
        "inclination_deg",
        "ascending_node_deg",
        "argument_of_perihelion_deg",
        "mean_anomaly_deg",
    )
    if any(payload.get(key) is None for key in required):
        return False
    return (
        0.0 < float(payload["perihelion_distance_au"]) < 2.0
        and 0.0 < float(payload["eccentricity"]) < 1.5
        and 0.0 <= float(payload["inclination_deg"]) <= 180.0
        and abs(float(payload["mean_anomaly_deg"])) <= 720.0
    )


def _payload_errors(payload: Optional[dict], truth: Optional[dict]) -> Optional[dict[str, float]]:
    if payload is None or truth is None:
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
    return {
        "q": abs(float(payload["perihelion_distance_au"]) - truth["perihelion_distance_au"]),
        "e": abs(float(payload["eccentricity"]) - truth["eccentricity"]),
        "i": abs(float(payload["inclination_deg"]) - truth["inclination_deg"]),
        "node": _wrapped_angle_delta(float(payload["ascending_node_deg"]), truth["ascending_node_deg"]),
        "argp": _wrapped_angle_delta(float(payload["argument_of_perihelion_deg"]), truth["argument_of_perihelion_deg"]),
        "mean_anomaly": _wrapped_angle_delta(float(payload["mean_anomaly_deg"]), truth["mean_anomaly_deg"]),
    }


def _stage_for_candidate(candidate: Optional[_ObservationOrbitCandidate], usable_tracks: int, raw_points: int, runtime_payload: Optional[dict], fallback_payload: dict) -> str:
    if candidate is None:
        if usable_tracks == 0:
            return "ingen brukbar stasjonsbane"
        if usable_tracks < _MIN_TRACKS:
            return "færre enn to brukbare stasjoner"
        if raw_points < _MIN_FIT_POINTS:
            return "for mange punkt falt bort før tilpassing"
        return "fart eller retning kunne ikke løses"
    if not _payload_is_physical(candidate.payload):
        if candidate.payload and any(candidate.payload.get(key) is not None for key in candidate.payload):
            return "full ny bane bygget, men fysisk vill"
        return "heliosentrisk bane kunne ikke løses"
    uses_new_geometry = runtime_payload is not None and runtime_payload.get("perihelion_distance_au") != fallback_payload.get("perihelion_distance_au")
    reuses_old_mean_epoch = (
        uses_new_geometry
        and runtime_payload.get("mean_anomaly_deg") == fallback_payload.get("mean_anomaly_deg")
        and runtime_payload.get("epoch") == fallback_payload.get("epoch")
    )
    if uses_new_geometry and reuses_old_mean_epoch:
        return "full ny bane akseptert i API-et (M/epoch stabilisert)"
    if uses_new_geometry:
        return "full ny bane akseptert i API-et"
    return "full ny bane bygget, men avvist før final API choice"


def _serialize_candidate(name: str, candidate: Optional[_ObservationOrbitCandidate], fallback_payload: dict, truth: Optional[dict], usable_tracks: int, raw_points: int) -> dict:
    runtime_payload = _runtime_payload_from_candidate(candidate, fallback_payload)
    diagnostics: Optional[_PathFitDiagnostics] = candidate.diagnostics if candidate is not None else None
    stabilized_payload = (
        _stabilize_observed_payload(candidate.payload, fallback_payload, diagnostics)
        if candidate is not None
        else None
    )
    return {
        "policy": name,
        "stage": _stage_for_candidate(candidate, usable_tracks, raw_points, runtime_payload, fallback_payload),
        "has_candidate": candidate is not None,
        "physical": _payload_is_physical(candidate.payload if candidate else None),
        "passes_runtime_guard": (
            _is_reasonable_observed_payload(stabilized_payload, fallback_payload, diagnostics)
            if candidate is not None
            else False
        ),
        "stabilizes_mean_anomaly": (
            _can_stabilize_mean_anomaly(candidate.payload, fallback_payload, diagnostics)
            if candidate is not None
            else False
        ),
        "diagnostics": {
            "track_count": diagnostics.track_count,
            "fit_point_count": diagnostics.fit_point_count,
            "median_residual_km": diagnostics.median_residual_km,
            "max_residual_km": diagnostics.max_residual_km,
            "policy_name": diagnostics.policy_name,
            "timing_spread_seconds": diagnostics.timing_spread_seconds,
            "late_point_fraction": diagnostics.late_point_fraction,
        } if diagnostics else None,
        "candidate_payload": candidate.payload if candidate else None,
        "runtime_payload_if_selected": runtime_payload,
        "errors_vs_tables": _payload_errors(candidate.payload if candidate else None, truth),
    }


def print_report(payload: dict) -> None:
    print("Orbit diagnose")
    print(f"- event id: {payload['event_id']}")
    print(f"- datetimetag: {payload['datetimetag']}")
    print(f"- observations in DB: {payload['observation_count']}")
    print(f"- usable tracks: {payload['usable_track_count']}")
    print(f"- raw point count: {payload['raw_point_count']}")
    print(f"- tables.html available: {payload['has_tables_truth']}")
    print("- old simple calculation:")
    print(f"  {payload['old_simple_calculation']}")
    print("- policies:")
    for item in payload["policies"]:
        print(f"  - {item['policy']}: {item['stage']}")
        if item["diagnostics"]:
            print(
                "    diagnostics: "
                f"tracks={item['diagnostics']['track_count']} fit_points={item['diagnostics']['fit_point_count']} "
                f"median_residual_km={item['diagnostics']['median_residual_km']:.3f} max_residual_km={item['diagnostics']['max_residual_km']:.3f} "
                f"timing_spread_s={item['diagnostics']['timing_spread_seconds']:.3f}"
            )
        if item["errors_vs_tables"]:
            print(f"    errors vs tables.html: {item['errors_vs_tables']}")
    print("- final API choice:")
    print(f"  {payload['final_api_choice']}")
    if payload["final_api_errors_vs_tables"]:
        print(f"  errors vs tables.html: {payload['final_api_errors_vs_tables']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose why the new point-based orbit does or does not work for one event.")
    parser.add_argument("--event-id", type=int, help="DB event id.")
    parser.add_argument("--datetimetag", help="Event datetimetag.")
    parser.add_argument("--data-root", help="Dataset root. Falls back to DATA_DIRECTORY.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    lookup = load_event_lookup(event_id=args.event_id, datetimetag=args.datetimetag)
    observations = lookup.observations
    usable_tracks = [_build_track(observation) for observation in observations]
    usable_tracks = [track for track in usable_tracks if track is not None]
    raw_points = sum(len(observation.trail_points or []) for observation in observations)
    fallback_payload = _legacy_stat_orbit(lookup.event)

    event_dir = None
    truth = None
    try:
        data_root = resolve_data_root(args.data_root)
        event_dir = find_event_dir(data_root, lookup.event.datetimetag)
        truth = _parse_tables_truth(event_dir)
    except SystemExit:
        pass

    policies = []
    for policy_name in ("policy_a", "policy_b", "policy_c", "reserve"):
        candidate = _solve_observation_candidate(lookup.event, observations, path_policy=policy_name)
        policies.append(_serialize_candidate(policy_name, candidate, fallback_payload, truth, len(usable_tracks), raw_points))

    final_api_choice = build_orbit_payload(lookup.event, observations)
    payload = {
        "event_id": lookup.event.id,
        "datetimetag": lookup.event.datetimetag,
        "observation_count": len(observations),
        "usable_track_count": len(usable_tracks),
        "raw_point_count": raw_points,
        "event_dir": str(event_dir) if event_dir else None,
        "has_tables_truth": truth is not None,
        "old_simple_calculation": fallback_payload,
        "old_simple_errors_vs_tables": _payload_errors(fallback_payload, truth),
        "policies": policies,
        "final_api_choice": final_api_choice,
        "final_api_errors_vs_tables": _payload_errors(final_api_choice, truth),
    }

    if args.json:
        print_json(payload)
    else:
        print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
