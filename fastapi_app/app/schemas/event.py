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


class EventTimes(MeteorSchema):
    utc: Optional[str] = Field(
        default=None,
        description="UTC timestamp used as the main machine-readable event time. Null means the backend could not derive a stable event time from current source data.",
    )
    local: Optional[str] = Field(
        default=None,
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
    role: str = Field(..., description="Presentation role, for example preview, map, kml, or raw_video.")
    type: str = Field(..., description="Artifact type, for example image, video, text, or interactive.")
    level: str = Field(..., description="Artifact scope. Current values are event or observation.")
    language: Optional[str] = Field(
        default=None,
        description="Language variant when available. Null means the artifact uses the default file variant without a language prefix, which in current public file naming usually means the Norwegian base file.",
    )
    url: str = Field(..., description="Resolved public URL for opening or downloading the artifact.")
    interactive: bool = Field(..., description="True when the artifact should be treated as interactive content.")
    primary_action: str = Field(..., description="Primary UI action, for example open or download.")
    downloadable: bool = Field(..., description="Whether the artifact is intended to be downloadable.")
    visibility: str = Field(..., description="Visibility hint for the frontend.")
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
    geometry_points: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Reserved for explicit sampled path geometry for dynamic 3D or map rendering. Null means this backend does not yet expose sampled path points.",
    )
    station_points: List[AtmosphericStationPoint] = Field(
        ...,
        description="Observation-linked station and summary points used when rendering solved atmospheric path views. Each item currently gives station or camera basis plus placeholder start or end fields for future richer geometry.",
    )


class RadiantPayload(MeteorSchema):
    ra: Optional[float] = Field(
        default=None,
        description="Right ascension. Null means no radiant solution is available.",
    )
    dec: Optional[float] = Field(
        default=None,
        description="Declination. Null means no radiant solution is available.",
    )
    shower: Optional[str] = Field(
        default=None,
        description="Meteor shower assignment. Null means no shower is assigned.",
    )


class OrbitPayload(MeteorSchema):
    perihelion_distance_au: Optional[float] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose this orbital element.",
    )
    eccentricity: Optional[float] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose this orbital element.",
    )
    inclination_deg: Optional[float] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose this orbital element.",
    )
    ascending_node_deg: Optional[float] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose this orbital element.",
    )
    argument_of_perihelion_deg: Optional[float] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose this orbital element.",
    )
    mean_anomaly_deg: Optional[float] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose this orbital element.",
    )
    epoch: Optional[str] = Field(
        default=None,
        description="Null means the backend does not yet ingest or expose a machine-readable orbital epoch.",
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
    location: Optional[str] = Field(
        default=None,
        description="Public place name when known. Null means no place text is available.",
    )
    event_type: str = Field(..., description="Public list/detail event type.")
    cross_station_confirmed: bool = Field(..., description="Public cross-station status.")
    event_path: str = Field(..., description="Path built from date and time folders.")
    public_url: Optional[str] = Field(
        default=None,
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
    ai_score: Optional[float] = Field(
        default=None,
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
    event_timestamp: Optional[float] = Field(default=None, description="Event timestamp when available.")
    coord_long: Optional[float] = Field(default=None, description="Solved longitude when available.")
    coord_lat: Optional[float] = Field(default=None, description="Solved latitude when available.")
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
    trailPoints: List[MeteorTrailPoint] = Field(
        ...,
        description="Frame-aligned trail points normalised from the raw trail series in one observation event.txt file.",
    )


class ExploreGround(MeteorSchema):
    lat: Optional[float] = Field(
        default=None,
        description="Solved event latitude used in the ground map when available.",
    )
    lng: Optional[float] = Field(
        default=None,
        description="Solved event longitude used in the ground map when available.",
    )
    slat: Optional[float] = Field(
        default=None,
        description="Solved start latitude when available from the cross-station event geometry.",
    )
    slng: Optional[float] = Field(
        default=None,
        description="Solved start longitude when available from the cross-station event geometry.",
    )


class ExploreFilters(MeteorSchema):
    from_date: Optional[str] = Field(
        default=None,
        description="Inclusive start date filter in `YYYY-MM-DD` form when one was sent.",
    )
    to_date: Optional[str] = Field(
        default=None,
        description="Inclusive end date filter in `YYYY-MM-DD` form when one was sent.",
    )
    stations: List[str] = Field(
        ...,
        description="Selected station names after CSV parsing. Empty list means no station filter was applied.",
    )
    cross_station_confirmed: Optional[bool] = Field(
        default=None,
        description="Cross-station filter after request parsing. Null means no explicit filter was applied.",
    )
    candidate: bool = Field(
        ...,
        description="True when Utforsk is limited to candidate events only.",
    )


class ExploreKpi(MeteorSchema):
    total_events: int = Field(
        ...,
        description="Number of event cards in the current filtered Utforsk response.",
    )
    cross_station_confirmed: int = Field(
        ...,
        description="Number of filtered events marked as cross-station confirmed.",
    )
    candidates: int = Field(
        ...,
        description="Number of filtered events marked as candidates by the active backend thresholds.",
    )
    stations: List[str] = Field(
        ...,
        description="Sorted list of station names represented in the current filtered event set.",
    )


class ExploreMeteorEvent(MeteorSchema):
    id: int
    event_path: str
    title: str
    times: EventTimes
    location: Optional[str] = Field(default=None, description="Public place name when known.")
    cross_station_confirmed: bool
    candidate: CandidateStatus
    shower: Optional[str] = Field(
        default=None,
        description="Meteor shower when known. Null means no shower is assigned.",
    )
    ai_score: Optional[float] = Field(
        default=None,
        description="Highest available observation-side meteor probability when the backend has one. Null means no usable probability was available in the current event data.",
    )
    technical_validity: TechnicalValidity
    station_summary: StationSummary
    preview: EventPreview
    radiant: RadiantPayload
    ground: ExploreGround = Field(
        ...,
        description="Ground-coordinate basis for Utforsk. In current runtime `lat` and `lng` come from event end-point coordinates, while `slat` and `slng` come from solved start coordinates when the event has them.",
    )
    final_classification: str


class ExploreResponse(MeteorSchema):
    filters: ExploreFilters = Field(
        ...,
        description="Echo of the active Utforsk filters built from the same request that produced the event cards and KPI values.",
    )
    candidate_settings: CandidateSettings = Field(
        ...,
        description="Active backend thresholds used when computing candidate status.",
    )
    kpi: ExploreKpi = Field(
        ...,
        description="Aggregate values built from the same filtered Utforsk data set as the event cards.",
    )
    events: List[ExploreMeteorEvent] = Field(
        ...,
        description="Filtered Utforsk event cards.",
    )


class InsightCoordinateRow(MeteorSchema):
    id: int = Field(..., description="Event database id.")
    datetimetag: str = Field(..., description="Event date and time tag in `YYYYMMDDHHMMSS` form.")
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
