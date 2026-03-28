from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MeteorSchema(BaseModel):
    class Config:
        extra = "allow"


class EventFilterParams(BaseModel):
    stationName: Optional[str] = None
    year: Optional[str] = None
    eventType: Optional[str] = None
    searchTerm: Optional[str] = None
    page: int = 1
    limit: int = 20
    orderby: str = "date"
    order: str = "desc"


class EventFilterOptionsResponse(MeteorSchema):
    years: List[str] = Field(
        ...,
        description="Available year values for event filtering.",
    )
    stations: List[str] = Field(
        ...,
        description="Available station names for event filtering.",
    )
    eventTypes: List[str] = Field(
        ...,
        description="Available public event types for event filtering.",
    )


class EventReviewRequest(BaseModel):
    eventID: Optional[int] = Field(
        default=None,
        alias="eventID",
        description="Optional event id in the payload. Must match the URL event id when sent, otherwise the request is rejected with 400.",
    )
    userID: Optional[int] = Field(
        default=None,
        alias="userID",
        description="Optional user id in the payload. Must match the authenticated token user when sent, otherwise the request is rejected with 400.",
    )
    confirmed: str = Field(
        ...,
        description="Review value. Accepted values today are Positive, Negative, 1, and 0. Positive and 1 are treated as yes, while Negative and 0 are treated as no.",
    )


class EventClassificationUpdate(BaseModel):
    user_confirmed: Optional[str] = Field(
        default=None,
        description="Classification input. Accepted values today are Positive, Negative, 1, and 0. Positive and 1 map to confirmed meteor, while Negative and 0 map to not meteor.",
    )


class InsightReportName(str, Enum):
    cam = "cam"
    station = "station"
    total = "total"
    coordinates = "coordinates"


class ArtifactRole(str, Enum):
    preview_thumbnail = "preview_thumbnail"
    event_preview = "event_preview"
    trajectory_map = "trajectory_map"
    height_profile = "height_profile"
    speed_acceleration = "speed_acceleration"
    position_vs_time = "position_vs_time"
    heliocentric_orbit = "heliocentric_orbit"
    kml = "kml"
    dynamic_analysis_report = "dynamic_analysis_report"
    station_analysis = "station_analysis"
    analysis_tables = "analysis_tables"
    observation_preview = "observation_preview"
    raw_image = "raw_image"
    raw_video = "raw_video"
    processed_image = "processed_image"
    processed_video = "processed_video"
    brightness_graph = "brightness_graph"
    frame_brightness_graph = "frame_brightness_graph"
    size_graph = "size_graph"
    observation_text = "observation_text"


class ArtifactType(str, Enum):
    image = "image"
    video = "video"
    text = "text"
    interactive = "interactive"


class ArtifactVisibility(str, Enum):
    public = "public"


class ArtifactPrimaryAction(str, Enum):
    open = "open"
    download = "download"


class EventTimes(MeteorSchema):
    utc: str | None = Field(
        default=None,
        nullable=True,
        description="UTC timestamp used as the main machine-readable event time. Null means the backend could not derive a stable event time from current source data.",
    )
    local: str | None = Field(
        default=None,
        nullable=True,
        description="Local public display time serialised by the backend in the configured public timezone, not in the browser timezone. Null means the backend could not derive a stable event time from current source data.",
    )
    timezone: str = Field(
        ...,
        description="Configured public timezone for local time serialisation.",
    )


class CandidateStatus(MeteorSchema):
    is_candidate: bool = Field(
        ...,
        description="True when the event matches the active meteorite-candidate thresholds.",
    )
    max_end_height_km: float = Field(
        ...,
        description="Maximum end height threshold currently used by the backend.",
    )
    max_speed_kms: float = Field(
        ...,
        description="Maximum speed threshold currently used by the backend.",
    )


class CandidateSettings(MeteorSchema):
    max_end_height_km: float = Field(
        ...,
        description="Maximum end height threshold currently used by the backend.",
    )
    max_speed_kms: float = Field(
        ...,
        description="Maximum speed threshold currently used by the backend.",
    )


class ArtifactManifestItem(MeteorSchema):
    id: str = Field(..., description="Stable artifact identifier within the response.")
    role: "ArtifactRole" = Field(
        ...,
        description="Presentation role for the artifact.",
    )
    type: "ArtifactType" = Field(
        ...,
        description="Artifact type.",
    )
    level: str = Field(..., description="Artifact scope. Current values are event or observation.")
    language: Optional[str] = Field(
        default=None,
        description="Language variant when available. Null means the artifact uses the default file variant without a language prefix, which in current public file naming usually means the Norwegian base file.",
    )
    url: str = Field(..., description="Resolved public URL for opening or downloading the artifact.")
    interactive: bool = Field(..., description="True when the artifact should be treated as interactive content.")
    primary_action: "ArtifactPrimaryAction" = Field(
        ...,
        description="Primary UI action.",
    )
    downloadable: bool = Field(..., description="Whether the artifact is intended to be downloadable.")
    visibility: "ArtifactVisibility" = Field(
        ...,
        description="Visibility hint for the frontend.",
    )
    observation_ref: Optional[str] = Field(
        default=None,
        description="Observation key when the artifact belongs to a specific observation. Null means the artifact belongs to the event level rather than one observation package.",
    )


class EventPreview(MeteorSchema):
    type: Optional[str] = Field(
        default=None,
        description="Preview media type. Null means no preview type is available.",
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Thumbnail preview URL. Null means no list/detail thumbnail is available.",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Primary still-image preview URL. Null means no still preview is available.",
    )
    has_preview: bool = Field(..., description="True when at least one preview artifact exists.")


class StationSummary(MeteorSchema):
    station_count: int = Field(..., description="Number of unique stations represented in the event response.")
    observation_count: int = Field(..., description="Number of visible observations in the event response.")
    stations: List[str] = Field(..., description="Unique station names used in the event response.")
    cameras: List[str] = Field(..., description="Camera labels derived from visible observations.")
    label: Optional[str] = Field(
        default=None,
        description="Short compact station/camera summary for cards and compact views, for example a combined label built from the visible stations or cameras in the response.",
    )


class TechnicalValidity(MeteorSchema):
    is_valid: bool = Field(..., description="High-level public validity flag.")
    is_deleted: bool = Field(..., description="Soft-delete state from ingestion lifecycle.")
    source_bad_detection: Optional[bool] = Field(
        default=None,
        description="True when the event source is known to come from an incorrect-detection bucket. Null means this indicator is not yet sourced in the current backend.",
    )
    proper_triangulation: Optional[bool] = Field(
        default=None,
        description="True when the solved event geometry passes the backend's basic sanity checks. Null means the backend does not yet have enough source data to state this reliably.",
    )


class ObservationRef(MeteorSchema):
    id: int = Field(..., description="Observation database id.")
    observation_key: str = Field(..., description="Stable observation identity across regrouping.")
    station_name: Optional[str] = Field(
        default=None,
        description="Station name when known. Null means the relation is missing in the loaded response.",
    )
    cam_name: Optional[str] = Field(
        default=None,
        description="Camera name when known. Null means the relation is missing in the loaded response.",
    )
    event_start_utc: Optional[str] = Field(
        default=None,
        description="Machine-readable UTC observation start time when extracted from source files.",
    )


class ObservationPreview(MeteorSchema):
    thumbnail_url: Optional[str] = Field(
        default=None,
        description="Observation preview image. Null means no preview image is available.",
    )
    open_url: Optional[str] = Field(
        default=None,
        description="Best opening target for the observation. Null means no direct opening target is available.",
    )
    type: Optional[str] = Field(
        default=None,
        description="Preview/open target type. Null means the backend cannot determine a display type.",
    )


class MeteorObservation(MeteorSchema):
    observation_ref: ObservationRef
    artifacts: List[ArtifactManifestItem] = Field(
        ...,
        description="Observation-level artifact manifest.",
    )
    preview: ObservationPreview
    has_ams_coords: bool = Field(
        False,
        description="True when this observation includes AMS trail coordinates in addition to the standard trail coordinate series.",
    )


class MeteorEventHeader(MeteorSchema):
    id: int = Field(..., description="Event database id.")
    event_path: str = Field(..., description="Public event path built from date and time folders.")
    title: str = Field(..., description="User-facing title prepared for public list/detail views.")
    location: Optional[str] = Field(
        default=None,
        description="Public place name when known. Null means no place text is available.",
    )
    times: EventTimes
    cross_station_confirmed: bool = Field(..., description="Public cross-station status.")


class MeteorEventSummaryBasis(MeteorSchema):
    location: Optional[str] = Field(
        default=None,
        description="Location value used when building dynamic summary text.",
    )
    station_summary: StationSummary
    shower: Optional[str] = Field(
        default=None,
        description="Meteor shower value used when building dynamic summary text. Null means no shower is assigned.",
    )
    candidate: CandidateStatus


class MeteorEventTitleBasis(MeteorSchema):
    event_type: str = Field(
        ...,
        description="Public event type used when building the title.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Location value used when building the title. Null means the title falls back to time-based wording.",
    )
    cross_station_confirmed: bool = Field(
        ...,
        description="Cross-station status used when building the title.",
    )


class AtmosphericStationPoint(MeteorSchema):
    observation_key: Optional[str] = Field(
        default=None,
        description="Observation key for the contributing observation when available.",
    )
    station_name: Optional[str] = Field(
        default=None,
        description="Station name for the contributing observation when available.",
    )
    cam_name: Optional[str] = Field(
        default=None,
        description="Camera name for the contributing observation when available.",
    )
    station_lat: Optional[float] = Field(
        default=None,
        description="Observation-side station or camera latitude basis when available from summary data.",
    )
    station_lng: Optional[float] = Field(
        default=None,
        description="Observation-side station or camera longitude basis when available from summary data.",
    )
    station_elevation_m: Optional[float] = Field(
        default=None,
        description="Observation-side elevation basis in metres when available from summary data.",
    )
    start_lat: Optional[float] = Field(
        default=None,
        description="Reserved for observation-linked start latitude when that source is connected.",
    )
    start_lng: Optional[float] = Field(
        default=None,
        description="Reserved for observation-linked start longitude when that source is connected.",
    )
    end_lat: Optional[float] = Field(
        default=None,
        description="Reserved for observation-linked end latitude when that source is connected.",
    )
    end_lng: Optional[float] = Field(
        default=None,
        description="Reserved for observation-linked end longitude when that source is connected.",
    )


class AtmosphericGeometryPoint(MeteorSchema):
    step_index: int = Field(
        ...,
        description="Zero-based sample index along the atmospheric path.",
    )
    fraction: float = Field(
        ...,
        description="Relative path position from 0 at the solved start point to 1 at the solved end point.",
    )
    lat: float = Field(
        ...,
        description="Sampled atmospheric latitude.",
    )
    lng: float = Field(
        ...,
        description="Sampled atmospheric longitude.",
    )
    height_km: float = Field(
        ...,
        description="Sampled atmospheric height in km.",
    )


class MeteorEventClassification(MeteorSchema):
    final_classification: str = Field(
        ...,
        description="Public final classification. Current values are Meteor, Ikke meteor, and Usikker.",
    )
    cross_station_confirmed: bool = Field(..., description="Public cross-station status.")
    user_confirmed: Optional[int] = Field(
        default=None,
        description="Stored moderation value used by the backend. Current runtime uses 1 for meteor, 0 for ikke meteor, and -1 or null for unclear.",
    )


class AtmosphericPath(MeteorSchema):
    start_height_km: Optional[float] = Field(
        default=None,
        description="Calculated atmospheric start height. Null means no solved path value is available.",
    )
    end_height_km: Optional[float] = Field(
        default=None,
        description="Calculated atmospheric end height. Null means no solved path value is available.",
    )
    start_lat: Optional[float] = Field(
        default=None,
        description="Calculated start latitude. Null means no solved path value is available.",
    )
    start_lng: Optional[float] = Field(
        default=None,
        description="Calculated start longitude. Null means no solved path value is available.",
    )
    end_lat: Optional[float] = Field(
        default=None,
        description="Calculated end latitude. Null means no solved path value is available.",
    )
    end_lng: Optional[float] = Field(
        default=None,
        description="Calculated end longitude. Null means no solved path value is available.",
    )
    course_deg: Optional[float] = Field(
        default=None,
        description="Solved course in degrees. Null means the source file did not provide a value.",
    )
    incidence_deg: Optional[float] = Field(
        default=None,
        description="Solved incidence angle in degrees. Null means the source file did not provide a value.",
    )
    speed_kms: Optional[float] = Field(
        default=None,
        description="Solved speed in km/s. Null means the source file did not provide a value.",
    )
    speed_source: Optional[str] = Field(
        default=None,
        description="Raw source label for the solved speed, for example `average` when the stat file does not claim an entry-speed solution. The orbit line uses this as provenance for the fallback speed path, not as a promise that the observed fit won.",
    )
    geometry_points: Optional[List[AtmosphericGeometryPoint]] = Field(
        default=None,
        description="Sampled atmospheric path geometry for dynamic rendering. Null means the backend could not derive a solved start or end line to sample from current event data.",
    )
    station_points: List[AtmosphericStationPoint] = Field(
        ...,
        description="Observation-linked station and summary points used when rendering solved atmospheric path views. Each item currently gives station or camera basis plus placeholder start or end fields for future richer geometry.",
    )


class RadiantPayload(MeteorSchema):
    ra: float | None = Field(
        default=None,
        nullable=True,
        description="Right ascension. Null means no radiant solution is available.",
    )
    dec: float | None = Field(
        default=None,
        nullable=True,
        description="Declination. Null means no radiant solution is available.",
    )
    shower: Optional[str] = Field(
        default=None,
        description="Meteor shower assignment. Null means no shower is assigned.",
    )
    zenith_attractor: Optional[str] = Field(
        default=None,
        description="Raw radiant correction state from the stat file, for example `uncorrected` when the solved radiant still needs zenith-attraction handling.",
    )


class OrbitPayload(MeteorSchema):
    perihelion_distance_au: Optional[float] = Field(
        default=None,
        description="Calculated perihelion distance in AU. Cross-station events first try an observation-driven solve from trail timestamps and coordinates, including AMS coordinates when present. That solve gives late trail points lower weight, keeps per-camera timing offsets, and can be benchmarked against a weak deceleration candidate along the same straight path. Runtime keeps the observed solve only when the trail fit stays stable and close to the stat-based fallback; otherwise it falls back to the older stat solve. Null means the backend could not derive an orbit from current event data.",
    )
    eccentricity: Optional[float] = Field(
        default=None,
        description="Calculated eccentricity from the same orbit solve path as `perihelion_distance_au`. Null means the backend could not derive an orbit from current event data.",
    )
    inclination_deg: Optional[float] = Field(
        default=None,
        description="Calculated inclination in degrees from the same orbit solve path as `perihelion_distance_au`. Null means the backend could not derive an orbit from current event data.",
    )
    ascending_node_deg: Optional[float] = Field(
        default=None,
        description="Calculated ascending node in degrees from the same orbit solve path as `perihelion_distance_au`. Null means the backend could not derive an orbit from current event data.",
    )
    argument_of_perihelion_deg: Optional[float] = Field(
        default=None,
        description="Calculated argument of perihelion in degrees from the same orbit solve path as `perihelion_distance_au`. Null means the backend could not derive an orbit from current event data.",
    )
    mean_anomaly_deg: Optional[float] = Field(
        default=None,
        description="Calculated mean anomaly in degrees from the same orbit solve path as `perihelion_distance_au`. Elliptic solutions are reported in the standard `0..360` range; hyperbolic solutions keep the direct solved value. Observation-driven solves are kept only when the fitted trail geometry stays stable after late-point handling and per-camera timing treatment. When geometry is good enough but mean anomaly still drifts, runtime reuses the fallback mean anomaly from the older stat-based line. Null means the backend could not derive an orbit from current event data.",
    )
    epoch: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp used as orbital epoch when the backend derived orbit values. Observation-driven solves normally use the earliest fitted trail timestamp after the per-camera timing fit, but runtime reuses the fallback epoch when it keeps the observed geometry and only stabilizes mean anomaly from the fallback line. Stat-based fallback uses the stored event timestamp. Null means the backend could not derive an orbit from current event data.",
    )


class MeteorEventAnalysis(MeteorSchema):
    atmospheric_path: AtmosphericPath
    radiant: RadiantPayload
    orbit: OrbitPayload
    artifacts: List[ArtifactManifestItem] = Field(
        ...,
        description="Event-level analysis artifacts and files.",
    )


class MeteorEvent(MeteorSchema):
    id: int = Field(..., description="Event database id.")
    location: str | None = Field(
        default=None,
        nullable=True,
        description="Public place name when known. Null means no place text is available.",
    )
    event_type: str = Field(..., description="Public list/detail event type.")
    cross_station_confirmed: bool = Field(..., description="Public cross-station status.")
    event_path: str = Field(..., description="Path built from date and time folders.")
    public_url: str | None = Field(
        default=None,
        nullable=True,
        description="Public frontend URL when FRONT_URL is configured. Null means no public frontend base URL is configured.",
    )
    event_artifacts: List[ArtifactManifestItem]
    preview: EventPreview
    candidate: CandidateStatus
    final_classification: str = Field(..., description="Public final classification.")
    times: EventTimes
    title: str = Field(..., description="User-facing event title.")
    title_basis: MeteorEventTitleBasis = Field(
        ...,
        description="Structured basis used to build the public title. Frontend should treat this as explanation data, not as a second title source.",
    )
    station_summary: StationSummary
    station_count: int = Field(..., description="Number of unique stations in the visible response.")
    observation_count: int = Field(..., description="Number of visible observations in the visible response.")
    shower: Optional[str] = Field(
        default=None,
        description="Meteor shower when known. Null means no shower is assigned.",
    )
    ai_score: float | None = Field(
        default=None,
        nullable=True,
        description="Highest available observation-side meteor probability when the backend has one. Null means no usable probability was available in the current event data.",
    )
    technical_validity: TechnicalValidity
    header: MeteorEventHeader
    summary_basis: MeteorEventSummaryBasis
    classification: MeteorEventClassification
    analysis: Optional[MeteorEventAnalysis] = Field(
        default=None,
        description="Detailed analysis payload. Null or omitted in list contexts that do not include full analysis blocks.",
    )
    observations: Optional[List[MeteorObservation]] = Field(
        default=None,
        description="Observation packages for detail views. Null or omitted in responses that do not include relationships.",
    )


class MeteorEventListResponse(MeteorSchema):
    totalItems: int = Field(..., description="Total number of items matching the current query.")
    events: List[MeteorEvent] = Field(
        ...,
        description="Paginated meteor events. Each object is rich enough for list rendering without a follow-up detail request.",
    )
    totalPages: int = Field(..., description="Total page count for the current query.")
    currentPage: int = Field(..., description="Current page number.")


class AdminMeteorEvent(MeteorEvent):
    datetimetag: str = Field(
        ...,
        description="Event folder tag. Usually `YYYYMMDDHHMMSS`, but some imported events also have a suffix such as `YYYYMMDDHHMMSSb`.",
    )
    date: Optional[str] = Field(
        default=None,
        description="Event timestamp in ISO form when available.",
    )
    camera_confirmed: int = Field(
        ...,
        description="Top-level admin compatibility value for cross-station status. Current runtime uses 1 for yes and 0 for no.",
    )
    user_confirmed: int = Field(
        ...,
        description="Top-level admin compatibility value for moderation status. Current runtime uses 1 for meteor, 0 for not meteor, and -1 for unclear.",
    )
    ratings: int = Field(
        ...,
        description="Total number of stored user reviews for this event.",
    )
    positive_ratings: int = Field(
        ...,
        description="Number of positive user reviews for this event.",
    )
    negative_ratings: int = Field(
        ...,
        description="Number of negative user reviews for this event.",
    )


class AdminMeteorEventListResponse(MeteorSchema):
    totalItems: int = Field(..., description="Total number of items matching the current query.")
    events: List[AdminMeteorEvent] = Field(
        ...,
        description="Paginated admin event-board rows with review counters.",
    )
    totalPages: int = Field(..., description="Total page count for the current query.")
    currentPage: int = Field(..., description="Current page number.")


class MeteorResEntry(MeteorSchema):
    id: int
    line_no: int = Field(..., description="Line number in the stored .res file.")
    entry_type: str = Field(
        ...,
        description="Parsed row type. Current runtime values are typically start, end, or station.",
    )
    label: Optional[str] = Field(
        default=None,
        description="Source label from the .res row, for example Start or End when present.",
    )
    long1: Optional[float] = Field(
        default=None,
        description="First longitude value from the .res row. Event-level start/end coordinates are currently taken from this first coordinate pair on row 1 and row 2.",
    )
    lat1: Optional[float] = Field(
        default=None,
        description="First latitude value from the .res row. Event-level start/end coordinates are currently taken from this first coordinate pair on row 1 and row 2.",
    )
    long2: Optional[float] = Field(
        default=None,
        description="Second longitude value from the same .res row. Its exact public semantics are not fully locked yet and it currently looks redundant or rounded in observed samples.",
    )
    lat2: Optional[float] = Field(
        default=None,
        description="Second latitude value from the same .res row. Its exact public semantics are not fully locked yet and it currently looks redundant or rounded in observed samples.",
    )
    height: Optional[float] = Field(
        default=None,
        description="Height value stored on the same .res row as the coordinate pairs.",
    )
    raw_line: str = Field(..., description="Original stored .res line.")


class MeteorResEntriesResponse(MeteorSchema):
    totalItems: int
    limit: int
    offset: int
    resEntries: List[MeteorResEntry] = Field(
        ...,
        description="Stored .res rows for one event. In practice this is row-based solved trajectory or geometry output for a cross-station event, with Start and End as the clearest row types today.",
    )


class MeteorTrailPoint(MeteorSchema):
    frame_index: int = Field(..., description="Frame index within the stored trail sequence.")
    pixel_x: Optional[float] = Field(default=None, description="Pixel x position when available.")
    pixel_y: Optional[float] = Field(default=None, description="Pixel y position when available.")
    event_timestamp_us: Optional[int] = Field(
        default=None,
        description="Exact event timestamp in Unix microseconds stored in the database.",
    )
    event_timestamp: Optional[float] = Field(
        default=None,
        description="Convenience event timestamp in Unix seconds derived from event_timestamp_us.",
    )
    coord_long: Optional[float] = Field(default=None, description="Solved longitude when available.")
    coord_lat: Optional[float] = Field(default=None, description="Solved latitude when available.")
    ams_coord_long: Optional[float] = Field(
        default=None,
        description="AMS trail longitude when that alternative coordinate series exists for this frame.",
    )
    ams_coord_lat: Optional[float] = Field(
        default=None,
        description="AMS trail latitude when that alternative coordinate series exists for this frame.",
    )
    centroid_coord_long: Optional[float] = Field(
        default=None,
        description="Longitude from `centroid.txt` when that file exists and the row could be matched to this frame.",
    )
    centroid_coord_lat: Optional[float] = Field(
        default=None,
        description="Latitude from `centroid.txt` when that file exists and the row could be matched to this frame.",
    )
    centroid2_coord_long: Optional[float] = Field(
        default=None,
        description="Longitude from `centroid2.txt` when that file exists and the row could be matched to this frame.",
    )
    centroid2_coord_lat: Optional[float] = Field(
        default=None,
        description="Latitude from `centroid2.txt` when that file exists and the row could be matched to this frame.",
    )
    gnomonic_x: Optional[float] = Field(
        default=None,
        description="Frame-aligned gnomonic x value when available from the raw trail series.",
    )
    gnomonic_y: Optional[float] = Field(
        default=None,
        description="Frame-aligned gnomonic y value when available from the raw trail series.",
    )
    brightness: Optional[float] = Field(
        default=None,
        description="Frame-aligned brightness value when available from the raw trail series.",
    )
    dct: Optional[float] = Field(
        default=None,
        description="Frame-aligned DCT-derived value when available from the raw trail series.",
    )
    size: Optional[float] = Field(
        default=None,
        description="Frame-aligned size value when available from the raw trail series.",
    )
    frame_brightness: Optional[float] = Field(
        default=None,
        description="Frame-aligned frame brightness value when available from the raw trail series.",
    )


class MeteorObservationTrailResponse(MeteorSchema):
    totalItems: int
    limit: int
    offset: int
    has_ams_coords: bool = Field(
        False,
        description="True when the stored observation contains AMS trail coordinates for at least one frame.",
    )
    has_centroid: bool = Field(
        False,
        description="True when the stored observation contains raw data from `centroid.txt`.",
    )
    has_centroid2: bool = Field(
        False,
        description="True when the stored observation contains raw data from `centroid2.txt`.",
    )
    trailPoints: List[MeteorTrailPoint] = Field(
        ...,
        description="Frame-aligned trail points normalised from the raw trail series in one observation event.txt file.",
    )


class InsightFilterRequest(MeteorSchema):
    from_date: Optional[str] = Field(
        default=None,
        description="Inclusive start date in `YYYY-MM-DD` form.",
    )
    to_date: Optional[str] = Field(
        default=None,
        description="Inclusive end date in `YYYY-MM-DD` form.",
    )
    stations: List[str] = Field(
        default_factory=list,
        description="Selected station names for the report filter.",
    )
    cross_station_confirmed: Optional[bool] = Field(
        default=None,
        description="Optional cross-station filter. Null means no explicit filter was applied.",
    )
    candidate: bool = Field(
        default=False,
        description="Set true to keep only candidate events in the report.",
    )
    includeDeleted: bool = Field(
        default=False,
        description="Set true to include rows backed by deleted events.",
    )


class InsightReportRowBase(BaseModel):
    ForsteObservasjonsTidspunkt: Optional[datetime] = Field(
        default=None,
        description="First observation timestamp in the report.",
    )
    SisteObervasjonsTidspunkt: Optional[datetime] = Field(
        default=None,
        description="Last observation timestamp in the report.",
    )
    DagerMedObservasjoner: int = Field(
        ...,
        description="Number of calendar days with observations in the report.",
    )
    DagerSidenSisteObservasjon: Optional[int] = Field(
        default=None,
        description="Days since the latest observation in the report.",
    )
    Kameraopptak: int = Field(
        ...,
        description="Number of camera recordings in the report.",
    )
    Hendelser: int = Field(..., description="Number of events in the report.")
    Krysspeilede: int = Field(
        ...,
        description="Number of cross-station confirmed events in the report.",
    )
    Meteorittkandidater: int = Field(
        ...,
        description="Number of meteorite candidates in the report.",
    )


class InsightCamRow(InsightReportRowBase):
    Stasjonsnavn: Optional[str] = Field(
        default=None,
        description="Station name for the grouped camera row.",
    )
    Kameranavn: Optional[str] = Field(
        default=None,
        description="Camera name for the grouped camera row.",
    )


class InsightStationRow(InsightReportRowBase):
    Stasjonsnavn: Optional[str] = Field(
        default=None,
        description="Station name for the grouped station row.",
    )


class InsightTotalRow(InsightReportRowBase):
    pass


class InsightCoordinateRow(MeteorSchema):
    id: int = Field(..., description="Event database id.")
    datetimetag: str = Field(
        ...,
        description="Event folder tag. Usually `YYYYMMDDHHMMSS`, but some imported events also have a suffix such as `YYYYMMDDHHMMSSb`.",
    )
    station_cam: str = Field(
        ...,
        description="Comma-separated `cam@station` labels for observations linked to the event.",
    )
    number_of_stations: int = Field(
        ...,
        description="Number of unique stations represented in the solved event.",
    )
    lat: float = Field(..., description="Solved end latitude.")
    lng: float = Field(..., description="Solved end longitude.")
    slat: Optional[float] = Field(
        default=None,
        description="Solved start latitude when available.",
    )
    slng: Optional[float] = Field(
        default=None,
        description="Solved start longitude when available.",
    )
    radiant_ra: Optional[float] = Field(
        default=None,
        description="Solved radiant right ascension when available.",
    )
    radiant_dec: Optional[float] = Field(
        default=None,
        description="Solved radiant declination when available.",
    )
    radiant_ecl_lat: Optional[float] = Field(
        default=None,
        description="Solved radiant ecliptic latitude when available.",
    )
    radiant_ecl_long: Optional[float] = Field(
        default=None,
        description="Solved radiant ecliptic longitude when available.",
    )
    track_speed: Optional[float] = Field(
        default=None,
        description="Solved speed in km/s when available.",
    )
    track_endheight: Optional[float] = Field(
        default=None,
        description="Solved end height in km when available.",
    )
    radiant_shower: Optional[str] = Field(
        default=None,
        description="Meteor shower assignment when available.",
    )
    date: Optional[str] = Field(
        default=None,
        description="Event time serialised as ISO timestamp when available.",
    )
    triangulation: bool = Field(
        ...,
        description="True when the backend has a basic solved radiant and trajectory set for the event.",
    )
    proper_triangulation: Optional[bool] = Field(
        default=None,
        description="True when the solved event geometry passes the backend's basic sanity checks. Null means not enough source data.",
    )
    ai_score: Optional[float] = Field(
        default=None,
        description="Highest available observation-side meteor probability when present.",
    )
