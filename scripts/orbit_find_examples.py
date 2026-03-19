from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Optional

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tools_common import (
    load_event_case_from_disk,
    print_json,
    resolve_data_root,
)

from fastapi_app.app.utils.orbit_solver import (
    _MAX_ORBIT_SPEED_KMS,
    _MIN_TRACKS,
    _ProjectedPathSample,
    _build_track,
    _fit_line_anchor,
    _fit_trajectory_direction,
    _path_endpoints_ecef,
    _sample_line_scalar_and_residual,
    _solve_observation_candidate,
)


def _iter_event_dirs(data_root: Path, include_without_tables: bool) -> list[Path]:
    event_dirs: list[Path] = []
    for date_dir in sorted(entry for entry in data_root.iterdir() if entry.is_dir() and entry.name.isdigit() and len(entry.name) == 8):
        for event_dir in sorted(entry for entry in date_dir.iterdir() if entry.is_dir()):
            if include_without_tables or (event_dir / "tables.html").exists():
                event_dirs.append(event_dir)
    return event_dirs


def _largest_gap_seconds(timestamps: list[float]) -> Optional[float]:
    if len(timestamps) < 2:
        return None
    return max(later - earlier for earlier, later in zip(timestamps, timestamps[1:]))


def _observation_summary(observation, track) -> dict[str, Any]:
    timestamps = sorted(
        float(point.event_timestamp)
        for point in (observation.trail_points or [])
        if point.event_timestamp is not None
    )
    return {
        "station": (
            observation.cam.station.station_name
            if observation.cam and observation.cam.station
            else getattr(observation, "station_name", None)
        ),
        "camera": observation.cam.cam_name if observation.cam else getattr(observation, "cam_name", None),
        "raw_point_count": len(observation.trail_points or []),
        "built_track_point_count": len(track.points) if track is not None else 0,
        "first_timestamp": timestamps[0] if timestamps else None,
        "last_timestamp": timestamps[-1] if timestamps else None,
        "largest_internal_gap_seconds": _largest_gap_seconds(timestamps),
        "ams_point_count": sum(
            1
            for point in (observation.trail_points or [])
            if point.ams_coord_long is not None and point.ams_coord_lat is not None
        ),
        "centroid_point_count": sum(
            1
            for point in (observation.trail_points or [])
            if point.centroid_coord_long is not None and point.centroid_coord_lat is not None
        ),
        "centroid2_point_count": sum(
            1
            for point in (observation.trail_points or [])
            if point.centroid2_coord_long is not None and point.centroid2_coord_lat is not None
        ),
    }


def _reserve_probe(tracks) -> dict[str, Any]:
    direction = _fit_trajectory_direction(tracks)
    if direction is None:
        return {
            "direction_found": False,
            "anchor_found": False,
            "sample_count": 0,
            "sample_track_count": 0,
            "raw_linear_speed_signed_kms": None,
            "raw_linear_speed_abs_kms": None,
        }

    anchor = _fit_line_anchor(direction, tracks)
    if anchor is None:
        return {
            "direction_found": True,
            "anchor_found": False,
            "sample_count": 0,
            "sample_track_count": 0,
            "raw_linear_speed_signed_kms": None,
            "raw_linear_speed_abs_kms": None,
        }

    samples: list[_ProjectedPathSample] = []
    sample_counts: dict[int, int] = {}
    for track_index, track in enumerate(tracks):
        for point in track.points:
            geometry = _sample_line_scalar_and_residual(anchor, direction, track, point)
            if geometry is None:
                continue
            scalar_km, residual_km = geometry
            if residual_km > 18.0:
                continue
            samples.append(
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
            sample_counts[track_index] = sample_counts.get(track_index, 0) + 1

    signed_speed = None
    if len(samples) >= 2 and len(sample_counts) >= _MIN_TRACKS:
        design_rows = []
        targets = []
        timestamps = []
        for sample in samples:
            row = [0.0]
            for intercept_index in range(len(tracks)):
                row.append(1.0 if intercept_index == sample.track_index else 0.0)
            design_rows.append(row)
            targets.append(sample.scalar_km)
            timestamps.append(sample.timestamp)
        design = np.asarray(design_rows, dtype=float)
        time_center = float(np.mean(np.asarray(timestamps, dtype=float)))
        design[:, 0] = np.asarray(timestamps, dtype=float) - time_center
        solution, _, _, _ = np.linalg.lstsq(
            design,
            np.asarray(targets, dtype=float),
            rcond=None,
        )
        signed_speed = float(solution[0])

    return {
        "direction_found": True,
        "anchor_found": True,
        "sample_count": len(samples),
        "sample_track_count": len(sample_counts),
        "sample_counts_by_track_index": sample_counts,
        "raw_linear_speed_signed_kms": signed_speed,
        "raw_linear_speed_abs_kms": abs(signed_speed) if signed_speed is not None else None,
    }


def _quick_notes(observations: list[dict[str, Any]], reserve_probe: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    largest_gap = max(
        (
            item["largest_internal_gap_seconds"]
            for item in observations
            if item["largest_internal_gap_seconds"] is not None
        ),
        default=None,
    )
    if largest_gap is not None and largest_gap > 1.0:
        notes.append(f"minst ett spor har stort tidsgap internt ({largest_gap:.2f} s)")
    raw_speed = reserve_probe.get("raw_linear_speed_abs_kms")
    if raw_speed is not None and raw_speed < 5.0:
        notes.append(f"rå lineær fart fra beholdte punkt havner under solvergrensa på 5 km/s ({raw_speed:.2f} km/s)")
    if raw_speed is not None and raw_speed > _MAX_ORBIT_SPEED_KMS:
        notes.append(
            f"rå lineær fart fra beholdte punkt havner over solvergrensa på {_MAX_ORBIT_SPEED_KMS:.0f} km/s ({raw_speed:.2f} km/s)"
        )
    if reserve_probe.get("sample_track_count", 0) < _MIN_TRACKS:
        notes.append("etter linjegeometri sitter det ikke igjen punkt fra to spor")
    return notes


def _process_event_dir(data_root: str, event_dir: str, policy_name: str) -> Optional[dict[str, Any]]:
    lookup = load_event_case_from_disk(Path(data_root), Path(event_dir))
    tracks_by_observation = [_build_track(observation) for observation in lookup.observations]
    usable_tracks = [track for track in tracks_by_observation if track is not None]
    if len(usable_tracks) < _MIN_TRACKS:
        return None

    candidate = _solve_observation_candidate(lookup.event, lookup.observations, path_policy=policy_name)
    if candidate is not None:
        return None

    observation_summaries = [
        _observation_summary(observation, track)
        for observation, track in zip(lookup.observations, tracks_by_observation)
    ]
    reserve_probe = _reserve_probe(usable_tracks)
    payload = {
        "datetimetag": lookup.event.datetimetag,
        "event_dir": str(lookup.event_dir),
        "policy": policy_name,
        "observation_count": len(lookup.observations),
        "usable_track_count": len(usable_tracks),
        "has_cross_station_endpoints": _path_endpoints_ecef(lookup.event) is not None,
        "observations": observation_summaries,
        "reserve_probe": reserve_probe,
    }
    payload["notes"] = _quick_notes(observation_summaries, reserve_probe)
    if not payload["has_cross_station_endpoints"]:
        payload["notes"].append("hendelsen mangler løste start/slutt-endepunkt i event-feltene")
    return payload


def _print_report(payload: dict[str, Any]) -> None:
    print("Eksempler der ny bane ikke blir bygget")
    print(f"- antall funnet: {payload['count']}")
    print(f"- policy: {payload['policy']}")
    for item in payload["examples"]:
        print(f"- {item['datetimetag']} ({item['event_dir']})")
        print(
            "  "
            f"observasjoner={item['observation_count']} "
            f"brukbare spor={item['usable_track_count']} "
            f"har_endepunkt={item['has_cross_station_endpoints']}"
        )
        probe = item["reserve_probe"]
        print(
            "  "
            f"reserve_probe: direction={probe['direction_found']} "
            f"anchor={probe['anchor_found']} "
            f"samples={probe['sample_count']} "
            f"sample_tracks={probe['sample_track_count']} "
            f"raw_speed_abs_kms={probe['raw_linear_speed_abs_kms']}"
        )
        for observation in item["observations"]:
            print(
                "  "
                f"{observation['station']}/{observation['camera']}: "
                f"raw_points={observation['raw_point_count']} "
                f"built_track_points={observation['built_track_point_count']} "
                f"largest_gap_s={observation['largest_internal_gap_seconds']}"
            )
        for note in item["notes"]:
            print(f"    note: {note}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Finn flere konkrete hendelser der solveren ikke bygger ny bane selv om den har minst to spor."
    )
    parser.add_argument("--data-root", help="Dataset root. Falls back to DATA_DIRECTORY.")
    parser.add_argument("--policy", default="policy_a", choices=("policy_a", "policy_b", "policy_c", "reserve"))
    parser.add_argument("--limit", type=int, default=5, help="Hvor mange eksempler som skal vises.")
    parser.add_argument(
        "--include-without-tables",
        action="store_true",
        help="Ta med hendelser uten tables.html.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, (os.cpu_count() or 1) - 1),
        help="Antall worker-prosesser.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    data_root = resolve_data_root(args.data_root)
    event_dirs = _iter_event_dirs(data_root, include_without_tables=args.include_without_tables)
    examples: list[dict[str, Any]] = []

    if args.workers <= 1:
        for event_dir in event_dirs:
            result = _process_event_dir(str(data_root), str(event_dir), args.policy)
            if result is None:
                continue
            examples.append(result)
            if len(examples) >= max(args.limit, 1):
                break
    else:
        with ProcessPoolExecutor(max_workers=max(1, args.workers)) as executor:
            for result in executor.map(
                _process_event_dir,
                (str(data_root) for _ in event_dirs),
                (str(event_dir) for event_dir in event_dirs),
                (args.policy for _ in event_dirs),
            ):
                if result is None:
                    continue
                examples.append(result)
                if len(examples) >= max(args.limit, 1):
                    break

    payload = {
        "count": len(examples),
        "policy": args.policy,
        "examples": examples,
    }
    if args.json:
        print_json(payload)
    else:
        _print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
