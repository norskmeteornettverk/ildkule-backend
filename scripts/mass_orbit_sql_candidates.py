from __future__ import annotations

import argparse
import importlib.util
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys
from typing import Optional

from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tools_common = load_module("tools_common_local", REPO_ROOT / "scripts" / "tools_common.py")
validate = load_module(
    "validate_orbit_against_tables_local",
    REPO_ROOT / "scripts" / "validate_orbit_against_tables.py",
)

from fastapi_app.app.db import session_scope
from fastapi_app.app.utils import orbit_solver

SQL = """
WITH observation_stats AS (
    SELECT
        e.id AS event_id,
        e.datetimetag,
        e.camera_confirmed,
        o.id AS observation_id,
        s.station_name,
        o.summary_latitude,
        o.summary_longitude,
        o.summary_elevation,
        COUNT(tp.id) AS trail_point_count,
        SUM(CASE WHEN tp.event_timestamp_us IS NOT NULL THEN 1 ELSE 0 END) AS timestamp_point_count,
        SUM(CASE WHEN tp.coord_long IS NOT NULL AND tp.coord_lat IS NOT NULL THEN 1 ELSE 0 END) AS coord_point_count,
        MIN(tp.event_timestamp_us) AS first_timestamp,
        MAX(tp.event_timestamp_us) AS last_timestamp,
        CASE
            WHEN COUNT(tp.id) >= 2
             AND MIN(tp.event_timestamp_us) IS NOT NULL
             AND MAX(tp.event_timestamp_us) IS NOT NULL
            THEN MAX(tp.event_timestamp_us) - MIN(tp.event_timestamp_us)
            ELSE NULL
        END AS duration_us,
        CASE
            WHEN o.summary_latitude IS NOT NULL
             AND o.summary_longitude IS NOT NULL
             AND COUNT(tp.id) >= 4
             AND SUM(CASE WHEN tp.event_timestamp_us IS NOT NULL THEN 1 ELSE 0 END) >= 4
             AND SUM(CASE WHEN tp.coord_long IS NOT NULL AND tp.coord_lat IS NOT NULL THEN 1 ELSE 0 END) >= 4
            THEN 1
            ELSE 0
        END AS is_sql_usable_observation
    FROM event e
    JOIN observation_cam_data o
        ON o.event_id = e.id
    JOIN cam c
        ON c.id = o.cam_id
    JOIN station s
        ON s.id = c.station_id
    LEFT JOIN observation_trail_point tp
        ON tp.observation_id = o.id
    WHERE e.is_deleted = 0
    GROUP BY
        e.id,
        e.datetimetag,
        e.camera_confirmed,
        o.id,
        s.station_name,
        o.summary_latitude,
        o.summary_longitude,
        o.summary_elevation
),
event_stats AS (
    SELECT
        event_id,
        datetimetag,
        camera_confirmed,
        COUNT(*) AS observation_count,
        COUNT(DISTINCT station_name) AS station_count,
        SUM(CASE WHEN summary_latitude IS NOT NULL AND summary_longitude IS NOT NULL THEN 1 ELSE 0 END) AS obs_with_camera_position,
        SUM(CASE WHEN trail_point_count >= 4 THEN 1 ELSE 0 END) AS obs_with_4_points,
        SUM(CASE WHEN timestamp_point_count >= 4 THEN 1 ELSE 0 END) AS obs_with_4_timestamps,
        SUM(CASE WHEN coord_point_count >= 4 THEN 1 ELSE 0 END) AS obs_with_4_coords,
        SUM(is_sql_usable_observation) AS usable_observation_count,
        COUNT(DISTINCT CASE WHEN is_sql_usable_observation = 1 THEN station_name END) AS usable_station_count,
        MIN(duration_us) AS min_duration_us,
        MAX(duration_us) AS max_duration_us,
        MIN(CASE WHEN is_sql_usable_observation = 1 THEN first_timestamp END) AS min_usable_first_timestamp,
        MAX(CASE WHEN is_sql_usable_observation = 1 THEN last_timestamp END) AS max_usable_last_timestamp
    FROM observation_stats
    GROUP BY
        event_id,
        datetimetag,
        camera_confirmed
),
event_reason AS (
    SELECT
        event_id,
        datetimetag,
        CASE
            WHEN observation_count = 0 THEN 'kan ikke beregnes: ingen observasjoner'
            WHEN station_count < 2 THEN 'kan ikke beregnes: færre enn to stasjoner'
            WHEN obs_with_camera_position < 2 THEN 'kan ikke beregnes: mangler kameraposisjon'
            WHEN obs_with_4_points < 2 THEN 'kan ikke beregnes: for få trail-punkt'
            WHEN obs_with_4_timestamps < 2 THEN 'kan ikke beregnes: for få timestamps'
            WHEN obs_with_4_coords < 2 THEN 'kan ikke beregnes: for få koordinatpunkt'
            WHEN usable_station_count < 2 THEN 'kan ikke beregnes: færre enn to brukbare stasjoner etter filter'
            WHEN min_usable_first_timestamp IS NOT NULL
             AND max_usable_last_timestamp IS NOT NULL
             AND (max_usable_last_timestamp - min_usable_first_timestamp) > 20000000
            THEN 'kan ikke beregnes: stort tidsgap mellom observasjoner'
            ELSE 'kan potensielt beregnes i SQL'
        END AS sql_status
    FROM event_stats
)
SELECT event_id, datetimetag
FROM event_reason
WHERE sql_status = 'kan potensielt beregnes i SQL'
ORDER BY event_id
"""

POLICIES = ("policy_a", "policy_b", "policy_c", "reserve")


def fetch_candidate_events() -> list[tuple[int, str]]:
    with session_scope() as session:
        rows = session.execute(text(SQL)).all()
        return [(int(row.event_id), str(row.datetimetag)) for row in rows]


def evaluate(event_id: int) -> dict:
    lookup = tools_common.load_event_lookup(event_id=event_id)
    event = lookup.event
    observations = lookup.observations
    fallback_payload = orbit_solver._legacy_stat_orbit(event)
    policy_candidates = {
        policy: orbit_solver._solve_observation_candidate(event, observations, path_policy=policy)
        for policy in POLICIES
    }
    auto_candidate = orbit_solver._solve_observation_candidate(event, observations)
    return {
        "event_id": event_id,
        "datetimetag": event.datetimetag,
        "policy_exists": {policy: candidate is not None for policy, candidate in policy_candidates.items()},
        "policy_usable": {
            policy: (
                candidate is not None
                and orbit_solver._is_reasonable_observed_payload(
                    orbit_solver._stabilize_observed_payload(candidate.payload, fallback_payload, candidate.diagnostics),
                    fallback_payload,
                    candidate.diagnostics,
                )
            )
            for policy, candidate in policy_candidates.items()
        },
        "policy_wild": {
            policy: bool(candidate is not None and validate._payload_is_physically_wild(candidate.payload))
            for policy, candidate in policy_candidates.items()
        },
        "auto_exists": auto_candidate is not None,
        "auto_usable": (
            auto_candidate is not None
            and orbit_solver._is_reasonable_observed_payload(
                orbit_solver._stabilize_observed_payload(auto_candidate.payload, fallback_payload, auto_candidate.diagnostics),
                fallback_payload,
                auto_candidate.diagnostics,
            )
        ),
        "auto_wild": bool(auto_candidate is not None and validate._payload_is_physically_wild(auto_candidate.payload)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch test orbit policies on SQL candidate events.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args()

    candidates = fetch_candidate_events()
    total = len(candidates)
    if not args.json:
        print(f"SQL potentials: {total}")

    results: list[dict] = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        for idx, item in enumerate(pool.map(evaluate, [event_id for event_id, _ in candidates], chunksize=8), start=1):
            results.append(item)
            if not args.json and (idx % 50 == 0 or idx == total):
                print(f"... processed {idx}/{total}")

    counts = Counter()
    examples = defaultdict(list)
    for item in results:
        policy_exists = item["policy_exists"]
        policy_usable = item["policy_usable"]
        auto_usable = item["auto_usable"]
        auto_exists = item["auto_exists"]
        reserve_usable = policy_usable["reserve"]
        scratch_usable = any(policy_usable[p] for p in ("policy_a", "policy_b", "policy_c"))
        scratch_exists = any(policy_exists[p] for p in ("policy_a", "policy_b", "policy_c"))

        counts["policy_a_exists"] += int(policy_exists["policy_a"])
        counts["policy_b_exists"] += int(policy_exists["policy_b"])
        counts["policy_c_exists"] += int(policy_exists["policy_c"])
        counts["reserve_exists"] += int(policy_exists["reserve"])
        counts["policy_a_usable"] += int(policy_usable["policy_a"])
        counts["policy_b_usable"] += int(policy_usable["policy_b"])
        counts["policy_c_usable"] += int(policy_usable["policy_c"])
        counts["reserve_usable"] += int(policy_usable["reserve"])
        counts["auto_usable"] += int(auto_usable)
        counts["auto_exists"] += int(auto_exists)
        counts["scratch_exists"] += int(scratch_exists)
        counts["scratch_usable"] += int(scratch_usable)
        counts["reserve_only_usable"] += int(reserve_usable and not scratch_usable)
        counts["no_usable_any"] += int(not auto_usable)
        counts["auto_wild"] += int(item["auto_wild"])
        counts["scratch_wild_any"] += int(any(item["policy_wild"][p] for p in ("policy_a", "policy_b", "policy_c")))

        if reserve_usable and not scratch_usable and len(examples["reserve_only"]) < 5:
            examples["reserve_only"].append((item["event_id"], item["datetimetag"]))
        if not auto_usable and len(examples["fail"]) < 5:
            examples["fail"].append((item["event_id"], item["datetimetag"]))

    def pct(n: int) -> float:
        return (100.0 * n / total) if total else 0.0

    summary = {
        "sql_potentials": total,
        "policy_usable": {
            policy: {"count": counts[key], "percent": round(pct(counts[key]), 1)}
            for policy, key in (
                ("policy_a", "policy_a_usable"),
                ("policy_b", "policy_b_usable"),
                ("policy_c", "policy_c_usable"),
                ("reserve", "reserve_usable"),
            )
        },
        "scratch_vs_reserve": {
            "any_from_scratch_policy_usable": {
                "count": counts["scratch_usable"],
                "percent": round(pct(counts["scratch_usable"]), 1),
            },
            "reserve_usable": {
                "count": counts["reserve_usable"],
                "percent": round(pct(counts["reserve_usable"]), 1),
            },
            "reserve_only_rescue": {
                "count": counts["reserve_only_usable"],
                "percent": round(pct(counts["reserve_only_usable"]), 1),
            },
            "auto_usable": {
                "count": counts["auto_usable"],
                "percent": round(pct(counts["auto_usable"]), 1),
            },
            "auto_physically_wild": {
                "count": counts["auto_wild"],
                "percent": round(pct(counts["auto_wild"]), 1),
            },
        },
        "examples": dict(examples),
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    print()
    print("Per policy usable:")
    for policy, key in (("policy_a", "policy_a_usable"), ("policy_b", "policy_b_usable"), ("policy_c", "policy_c_usable"), ("reserve", "reserve_usable")):
        print(f"- {policy}: {counts[key]} ({pct(counts[key]):.1f}%)")

    print()
    print("Scratch vs reserve:")
    print(f"- any from-scratch policy usable: {counts['scratch_usable']} ({pct(counts['scratch_usable']):.1f}%)")
    print(f"- reserve usable: {counts['reserve_usable']} ({pct(counts['reserve_usable']):.1f}%)")
    print(f"- reserve-only rescue: {counts['reserve_only_usable']} ({pct(counts['reserve_only_usable']):.1f}%)")
    print(f"- auto usable (final runtime path): {counts['auto_usable']} ({pct(counts['auto_usable']):.1f}%)")
    print(f"- auto physically wild: {counts['auto_wild']} ({pct(counts['auto_wild']):.1f}%)")

    print()
    print("Examples:")
    print(f"- reserve-only rescue: {examples['reserve_only']}")
    print(f"- no usable orbit: {examples['fail']}")


if __name__ == "__main__":
    main()
