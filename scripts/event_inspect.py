from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import argparse

from tools_common import (
    event_file_summary,
    find_event_dir,
    load_event_lookup,
    observation_stats,
    print_json,
    resolve_data_root,
    serialize_event_basic,
)


def print_report(payload: dict) -> None:
    event = payload["event"]
    print("Event inspect")
    print(f"- event id: {event['id']}")
    print(f"- datetimetag: {event['datetimetag']}")
    print(f"- date: {event['date']}")
    print(f"- location: {event['location']}")
    print(f"- camera_confirmed: {event['camera_confirmed']}")
    print(f"- track_speed: {event['track_speed']} ({event['track_speed_source']})")
    print(
        f"- start: lat={event['track_start']['lat']} long={event['track_start']['long']} height_km={event['track_start']['height_km']}"
    )
    print(
        f"- end: lat={event['track_end']['lat']} long={event['track_end']['long']} height_km={event['track_end']['height_km']}"
    )
    print(
        f"- radiant: ra={event['radiant']['ra']} dec={event['radiant']['dec']} ecl_long={event['radiant']['ecl_long']} ecl_lat={event['radiant']['ecl_lat']}"
    )
    print(f"- observations in DB: {len(payload['observations'])}")
    for observation in payload["observations"]:
        print(
            f"  - obs {observation['observation_id']}: {observation['station']} / {observation['camera']} | "
            f"trail={observation['trail_point_count']} coord={observation['coord_point_count']} "
            f"ams={observation['ams_point_count']} centroid={observation['centroid_point_count']} "
            f"centroid2={observation['centroid2_point_count']}"
        )
    file_summary = payload.get("files")
    if file_summary:
        print(f"- event folder: {file_summary['event_dir']}")
        print(f"- event-level files: {', '.join(file_summary['event_files']) if file_summary['event_files'] else '(none)'}")
        print(f"- observation folders on disk: {len(file_summary['observation_folders'])}")
        for item in file_summary["observation_folders"]:
            print(
                f"  - {item['station']} / {item['camera']}: event.txt={item['has_event_txt']} centroid={item['has_centroid']} centroid2={item['has_centroid2']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect one event from DB and optional files on disk.")
    parser.add_argument("--event-id", type=int, help="DB event id.")
    parser.add_argument("--datetimetag", help="Event datetimetag.")
    parser.add_argument("--data-root", help="Dataset root. Falls back to DATA_DIRECTORY.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    lookup = load_event_lookup(event_id=args.event_id, datetimetag=args.datetimetag)
    payload = {
        "event": serialize_event_basic(lookup.event),
        "observations": [observation_stats(observation) for observation in lookup.observations],
    }
    try:
        data_root = resolve_data_root(args.data_root)
        event_dir = find_event_dir(data_root, lookup.event.datetimetag)
        if event_dir is not None:
            payload["files"] = event_file_summary(event_dir)
    except SystemExit:
        pass

    if args.json:
        print_json(payload)
    else:
        print_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
