from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import inspect, select
from sqlalchemy.orm import selectinload

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi_app.app.config import get_settings
from fastapi_app.app.db import engine, session_scope
from fastapi_app.app.models import Cam, Event, ObservationCamData, ObservationTrailPoint, Station

_DATE_DIR_RE = re.compile(r"^\d{8}$")
_EVENT_DIR_RE = re.compile(r"^\d{6}[A-Za-z]?$")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_COLUMN_RE = re.compile(r"^\s*`?(?P<name>[A-Za-z_][A-Za-z0-9_]*)`?\s+(?P<type>[A-Za-z]+(?:\([^\)]*\))?)", re.IGNORECASE)
_SKIP_PREFIXES = ("PRIMARY KEY", "CONSTRAINT", "INDEX", "UNIQUE", "FOREIGN KEY", "KEY ", "REFERENCES", "ON ")


@dataclass(frozen=True)
class EventLookup:
    event: Event
    observations: list[ObservationCamData]


@dataclass(frozen=True)
class DiskEventLookup:
    event: Event
    observations: list[ObservationCamData]
    event_dir: Path


def resolve_repo_root() -> Path:
    return REPO_ROOT


def resolve_data_root(data_root: Optional[str]) -> Path:
    if data_root:
        return Path(data_root)
    settings = get_settings()
    if settings.data_directory:
        return Path(settings.data_directory)
    raise SystemExit("No data root given and DATA_DIRECTORY is not set.")


def find_event_dir(data_root: Path, datetimetag: str) -> Optional[Path]:
    if len(datetimetag) < 14:
        return None
    candidate = data_root / datetimetag[:8] / datetimetag[8:]
    if candidate.is_dir():
        return candidate
    return None


def event_file_summary(event_dir: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "event_dir": str(event_dir),
        "exists": event_dir.is_dir(),
        "event_files": [],
        "observation_folders": [],
    }
    if not event_dir.is_dir():
        return summary
    event_files = sorted(
        entry.name
        for entry in event_dir.iterdir()
        if entry.is_file()
    )
    summary["event_files"] = event_files
    observation_folders: list[dict[str, Any]] = []
    for station_dir in sorted(entry for entry in event_dir.iterdir() if entry.is_dir()):
        camera_dirs = [entry for entry in station_dir.iterdir() if entry.is_dir()]
        for camera_dir in sorted(camera_dirs):
            files = {entry.name for entry in camera_dir.iterdir() if entry.is_file()}
            if not files:
                continue
            observation_folders.append(
                {
                    "station": station_dir.name,
                    "camera": camera_dir.name,
                    "has_event_txt": "event.txt" in files,
                    "has_centroid": "centroid.txt" in files,
                    "has_centroid2": "centroid2.txt" in files,
                    "file_count": len(files),
                }
            )
    summary["observation_folders"] = observation_folders
    return summary


def load_event_lookup(event_id: Optional[int] = None, datetimetag: Optional[str] = None) -> EventLookup:
    if event_id is None and not datetimetag:
        raise SystemExit("Use --event-id or --datetimetag.")
    with session_scope() as session:
        session.expire_on_commit = False
        stmt = (
            select(Event)
            .options(
                selectinload(Event.observation_data)
                .selectinload(ObservationCamData.cam)
                .selectinload(Cam.station),
                selectinload(Event.observation_data).selectinload(ObservationCamData.trail_points),
            )
        )
        if event_id is not None:
            stmt = stmt.where(Event.id == event_id)
        else:
            stmt = stmt.where(Event.datetimetag == datetimetag)
        event = session.scalars(stmt).unique().first()
        if event is None:
            lookup = datetimetag if datetimetag else str(event_id)
            raise SystemExit(f"Event not found: {lookup}")
        observations = list(event.observation_data or [])
        session.expunge_all()
        return EventLookup(event=event, observations=observations)


def coerce_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _NUMBER_RE.search(str(value).replace(",", "."))
    return float(match.group(0)) if match else None


def _event_from_disk_record(record: dict[str, Any]) -> Event:
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
        payload[field_name] = coerce_float(payload.get(field_name))
    return Event(**payload)


def _observation_from_disk_record(record: Any) -> ObservationCamData:
    values = dict(record.values)
    for field_name in ("summary_latitude", "summary_longitude", "summary_elevation"):
        values[field_name] = coerce_float(values.get(field_name))
    observation = ObservationCamData(
        **{key: value for key, value in values.items() if hasattr(ObservationCamData, key)}
    )
    observation.station_name = getattr(record, "station_name", None)
    observation.cam_name = getattr(record, "cam_name", None)
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
            centroid_coord_long=point.centroid_coord_long,
            centroid_coord_lat=point.centroid_coord_lat,
            centroid2_coord_long=point.centroid2_coord_long,
            centroid2_coord_lat=point.centroid2_coord_lat,
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


def load_event_case_from_disk(data_root: Path, event_dir: Path) -> DiskEventLookup:
    from fastapi_app.app.services.file_mapper import FileToObjectMapper

    date_string = event_dir.parent.name
    mapper = FileToObjectMapper(data_root, date_string, date_string)
    record = mapper._process_event_folder(date_string, event_dir.name, event_dir)
    if record is None:
        raise SystemExit(f"Could not parse event folder {event_dir}")
    return DiskEventLookup(
        event=_event_from_disk_record(record.event),
        observations=[_observation_from_disk_record(item) for item in record.observations],
        event_dir=event_dir,
    )


def serialize_event_basic(event: Event) -> dict[str, Any]:
    return {
        "id": event.id,
        "datetimetag": event.datetimetag,
        "date": event.date.isoformat() if event.date else None,
        "location": event.location,
        "camera_confirmed": event.camera_confirmed,
        "track_speed": event.track_speed,
        "track_speed_source": event.track_speed_source,
        "track_start": {
            "lat": event.track_startlat,
            "long": event.track_startlong,
            "height_km": event.track_startheight,
        },
        "track_end": {
            "lat": event.track_endlat,
            "long": event.track_endlong,
            "height_km": event.track_endheight,
        },
        "radiant": {
            "ra": event.radiant_ra,
            "dec": event.radiant_dec,
            "ecl_long": event.radiant_ecl_long,
            "ecl_lat": event.radiant_ecl_lat,
        },
    }


def observation_stats(observation: ObservationCamData) -> dict[str, Any]:
    points = list(observation.trail_points or [])
    timestamps = [point.event_timestamp for point in points if point.event_timestamp is not None]
    return {
        "observation_id": observation.id,
        "observation_key": observation.observation_key,
        "station": observation.cam.station.station_name if observation.cam and observation.cam.station else None,
        "camera": observation.cam.cam_name if observation.cam else None,
        "summary_latitude": observation.summary_latitude,
        "summary_longitude": observation.summary_longitude,
        "summary_elevation": observation.summary_elevation,
        "trail_point_count": len(points),
        "coord_point_count": sum(1 for point in points if point.coord_long is not None and point.coord_lat is not None),
        "ams_point_count": sum(1 for point in points if point.ams_coord_long is not None and point.ams_coord_lat is not None),
        "centroid_point_count": sum(1 for point in points if point.centroid_coord_long is not None and point.centroid_coord_lat is not None),
        "centroid2_point_count": sum(1 for point in points if point.centroid2_coord_long is not None and point.centroid2_coord_lat is not None),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
        "has_event_txt_raw": bool(observation.trail_coordinates),
        "has_ams_raw": bool(observation.trail_ams_coords),
        "has_centroid_raw": bool(observation.trail_centroid),
        "has_centroid2_raw": bool(observation.trail_centroid2),
    }


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _normalize_sql_type(type_name: str) -> str:
    upper = type_name.upper()
    if "VARCHAR" in upper:
        return "VARCHAR"
    if re.search(r"\bCHAR\b", upper):
        return "CHAR"
    if "TEXT" in upper:
        return "TEXT"
    if "BIGINT" in upper:
        return "BIGINT"
    if "SMALLINT" in upper:
        return "SMALLINT"
    if "TINYINT" in upper and "(1" in upper:
        return "BOOLEAN"
    if "BOOLEAN" in upper or upper == "BOOL":
        return "BOOLEAN"
    if "INT" in upper or "INTEGER" in upper:
        return "INT"
    if "FLOAT" in upper or "DOUBLE" in upper or "REAL" in upper:
        return "FLOAT"
    if "DATETIME" in upper:
        return "DATETIME"
    if "TIMESTAMP" in upper:
        return "TIMESTAMP"
    if "DATE" in upper:
        return "DATE"
    return upper.split("(")[0].strip()


def parse_build_db_schema(sql_path: Path) -> dict[str, dict[str, str]]:
    lines = sql_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    schema: dict[str, dict[str, str]] = {}
    current_table: Optional[str] = None
    current_columns: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        upper = line.upper()
        if current_table is None:
            create_match = re.match(r"CREATE TABLE IF NOT EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line, re.IGNORECASE)
            if create_match:
                current_table = create_match.group(1)
                current_columns = {}
            continue
        if line == ");" or line == ";":
            schema[current_table] = current_columns
            current_table = None
            current_columns = {}
            continue
        line = line.rstrip(",")
        if not line:
            continue
        upper = line.upper()
        if upper.startswith(_SKIP_PREFIXES):
            continue
        column_match = _COLUMN_RE.match(line)
        if not column_match:
            continue
        column_name = column_match.group("name")
        type_name = column_match.group("type")
        current_columns[column_name] = _normalize_sql_type(type_name)
    return schema


def read_live_db_schema() -> dict[str, dict[str, str]]:
    inspector = inspect(engine)
    schema: dict[str, dict[str, str]] = {}
    for table_name in inspector.get_table_names():
        schema[table_name] = {
            column["name"]: _normalize_sql_type(str(column["type"]))
            for column in inspector.get_columns(table_name)
        }
    return schema


def is_date_dir(name: str) -> bool:
    return bool(_DATE_DIR_RE.fullmatch(name))


def is_event_dir(name: str) -> bool:
    return bool(_EVENT_DIR_RE.fullmatch(name))


def as_plain_dict(data: Any) -> Any:
    if hasattr(data, "__dataclass_fields__"):
        return asdict(data)
    return data
