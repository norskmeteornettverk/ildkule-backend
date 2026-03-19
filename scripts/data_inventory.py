from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import argparse
from collections import Counter
from pathlib import Path

from tools_common import is_date_dir, is_event_dir, print_json, resolve_data_root


KEY_EVENT_FILES = ("tables.html", "location.txt", "event.stat", "event.res", "orbit.html", "orbit.jpg")
KEY_OBSERVATION_FILES = ("event.txt", "centroid.txt", "centroid2.txt")


def build_inventory(data_root: Path) -> dict:
    counts = Counter()
    key_event_file_counts = Counter()
    key_observation_file_counts = Counter()
    events_with = Counter()
    observations_per_event: list[int] = []

    for date_dir in sorted(entry for entry in data_root.iterdir() if entry.is_dir() and is_date_dir(entry.name)):
        counts["date_dirs"] += 1
        for event_dir in sorted(entry for entry in date_dir.iterdir() if entry.is_dir()):
            counts["event_dirs"] += 1
            if event_dir.name[:6].isdigit() and len(event_dir.name) > 6:
                counts["suffix_event_dirs"] += 1
            if is_event_dir(event_dir.name):
                counts["pattern_event_dirs"] += 1
            event_files = {entry.name for entry in event_dir.iterdir() if entry.is_file()}
            for file_name in KEY_EVENT_FILES:
                if file_name in event_files:
                    key_event_file_counts[file_name] += 1
                    events_with[file_name] += 1

            observation_count = 0
            for station_dir in sorted(entry for entry in event_dir.iterdir() if entry.is_dir()):
                for camera_dir in sorted(entry for entry in station_dir.iterdir() if entry.is_dir()):
                    camera_files = {entry.name for entry in camera_dir.iterdir() if entry.is_file()}
                    if not camera_files:
                        continue
                    counts["camera_dirs"] += 1
                    observation_count += 1
                    for file_name in KEY_OBSERVATION_FILES:
                        if file_name in camera_files:
                            key_observation_file_counts[file_name] += 1
                    if "event.txt" in camera_files and "centroid.txt" in camera_files:
                        counts["event_plus_centroid"] += 1
                    if "event.txt" in camera_files and "centroid2.txt" in camera_files:
                        counts["event_plus_centroid2"] += 1
            observations_per_event.append(observation_count)
            if observation_count >= 1:
                counts["events_with_observations"] += 1
            if observation_count >= 2:
                counts["events_with_two_plus_observations"] += 1

    average_observations = (
        sum(observations_per_event) / len(observations_per_event)
        if observations_per_event else 0.0
    )
    return {
        "data_root": str(data_root),
        "counts": dict(counts),
        "key_event_files": dict(key_event_file_counts),
        "key_observation_files": dict(key_observation_file_counts),
        "average_observations_per_event": round(average_observations, 3),
    }


def print_report(payload: dict) -> None:
    counts = payload["counts"]
    print("Data inventory")
    print(f"- data root: {payload['data_root']}")
    print(f"- date folders: {counts.get('date_dirs', 0)}")
    print(f"- event folders: {counts.get('event_dirs', 0)}")
    print(f"- event folders with suffix: {counts.get('suffix_event_dirs', 0)}")
    print(f"- camera folders: {counts.get('camera_dirs', 0)}")
    print(f"- events with at least one observation: {counts.get('events_with_observations', 0)}")
    print(f"- events with at least two observations: {counts.get('events_with_two_plus_observations', 0)}")
    print(f"- average observations per event: {payload['average_observations_per_event']}")
    print("- event-level files:")
    for key, value in sorted(payload["key_event_files"].items()):
        print(f"  - {key}: {value}")
    print("- observation-level files:")
    for key, value in sorted(payload["key_observation_files"].items()):
        print(f"  - {key}: {value}")
    print(f"- observation folders with event.txt + centroid.txt: {counts.get('event_plus_centroid', 0)}")
    print(f"- observation folders with event.txt + centroid2.txt: {counts.get('event_plus_centroid2', 0)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick inventory of the file dataset without heavy parsing.")
    parser.add_argument("--data-root", help="Dataset root. Falls back to DATA_DIRECTORY.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    data_root = resolve_data_root(args.data_root)
    payload = build_inventory(data_root)
    if args.json:
        print_json(payload)
    else:
        print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
