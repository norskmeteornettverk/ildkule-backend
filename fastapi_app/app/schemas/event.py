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


class EventReviewRequest(BaseModel):
    eventID: Optional[int] = Field(
        default=None,
        alias="eventID",
        description="Optional event id in the payload. Must match the URL if sent.",
    )
    userID: Optional[int] = Field(
        default=None,
        alias="userID",
        description="Optional user id in the payload. Must match the authenticated user if sent.",
    )
    confirmed: str = Field(
        ...,
        description="Review value. Accepted values today are Positive, Negative, 1, 0.",
    )


class EventClassificationUpdate(BaseModel):
    id: int = Field(..., description="Event id.")
    user_confirmed: Optional[str] = Field(
        default=None,
        description="Admin classification input. Accepted values today are Positive, Negative, 1, 0.",
    )


class EventTimes(MeteorSchema):
    utc: Optional[str] = Field(
        default=None,
        description="UTC timestamp used as the main machine-readable event time.",
    )
    local: Optional[str] = Field(
        default=None,
        description="Local public display time in the configured public timezone.",
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
        description="Language variant when available. Null means no explicit language variant is known.",
    )
    url: str = Field(..., description="Resolved public URL for opening or downloading the artifact.")
    interactive: bool = Field(..., description="True when the artifact should be treated as interactive content.")
    primary_action: str = Field(..., description="Primary UI action, for example open or download.")
    downloadable: bool = Field(..., description="Whether the artifact is intended to be downloadable.")
    visibility: str = Field(..., description="Visibility hint for the frontend.")
    observation_ref: Optional[str] = Field(
        default=None,
        description="Observation key when the artifact belongs to a specific observation.",
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
        description="Short text summary intended for cards and compact views.",
    )


class TechnicalValidity(MeteorSchema):
    is_valid: bool = Field(..., description="High-level public validity flag.")
    is_deleted: bool = Field(..., description="Soft-delete state from ingestion lifecycle.")
    source_bad_detection: Optional[bool] = Field(
        default=None,
        description="Null means this technical indicator is not yet sourced in the current backend.",
    )
    proper_triangulation: Optional[bool] = Field(
        default=None,
        description="Null means the backend does not have enough source data to state this reliably.",
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
        description="Location value used when building summary text.",
    )
    station_summary: StationSummary
    shower: Optional[str] = Field(
        default=None,
        description="Meteor shower when known. Null means no shower is assigned.",
    )
    candidate: CandidateStatus


class MeteorEventClassification(MeteorSchema):
    final_classification: str = Field(
        ...,
        description="Public final classification. Current values are Meteor, Ikke meteor, and Usikker.",
    )
    cross_station_confirmed: bool = Field(..., description="Public cross-station status.")


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
        description="Reserved for explicit path geometry. Null means this backend does not yet expose sampled path points.",
    )
    station_points: List[Dict[str, Any]] = Field(
        ...,
        description="Observation/station context used when rendering path views.",
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
    title_basis: Dict[str, Any] = Field(
        ...,
        description="Raw basis used to build the public title.",
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
        description="Null means this backend does not yet expose a public AI score source.",
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


class MeteorResEntry(MeteorSchema):
    id: int
    line_no: int = Field(..., description="Line number in the stored .res file.")
    entry_type: str = Field(..., description="Parsed row type.")
    label: Optional[str] = Field(default=None, description="Source label from the .res row.")
    raw_line: str = Field(..., description="Original stored .res line.")


class MeteorResEntriesResponse(MeteorSchema):
    totalItems: int
    limit: int
    offset: int
    resEntries: List[MeteorResEntry] = Field(
        ...,
        description="Stored raw .res rows for one event.",
    )


class MeteorTrailPoint(MeteorSchema):
    frame_index: int = Field(..., description="Frame index within the stored trail sequence.")
    pixel_x: Optional[float] = Field(default=None, description="Pixel x position when available.")
    pixel_y: Optional[float] = Field(default=None, description="Pixel y position when available.")
    event_timestamp: Optional[float] = Field(default=None, description="Event timestamp when available.")
    coord_long: Optional[float] = Field(default=None, description="Solved longitude when available.")
    coord_lat: Optional[float] = Field(default=None, description="Solved latitude when available.")


class MeteorObservationTrailResponse(MeteorSchema):
    totalItems: int
    limit: int
    offset: int
    trailPoints: List[MeteorTrailPoint] = Field(
        ...,
        description="Frame-aligned trail points for one observation.",
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
        description="Null means this backend does not yet expose a public AI score source.",
    )
    technical_validity: TechnicalValidity
    station_summary: StationSummary
    preview: EventPreview
    radiant: RadiantPayload
    ground: Dict[str, Optional[float]] = Field(
        ...,
        description="Ground and station coordinate basis for Utforsk. Fields such as slat/slng may be null when that source is not yet connected.",
    )
    final_classification: str


class ExploreResponse(MeteorSchema):
    filters: Dict[str, Any] = Field(
        ...,
        description="Echo of the active Utforsk filters.",
    )
    candidate_settings: CandidateSettings = Field(
        ...,
        description="Active backend thresholds used when computing candidate status.",
    )
    kpi: Dict[str, Any] = Field(
        ...,
        description="Aggregate values built from the same filtered data set as the event list.",
    )
    events: List[ExploreMeteorEvent] = Field(
        ...,
        description="Filtered Utforsk event cards.",
    )
