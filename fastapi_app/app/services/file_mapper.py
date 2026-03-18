from __future__ import annotations

import hashlib
from math import isfinite
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from PIL import Image


@dataclass
class TrailPointRecord:
    """Represents one frame-aligned point from the [trail] section in event.txt."""

    frame_index: int
    pixel_x: Optional[float] = None
    pixel_y: Optional[float] = None
    event_timestamp: Optional[float] = None
    coord_long: Optional[float] = None
    coord_lat: Optional[float] = None
    ams_coord_long: Optional[float] = None
    ams_coord_lat: Optional[float] = None
    centroid_coord_long: Optional[float] = None
    centroid_coord_lat: Optional[float] = None
    centroid2_coord_long: Optional[float] = None
    centroid2_coord_lat: Optional[float] = None
    gnomonic_x: Optional[float] = None
    gnomonic_y: Optional[float] = None
    brightness: Optional[float] = None
    dct: Optional[float] = None
    size: Optional[float] = None
    frame_brightness: Optional[float] = None


@dataclass
class CentroidPointRecord:
    """Represents one parsed row from centroid.txt or centroid2.txt."""

    row_index: int
    seconds_from_start: Optional[float] = None
    coord_long: Optional[float] = None
    coord_lat: Optional[float] = None
    quality: Optional[float] = None
    station_code: Optional[str] = None
    event_timestamp: Optional[float] = None


@dataclass
class ResEntryRecord:
    """Represents one parsed row from a event .res file."""

    line_no: int
    entry_type: str
    label: Optional[str]
    long1: Optional[float]
    lat1: Optional[float]
    long2: Optional[float]
    lat2: Optional[float]
    height: Optional[float]
    raw_line: str


@dataclass
class ObservationRecord:
    """Represents one observation folder before persistence."""

    station_name: str
    cam_name: str
    values: Dict[str, object]
    event_start_utc: Optional[datetime] = None
    observation_key: str = ""
    source_hash: str = ""
    trail_points: List[TrailPointRecord] = field(default_factory=list)


@dataclass
class EventRecord:
    """Represents one event folder before persistence."""

    event: Dict[str, object]
    observations: List[ObservationRecord] = field(default_factory=list)
    res_entries: List[ResEntryRecord] = field(default_factory=list)


class FileToObjectMapper:
    """Read event folders from disk and map them into persistence-ready records."""

    stat_file_map = {
        "startheight": "track_startheight",
        "endheight": "track_endheight",
        "groundtrack": "track_groundtrack",
        "course": "track_course",
        "incidence": "track_incidence",
        "speed": "track_speed",
        "speed_source": "track_speed_source",
        "error": "fit_error",
        "quality": "fit_quality",
        "ra": "radiant_ra",
        "dec": "radiant_dec",
        "ecl_long": "radiant_ecl_long",
        "ecl_lat": "radiant_ecl_lat",
        "zenith_attractor": "radiant_zenith_attractor",
        "timestamp": "timestamp",
    }

    # event.txt is sectioned and some real-world files use spaces or omit underscores.
    event_file_map = {
        "trail:frames": "trail_frames",
        "trail:duration": "trail_duration",
        "trail:slope": "trail_slope",
        "trail:offset": "trail_offset",
        "trail:speed": "trail_speed",
        "trail:correlation": "trail_correlation",
        "trail:correlation1": "trail_correlation",
        "trail:positions": "trail_positions",
        "trail:timestamps": "trail_timestamps",
        "trail:coordinates": "trail_coordinates",
        "trail:ams_coords": "trail_ams_coords",
        "trail:ams coords": "trail_ams_coords",
        "ams_coords": "trail_ams_coords",
        "trail:gnomonic": "trail_gnomonic",
        "trail:midpoint": "trail_midpoint",
        "trail:arc": "trail_arc",
        "trail:brightness": "trail_brightness",
        "trail:dct_midpoint": "trail_dct_midpoint",
        "trail:dct midpoint": "trail_dct_midpoint",
        "trail:dct": "trail_dct",
        "trail:size": "trail_size",
        "trail:frame_brightness": "trail_frame_brightness",
        "video:start": "video_start",
        "video:end": "video_end",
        "video:wallclock": "video_wallclock",
        "video:heigth": "video_heigth",
        "video:height": "video_heigth",
        "video:raw": "video_raw",
        "video:flash": "video_flash",
        "config:swidth": "config_swidth",
        "config:sheight": "config_sheight",
        "config:swdec": "config_swdec",
        "config:downscale_thr": "config_downscale_thr",
        "config:mintrail_sec": "config_mintrail_sec",
        "config:maxtrail_sec": "config_maxtrail_sec",
        "config:mintrail": "config_mintrail",
        "config:maxtrail": "config_maxtrail",
        "config:minspeed": "config_minspeed",
        "config:maxspeed": "config_maxspeed",
        "config:minspeed_kms": "config_minspeed_kms",
        "config:minspeedkms": "config_minspeed_kms",
        "config:maxspeed_kms": "config_maxspeed_kms",
        "config:maxspeedkms": "config_maxspeed_kms",
        "config:leveltest": "config_leveltest",
        "config:numspots": "config_numspots",
        "config:brightness": "config_brightness",
        "config:flash_thr": "config_flash_thr",
        "config:lookahead": "config_lookahead",
        "config:exit": "config_exit",
        "config:peak": "config_peak",
        "config:filter": "config_filter",
        "config:dct_threshold": "config_dct_threshold",
        "config:correlation": "config_correlation",
        "config:spacing_correlation": "config_spacing_correlation",
        "config:spacing correlation": "config_spacing_correlation",
        "config:gnomonic_correlation": "config_gnomonic_correlation",
        "config:gnomonic correlation": "config_gnomonic_correlation",
        "config:nothreads": "config_nothreads",
        "config:lastreport_ts": "config_lastreport_ts",
        "config:ts_future": "config_ts_future",
        "config:snapshot_interval": "config_snapshot_interval",
        "config:snapshot_integration": "config_snapshot_integration",
        "config:log_file": "config_log_file",
        "config:logfile": "config_log_file",
        "config:mask_file": "config_mask_file",
        "config:maskfile": "config_mask_file",
        "config:max_file": "config_max_file",
        "config:maxfile": "config_max_file",
        "config:save_file": "config_save_file",
        "config:savefile": "config_save_file",
        "config:pto_file": "config_pto_file",
        "config:ptofile": "config_pto_file",
        "config:pto_scale": "config_pto_scale",
        "config:ptoscale": "config_pto_scale",
        "config:pto_width": "config_pto_width",
        "config:ptowidth": "config_pto_width",
        "config:pto_height": "config_pto_height",
        "config:ptoheight": "config_pto_height",
        "config:execute": "config_execute",
        "config:event_dir": "config_event_dir",
        "config:eventdir": "config_event_dir",
        "config:snapshot_dir": "config_snapshot_dir",
        "summary:latitude": "summary_latitude",
        "summary:longitude": "summary_longitude",
        "summary:elevation": "summary_elevation",
        "summary:timestamp": "summary_timestamp",
        "summary:startpos": "summary_startpos",
        "summary:endpos": "summary_endpos",
        "summary:duration": "summary_duration",
        "summary:sunalt": "summary_sunalt",
        "summary:recalibrated": "summary_recalibrated",
        "summary:meteor_probability": "summary_meteor_probability",
        # Fallbacks for older simplified test fixtures without [section] headers.
        "frames": "trail_frames",
        "duration": "trail_duration",
        "latitude": "summary_latitude",
        "longitude": "summary_longitude",
    }

    def __init__(self, data_directory: str | Path, date_from: str, date_to: str):
        self.data_dir = Path(data_directory)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        self.date_strings = self._build_date_strings(date_from, date_to)
        self.records: List[EventRecord] = []

    @staticmethod
    def _build_date_strings(date_from: str, date_to: str) -> List[str]:
        start = datetime.strptime(date_from, "%Y%m%d")
        end = datetime.strptime(date_to, "%Y%m%d")
        if end <= start:
            end = start + timedelta(days=1)
        names: List[str] = []
        cursor = start
        while cursor < end:
            names.append(cursor.strftime("%Y%m%d"))
            cursor += timedelta(days=1)
        return names

    def map(self) -> List[EventRecord]:
        if not self.date_strings:
            return []
        available_dates = {
            entry.name for entry in self.data_dir.iterdir() if entry.is_dir()
        }
        target_dates = sorted(available_dates.intersection(self.date_strings))
        for date_folder in target_dates:
            date_path = self.data_dir / date_folder
            for event_folder in self._get_folder_content(date_path):
                event_path = date_path / event_folder
                if not event_path.is_dir():
                    continue
                record = self._process_event_folder(date_folder, event_folder, event_path)
                if record:
                    self.records.append(record)
        return self.records

    def _get_folder_content(self, path: Path) -> List[str]:
        if not path.is_dir():
            return []
        return [entry.name for entry in path.iterdir()]

    def _find_files(self, entries: Iterable[str], suffix: str) -> List[str]:
        suffix_lower = suffix.lower()
        return [name for name in entries if name.lower().endswith(suffix_lower)]

    def _load_event_location(
        self,
        event: Dict[str, object],
        event_path: Path,
        folder_entries: Iterable[str],
    ) -> None:
        """Load cross-station solved status and human-readable place text for one event."""

        has_crossbearing_results = bool(
            self._find_files(folder_entries, ".res")
            or self._find_files(folder_entries, ".stat")
            or "location.txt" in folder_entries
        )
        event["camera_confirmed"] = 1 if has_crossbearing_results else 0

        if "location.txt" in folder_entries:
            location_file = event_path / "location.txt"
            try:
                with location_file.open("r", encoding="utf-8") as handle:
                    line = handle.readline().strip()
                    event["location"] = line or None
            except OSError:
                event["location"] = None

    def _create_thumbnail(self, image_path: Path, thumbnail_path: Path) -> None:
        if not image_path.exists():
            return
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width == 0 or height == 0:
                    return
                target_width = 365
                ratio = target_width / float(width)
                target_height = int(height * ratio)
                thumbnail = img.resize((target_width, target_height), Image.LANCZOS)
                thumbnail.save(thumbnail_path)
        except OSError:
            # Skip thumbnail creation if Pillow cannot read the file
            return

    def _load_event_stat_file(
        self,
        event: Dict[str, object],
        event_path: Path,
        folder_entries: Iterable[str],
    ) -> None:
        """Load cross-station solved event properties from a .stat file when present."""

        stat_files = self._find_files(folder_entries, ".stat")
        if not stat_files:
            return
        stat_path = event_path / stat_files[0]
        try:
            with stat_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    parts = line.strip().split(" ")
                    if len(parts) < 3:
                        continue
                    key = parts[0]
                    if key in self.stat_file_map:
                        event[self.stat_file_map[key]] = " ".join(parts[2:]).strip()
                    elif key == "shower":
                        event["radiant_shower"] = " ".join(parts[2:5]).strip()
        except OSError:
            return

    def _load_res_file_data(
        self,
        event: Dict[str, object],
        event_path: Path,
        folder_entries: Iterable[str],
    ) -> List[ResEntryRecord]:
        """Load cross-station solved trajectory rows from .res and keep the raw row structure."""

        res_files = self._find_files(folder_entries, ".res")
        if not res_files:
            return []
        res_path = event_path / res_files[0]
        try:
            with res_path.open("r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError:
            return []
        if len(lines) < 2:
            return []
        coords_start = self._parse_res_coordinates(lines[0])
        coords_end = self._parse_res_coordinates(lines[1])
        if coords_start:
            event["track_startlong"], event["track_startlat"] = coords_start
        if coords_end:
            event["track_endlong"], event["track_endlat"] = coords_end
        res_entries: List[ResEntryRecord] = []
        for line_no, raw_line in enumerate(lines, start=1):
            entry = self._parse_res_entry(line_no, raw_line)
            if entry:
                res_entries.append(entry)
        return res_entries

    @staticmethod
    def _parse_res_coordinates(line: str) -> tuple[float, float] | None:
        trimmed = line.strip()
        if not trimmed:
            return None
        parts = [token for token in trimmed.split("  ") if token]
        if len(parts) < 2:
            return None
        try:
            long_value = float(parts[0])
            lat_value = float(parts[1])
            if not isfinite(long_value) or not isfinite(lat_value):
                return None
            return long_value, lat_value
        except ValueError:
            return None

    def _parse_res_entry(self, line_no: int, raw_line: str) -> ResEntryRecord | None:
        """Parse one .res row as long1/lat1/long2/lat2/height/label plus raw text."""

        tokens = raw_line.split()
        if len(tokens) < 6:
            return None
        long1 = self._safe_float(tokens[0])
        lat1 = self._safe_float(tokens[1])
        long2 = self._safe_float(tokens[2])
        lat2 = self._safe_float(tokens[3])
        height = self._safe_float(tokens[4])
        label = tokens[5]
        return ResEntryRecord(
            line_no=line_no,
            entry_type=self._classify_res_entry(label),
            label=label,
            long1=long1,
            lat1=lat1,
            long2=long2,
            lat2=lat2,
            height=height,
            raw_line=raw_line.strip(),
        )

    @staticmethod
    def _classify_res_entry(label: str) -> str:
        lowered = label.lower()
        if lowered == "start":
            return "start"
        if lowered == "end":
            return "end"
        return "station"

    def _load_event_observation_data(
        self,
        event_path: Path,
        folder_entries: Iterable[str],
    ) -> List[ObservationRecord]:
        """Load individual-camera detection and measurement data from event.txt files."""

        observations: List[ObservationRecord] = []
        for station_name in folder_entries:
            station_path = event_path / station_name
            if not station_path.is_dir():
                continue
            for cam_name in self._get_folder_content(station_path):
                cam_path = station_path / cam_name
                if not cam_path.is_dir():
                    continue
                event_file = cam_path / "event.txt"
                if not event_file.is_file():
                    continue
                try:
                    with event_file.open("r", encoding="utf-8") as handle:
                        values: Dict[str, str] = {}
                        current_section = ""
                        for raw_line in handle:
                            stripped = raw_line.strip()
                            if not stripped:
                                continue
                            if stripped.startswith("[") and stripped.endswith("]"):
                                current_section = stripped[1:-1].strip().lower()
                                continue
                            if "=" not in raw_line:
                                continue
                            key, value = raw_line.split("=", 1)
                            mapped = self._map_event_key(current_section, key.strip())
                            if mapped:
                                values[mapped] = value.strip()
                    if values:
                        centroid_text = self._read_optional_text(cam_path / "centroid.txt")
                        centroid2_text = self._read_optional_text(cam_path / "centroid2.txt")
                        if centroid_text is not None:
                            values["trail_centroid"] = centroid_text
                        if centroid2_text is not None:
                            values["trail_centroid2"] = centroid2_text
                        event_start_utc = self._extract_event_start_utc(values)
                        observation_key = self._build_observation_key(
                            station_name, cam_name, event_start_utc, values
                        )
                        observations.append(
                            ObservationRecord(
                                station_name=station_name,
                                cam_name=cam_name,
                                values=values,
                                event_start_utc=event_start_utc,
                                observation_key=observation_key,
                                source_hash=self._build_source_hash(
                                    station_name, cam_name, values
                                ),
                                trail_points=self._build_trail_points(
                                    values,
                                    centroid_text=centroid_text,
                                    centroid2_text=centroid2_text,
                                ),
                            )
                        )
                except OSError:
                    continue
        return observations

    def _map_event_key(self, section: str, key: str) -> str | None:
        scoped_key = f"{section}:{key.lower()}" if section else key.lower()
        if scoped_key in self.event_file_map:
            return self.event_file_map[scoped_key]
        return self.event_file_map.get(key.lower())

    def _extract_event_start_utc(self, values: Dict[str, object]) -> datetime | None:
        """Extract a stable UTC start time from event.txt for observation identity."""

        video_start = values.get("video_start")
        if isinstance(video_start, str):
            parsed = self._parse_event_datetime(video_start)
            if parsed:
                return parsed
        trail_timestamps = self._parse_scalar_series(values.get("trail_timestamps"))
        if trail_timestamps:
            return datetime.utcfromtimestamp(trail_timestamps[0])
        return None

    def _build_observation_key(
        self,
        station_name: str,
        cam_name: str,
        event_start_utc: datetime | None,
        values: Dict[str, object],
    ) -> str:
        """Build a stable observation identifier that survives event regrouping."""

        if event_start_utc is not None:
            return (
                f"{station_name.lower()}:{cam_name.lower()}:"
                f"{event_start_utc.isoformat(timespec='milliseconds')}"
            )
        return f"fallback:{self._build_source_hash(station_name, cam_name, values)}"

    def _build_source_hash(
        self, station_name: str, cam_name: str, values: Dict[str, object]
    ) -> str:
        """Create a deterministic fallback signature for one observation."""

        signature = "|".join(
            [
                station_name.lower(),
                cam_name.lower(),
                str(values.get("video_start", "")),
                str(values.get("trail_timestamps", "")),
                str(values.get("trail_positions", "")),
                str(values.get("trail_ams_coords", "")),
            ]
        )
        return hashlib.sha256(signature.encode("utf-8")).hexdigest()

    def _build_trail_points(
        self,
        values: Dict[str, object],
        centroid_text: Optional[str] = None,
        centroid2_text: Optional[str] = None,
    ) -> List[TrailPointRecord]:
        """Normalise parallel [trail] arrays into frame-based rows."""

        positions = self._parse_pair_series(values.get("trail_positions"))
        timestamps = self._parse_scalar_series(values.get("trail_timestamps"))
        coordinates = self._parse_pair_series(values.get("trail_coordinates"))
        ams_coordinates = self._parse_pair_series(values.get("trail_ams_coords"))
        gnomonic = self._parse_pair_series(values.get("trail_gnomonic"))
        brightness = self._parse_scalar_series(values.get("trail_brightness"))
        dct_values = self._parse_scalar_series(values.get("trail_dct"))
        size_values = self._parse_scalar_series(values.get("trail_size"))
        frame_brightness = self._parse_scalar_series(values.get("trail_frame_brightness"))

        sequences = [
            seq
            for seq in (
                positions,
                timestamps,
                coordinates,
                gnomonic,
                brightness,
                dct_values,
                size_values,
                frame_brightness,
            )
            if seq
        ]
        if not sequences:
            return []

        common_length = min(len(seq) for seq in sequences)
        points: List[TrailPointRecord] = []
        for frame_index in range(common_length):
            pixel = positions[frame_index] if frame_index < len(positions) else None
            coord = coordinates[frame_index] if frame_index < len(coordinates) else None
            ams_coord = (
                ams_coordinates[frame_index] if frame_index < len(ams_coordinates) else None
            )
            gnomonic_pair = gnomonic[frame_index] if frame_index < len(gnomonic) else None
            points.append(
                TrailPointRecord(
                    frame_index=frame_index,
                    pixel_x=pixel[0] if pixel else None,
                    pixel_y=pixel[1] if pixel else None,
                    event_timestamp=timestamps[frame_index]
                    if frame_index < len(timestamps)
                    else None,
                    coord_long=coord[0] if coord else None,
                    coord_lat=coord[1] if coord else None,
                    ams_coord_long=ams_coord[0] if ams_coord else None,
                    ams_coord_lat=ams_coord[1] if ams_coord else None,
                    gnomonic_x=gnomonic_pair[0] if gnomonic_pair else None,
                    gnomonic_y=gnomonic_pair[1] if gnomonic_pair else None,
                    brightness=brightness[frame_index]
                    if frame_index < len(brightness)
                    else None,
                    dct=dct_values[frame_index]
                    if frame_index < len(dct_values)
                    else None,
                    size=size_values[frame_index]
                    if frame_index < len(size_values)
                    else None,
                    frame_brightness=frame_brightness[frame_index]
                    if frame_index < len(frame_brightness)
                    else None,
                )
            )
        self._apply_centroid_points(
            points,
            self._parse_centroid_points(centroid_text),
            long_key="centroid_coord_long",
            lat_key="centroid_coord_lat",
        )
        self._apply_centroid_points(
            points,
            self._parse_centroid_points(centroid2_text),
            long_key="centroid2_coord_long",
            lat_key="centroid2_coord_lat",
        )
        return points

    @staticmethod
    def _read_optional_text(path: Path) -> Optional[str]:
        try:
            if not path.is_file():
                return None
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def _parse_centroid_points(self, raw_text: object) -> List[CentroidPointRecord]:
        if not isinstance(raw_text, str):
            return []

        points: List[CentroidPointRecord] = []
        for raw_line in raw_text.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) < 9:
                continue
            row_index = self._safe_int(parts[0])
            seconds_from_start = self._safe_float(parts[1])
            coord_lat = self._safe_float(parts[2])
            coord_long = self._safe_float(parts[3])
            quality = self._safe_float(parts[4])
            station_code = parts[5]
            timestamp = self._parse_centroid_timestamp(parts[6], parts[7], parts[8])
            if row_index is None:
                row_index = len(points)
            points.append(
                CentroidPointRecord(
                    row_index=row_index,
                    seconds_from_start=seconds_from_start,
                    coord_long=coord_long,
                    coord_lat=coord_lat,
                    quality=quality,
                    station_code=station_code,
                    event_timestamp=timestamp,
                )
            )
        return points

    def _apply_centroid_points(
        self,
        points: List[TrailPointRecord],
        centroid_points: List[CentroidPointRecord],
        *,
        long_key: str,
        lat_key: str,
    ) -> None:
        if not points or not centroid_points:
            return

        matches = self._match_centroid_points(points, centroid_points)
        for index, centroid_point in matches.items():
            setattr(points[index], long_key, centroid_point.coord_long)
            setattr(points[index], lat_key, centroid_point.coord_lat)

    def _match_centroid_points(
        self,
        trail_points: List[TrailPointRecord],
        centroid_points: List[CentroidPointRecord],
    ) -> Dict[int, CentroidPointRecord]:
        centroid_by_timestamp: Dict[int, List[CentroidPointRecord]] = {}
        for point in centroid_points:
            key = self._timestamp_match_key(point.event_timestamp)
            if key is None:
                continue
            centroid_by_timestamp.setdefault(key, []).append(point)

        matches: Dict[int, CentroidPointRecord] = {}
        for index, trail_point in enumerate(trail_points):
            key = self._timestamp_match_key(trail_point.event_timestamp)
            if key is None:
                continue
            candidates = centroid_by_timestamp.get(key)
            if candidates:
                matches[index] = candidates.pop(0)

        if matches:
            return matches
        if len(trail_points) != len(centroid_points):
            return {}
        return {index: centroid_point for index, centroid_point in enumerate(centroid_points)}

    @staticmethod
    def _timestamp_match_key(timestamp: Optional[float]) -> Optional[int]:
        if timestamp is None:
            return None
        return int(round(timestamp * 1_000_000))

    @staticmethod
    def _parse_centroid_timestamp(
        date_part: str, time_part: str, timezone_part: str
    ) -> Optional[float]:
        if timezone_part.upper() != "UTC":
            return None
        candidate = f"{date_part} {time_part}"
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return (
                    datetime.strptime(candidate, fmt)
                    .replace(tzinfo=timezone.utc)
                    .timestamp()
                )
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_event_datetime(raw_value: str) -> datetime | None:
        """Parse the leading UTC timestamp from event.txt video/summary fields."""

        match = re.match(r"^\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)", raw_value)
        if not match:
            return None
        candidate = match.group(1)
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
        return None

    def _parse_pair_series(self, raw_value: object) -> List[tuple[float, float]]:
        if not isinstance(raw_value, str):
            return []
        pairs: List[tuple[float, float]] = []
        for token in raw_value.split():
            if "," not in token:
                continue
            left, right = token.split(",", 1)
            left_value = self._safe_float(left)
            right_value = self._safe_float(right)
            if left_value is None or right_value is None:
                continue
            pairs.append((left_value, right_value))
        return pairs

    def _parse_scalar_series(self, raw_value: object) -> List[float]:
        if not isinstance(raw_value, str):
            return []
        values: List[float] = []
        for token in raw_value.split():
            parsed = self._safe_float(token)
            if parsed is not None:
                values.append(parsed)
        return values

    @staticmethod
    def _safe_float(raw_value: object) -> float | None:
        try:
            parsed = float(raw_value)
            if not isfinite(parsed):
                return None
            return parsed
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(raw_value: object) -> int | None:
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    def _process_event_folder(
        self, date_folder: str, event_folder: str, event_path: Path
    ) -> EventRecord | None:
        event_image = event_path / "image.jpg"
        thumbnail_path = event_path / "thumbnail.jpg"
        self._create_thumbnail(event_image, thumbnail_path)

        datetimetag = f"{date_folder}{event_folder}"
        event_payload: Dict[str, object] = {"datetimetag": datetimetag}
        try:
            event_payload["date"] = datetime.strptime(
                datetimetag[:14], "%Y%m%d%H%M%S"
            )
        except ValueError:
            event_payload["date"] = None

        folder_entries = self._get_folder_content(event_path)
        self._load_event_location(event_payload, event_path, folder_entries)
        self._load_event_stat_file(event_payload, event_path, folder_entries)
        res_entries = self._load_res_file_data(event_payload, event_path, folder_entries)
        observations = self._load_event_observation_data(event_path, folder_entries)

        return EventRecord(
            event=event_payload,
            observations=observations,
            res_entries=res_entries,
        )
