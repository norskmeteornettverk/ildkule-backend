from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.event import (
    AdminMeteorEventListResponse,
    InsightCamRow,
    EventClassificationUpdate,
    EventFilterOptionsResponse,
    ExploreResponse,
    InsightFilterRequest,
    InsightCoordinateRow,
    InsightReportName,
    InsightStationRow,
    InsightTotalRow,
    EventReviewRequest,
    MeteorEvent,
    MeteorEventListResponse,
    MeteorObservationTrailResponse,
    MeteorResEntriesResponse,
)
from ..security import enforce_role, get_current_user
from ..services.event_service import EventService

router = APIRouter(tags=["events"])
event_service = EventService()


def _parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_optional_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes"}:
        return True
    if lowered in {"0", "false", "no"}:
        return False
    raise HTTPException(status_code=400, detail=f"Invalid boolean value: {value}")


def _legacy_probability(score: Optional[float]) -> Optional[float]:
    if score is None:
        return None
    return score / 100 if score > 1 else score


def _legacy_coordinate_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    legacy_rows: List[Dict[str, Any]] = []
    for row in rows:
        legacy_rows.append(
            {
                **row,
                "StationCam": row.get("station_cam"),
                "NumberOfStations": row.get("number_of_stations"),
                "ProperTriangulation": (
                    "1" if row.get("proper_triangulation") else "0"
                ),
                "SourceBadDetection": "0",
                "MeteorScoreHighest": _legacy_probability(row.get("ai_score")),
            }
        )
    return legacy_rows


@router.get(
    "/events",
    response_model=MeteorEventListResponse,
    summary="List meteor events",
    description=(
        "Returns the meteor-event list contract. "
        "Each event object is intended to be rich enough for public list rendering "
        "without a follow-up detail request."
    ),
    response_description="Paginated meteor-event list.",
)
def get_events(
    searchTerm: Optional[str] = Query(None),
    stationName: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    eventType: Optional[str] = Query(
        None,
        description="Comma-separated event-type filter. Current public values are Meteorittkandidat, Krysspeilet, and Upeilet.",
    ),
    includeDeleted: bool = Query(False),
    page: int = Query(1),
    limit: int = Query(20),
    orderby: str = Query("date"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
):
    if searchTerm:
        return event_service.search(session, searchTerm, include_deleted=includeDeleted)
    if stationName or year or eventType:
        years = [int(y) for y in _parse_csv(year) or []]
        classes = _parse_csv(eventType)
        stations = _parse_csv(stationName)
        return event_service.filter(
            session,
            stations,
            years,
            classes,
            include_deleted=includeDeleted,
        )
    return event_service.list_events(
        session,
        page,
        limit,
        orderby,
        order,
        include_deleted=includeDeleted,
    )


@router.get(
    "/events/filters",
    response_model=EventFilterOptionsResponse,
    summary="Get event filter options",
    description="Returns available years, stations, and meteor event types for list filtering.",
    response_description="Available event-filter values.",
)
def get_event_filter_options(
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
    ):
    return event_service.get_filter_options(session, include_deleted=includeDeleted)


@router.get(
    "/events/{event_id}",
    response_model=MeteorEvent,
    summary="Get meteor event detail",
    description=(
        "Returns the rich meteor-event detail contract, including header, summary basis, "
        "classification, analysis, artifacts, and observation packages."
    ),
    response_description="Meteor-event detail object.",
)
def get_event(
    event_id: int,
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.get_event(
        session,
        event_id,
        include_deleted=includeDeleted,
    )


@router.get(
    "/events/{event_id}/res",
    response_model=MeteorResEntriesResponse,
    summary="Get stored .res rows for one event",
    description=(
        "Returns paginated stored .res rows for one event. "
        "In the current backend these rows act as solved trajectory or geometry rows for a cross-station event. "
        "The parser reads each row as long1/lat1/long2/lat2/height/label, and the event-level start/end coordinates are taken from the first coordinate pair on row 1 and row 2. "
        "Start and End are the clearest row labels today, while the exact semantics of the second coordinate pair are still being clarified."
    ),
    response_description="Paginated stored .res rows.",
)
def get_event_res_entries(
    event_id: int,
    includeDeleted: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return event_service.get_event_res_entries(
        session,
        event_id,
        limit,
        offset,
        include_deleted=includeDeleted,
    )


@router.get(
    "/observations/{observation_id}/trail",
    response_model=MeteorObservationTrailResponse,
    summary="Get stored trail points for one observation",
    description="Returns paginated frame-aligned trail points normalised from the raw trail arrays in one observation event.txt file.",
    response_description="Paginated observation trail points.",
)
def get_observation_trail_points(
    observation_id: int,
    includeDeleted: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return event_service.get_observation_trail_points(
        session,
        observation_id,
        limit,
        offset,
        include_deleted=includeDeleted,
    )


@router.post(
    "/events/{event_id}/review",
    summary="Review event",
    description="Stores one authenticated review for an event. Optional payload fields `eventID` and `userID` must match the URL id and authenticated token user when they are sent.",
)
def review_event(
    event_id: int,
    payload: EventReviewRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if payload.eventID is not None and payload.eventID != event_id:
        raise HTTPException(status_code=400, detail="eventID does not match URL id")
    if payload.userID is not None and payload.userID != current_user.id:
        raise HTTPException(status_code=400, detail="userID does not match token user")

    classification = payload.confirmed
    rating = -1
    if classification in {"Positive", "1"}:
        rating = 1
    elif classification in {"Negative", "0"}:
        rating = 0
    event_service.review_event(session, event_id, current_user.id, rating)
    if rating == 1:
        message = "Takk for din anbefaling (Ja)"
    elif rating == 0:
        message = "Takk for din anbefaling (Nei)"
    else:
        message = "Anbefalingen er nullstilt"
    return {"msg": message}


@router.put(
    "/events/{event_id}/classification",
    summary="Update event classification",
    description="Admin-only event classification update. Current compatibility input values Positive and 1 map to confirmed meteor, while Negative and 0 map to not meteor.",
)
def admin_event_classification(
    event_id: int,
    payload: EventClassificationUpdate,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    event_service.update_user_confirmation(
        session, event_id, payload.user_confirmed
    )
    return {"msg": "Success!"}


@router.get(
    "/insights/coordinates",
    response_model=List[InsightCoordinateRow],
    summary="Get coordinate report",
    description="Convenience route for the solved-event coordinate report. The current runtime returns end coordinates, start coordinates, radiant values, speed, end height, triangulation flags, station count, and the highest available observation-side probability when the source data has it. The same date, station, candidate, and cross-station filters used by Utforsk can also be applied here.",
)
def report_coordinates(
    from_date: Optional[str] = Query(
        None,
        description="Inclusive start date in `YYYY-MM-DD` form.",
    ),
    to_date: Optional[str] = Query(
        None,
        description="Inclusive end date in `YYYY-MM-DD` form.",
    ),
    stations: Optional[str] = Query(
        None,
        description="Comma-separated station names, for example `alta,ski`.",
    ),
    cross_station_confirmed: Optional[str] = Query(
        None,
        description="Optional boolean filter accepted as `true`, `false`, `1`, `0`, `yes`, or `no`.",
    ),
    candidate: bool = Query(
        False,
        description="Set true to keep only candidate events.",
    ),
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.get_coordinate_insight(
        session,
        from_date=from_date,
        to_date=to_date,
        stations=_parse_csv(stations),
        cross_station_confirmed=_parse_optional_bool(cross_station_confirmed),
        candidate_only=candidate,
        include_deleted=includeDeleted,
    )


@router.get(
    "/insights/cam",
    response_model=List[InsightCamRow],
    summary="Get camera insight report",
    description="Returns the camera-level observation summary with the current backend field names preserved as-is.",
    response_description="Camera-level insight rows.",
)
def report_insight_cam(
    session: Session = Depends(get_session),
):
    return event_service.get_insight(session, "cam")


@router.get(
    "/insights/station",
    response_model=List[InsightStationRow],
    summary="Get station insight report",
    description="Returns the station-level observation summary with the current backend field names preserved as-is.",
    response_description="Station-level insight rows.",
)
def report_insight_station(
    session: Session = Depends(get_session),
):
    return event_service.get_insight(session, "station")


@router.get(
    "/insights/total",
    response_model=List[InsightTotalRow],
    summary="Get total insight report",
    description="Returns the total observation summary as the current single-row report.",
    response_description="Total insight row.",
)
def report_insight_total(
    session: Session = Depends(get_session),
):
    return event_service.get_insight(session, "total")


@router.get(
    "/insights/{report_name}",
    response_model=List[Dict[str, Any]],
    summary="Get aggregate report",
    description="Returns one named aggregate report. Current supported values are `cam`, `station`, `total`, and `coordinates`. The `coordinates` variant is a solved-event coordinate report with start and end geometry, radiant values, and basic quality flags rather than a generic free-form map feed.",
    include_in_schema=False,
)
def insight(
    report_name: InsightReportName = Path(
        ...,
        description="Report selector. Supported values today are `cam`, `station`, `total`, and `coordinates`.",
    ),
    session: Session = Depends(get_session),
):
    return event_service.get_insight(session, report_name.value)


@router.get("/insight/{report_name}", include_in_schema=False)
def legacy_insight(
    report_name: InsightReportName,
    session: Session = Depends(get_session),
):
    if report_name == InsightReportName.coordinates:
        return _legacy_coordinate_rows(event_service.get_coordinate_insight(session))
    return event_service.get_insight(session, report_name.value)


@router.get("/report/coordinates", include_in_schema=False)
def legacy_report_coordinates_get(session: Session = Depends(get_session)):
    return _legacy_coordinate_rows(event_service.get_coordinate_insight(session))


@router.post("/insight/coordinates", include_in_schema=False)
def legacy_report_coordinates_post(
    payload: Optional[InsightFilterRequest] = Body(default=None),
    session: Session = Depends(get_session),
):
    filters = payload or InsightFilterRequest()
    rows = event_service.get_coordinate_insight(
        session,
        from_date=filters.from_date,
        to_date=filters.to_date,
        stations=filters.stations or None,
        cross_station_confirmed=filters.cross_station_confirmed,
        candidate_only=filters.candidate,
        include_deleted=filters.includeDeleted,
    )
    return _legacy_coordinate_rows(rows)


@router.get(
    "/explore",
    response_model=ExploreResponse,
    summary="Get Utforsk data",
    description=(
        "Returns the filtered Utforsk contract. "
        "The response combines filter echo, active candidate settings, KPI values, "
        "and event cards from one shared filtered data set."
    ),
    response_description="Utforsk response with filters, KPI values, and event cards.",
)
def explore(
    from_date: Optional[str] = Query(
        None,
        description="Inclusive start date in `YYYY-MM-DD` form.",
    ),
    to_date: Optional[str] = Query(
        None,
        description="Inclusive end date in `YYYY-MM-DD` form.",
    ),
    stations: Optional[str] = Query(
        None,
        description="Comma-separated station names, for example `alta,ski`.",
    ),
    cross_station_confirmed: Optional[str] = Query(
        None,
        description="Optional boolean filter accepted as `true`, `false`, `1`, `0`, `yes`, or `no`.",
    ),
    candidate: bool = Query(
        False,
        description="Set true to keep only candidate events.",
    ),
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.explore(
        session,
        from_date=from_date,
        to_date=to_date,
        stations=_parse_csv(stations),
        cross_station_confirmed=_parse_optional_bool(cross_station_confirmed),
        candidate_only=candidate,
        include_deleted=includeDeleted,
    )


@router.get(
    "/explore/export",
    response_class=PlainTextResponse,
    summary="Export Utforsk CSV",
    description="Exports the same filtered Utforsk data set as CSV. Use `format=csv`. Other format values are rejected with HTTP 400.",
    response_description="CSV export built from the filtered Utforsk data set.",
)
def explore_export_csv(
    from_date: Optional[str] = Query(
        None,
        description="Inclusive start date in `YYYY-MM-DD` form.",
    ),
    to_date: Optional[str] = Query(
        None,
        description="Inclusive end date in `YYYY-MM-DD` form.",
    ),
    stations: Optional[str] = Query(
        None,
        description="Comma-separated station names, for example `alta,ski`.",
    ),
    cross_station_confirmed: Optional[str] = Query(
        None,
        description="Optional boolean filter accepted as `true`, `false`, `1`, `0`, `yes`, or `no`.",
    ),
    candidate: bool = Query(
        False,
        description="Set true to keep only candidate events.",
    ),
    format: str = Query(
        "csv",
        description="Export format. Only `csv` is supported today. Other values return HTTP 400.",
    ),
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    if format.lower() != "csv":
        raise HTTPException(status_code=400, detail="Only csv export is supported")
    return event_service.explore_csv(
        session,
        from_date=from_date,
        to_date=to_date,
        stations=_parse_csv(stations),
        cross_station_confirmed=_parse_optional_bool(cross_station_confirmed),
        candidate_only=candidate,
        include_deleted=includeDeleted,
    )


@router.get(
    "/admin/events",
    response_model=AdminMeteorEventListResponse,
    summary="List events for admin board",
    description="Admin-authenticated event-board list for moderation and queue work. The response keeps the same rich event basis as `/api/events`, but also exposes top-level admin helper fields `datetimetag`, `date`, `camera_confirmed`, `user_confirmed`, `ratings`, `positive_ratings`, and `negative_ratings`. These helper fields belong only to `/api/admin/events`, while `classification` remains the canonical moderation object.",
    response_description="Paginated event-board list.",
)
def event_board(
    includeDeleted: bool = Query(False),
    page: int = Query(1),
    limit: int = Query(50),
    orderby: str = Query("date"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    return event_service.list_events(
        session,
        page=page,
        limit=limit,
        order_by=orderby,
        order=order,
        include_deleted=includeDeleted,
        include_ratings=True,
    )


@router.get(
    "/events/by-path/{date_tag}/{time_tag}",
    response_model=MeteorEvent,
    summary="Get meteor event detail by date/time tag",
    description="Same meteor-event detail contract as `/api/events/{event_id}`, looked up by event path components from `YYYYMMDD/HHMMSS`.",
    response_description="Meteor-event detail object.",
)
def get_event_by_tag(
    date_tag: str = Path(
        ...,
        description="Event date folder in `YYYYMMDD` format.",
    ),
    time_tag: str = Path(
        ...,
        description="Event time folder in `HHMMSS` format.",
    ),
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.get_event_by_datetimetag(
        session,
        date_tag,
        time_tag,
        include_deleted=includeDeleted,
    )
