from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.event import (
    EventClassificationUpdate,
    ExploreResponse,
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
    summary="Get coordinate report",
    description="Convenience route for the solved-event coordinate report. The current runtime returns event end-point coordinates, while richer solved-event summary and geometry fields are being tracked separately.",
)
def report_coordinates(session: Session = Depends(get_session)):
    return event_service.get_insight(session, "coordinates")


@router.get(
    "/insights/{report_name}",
    summary="Get aggregate report",
    description="Returns one named aggregate report. Current supported values are `cam`, `station`, `total`, and `coordinates`. The `coordinates` variant is a solved-event coordinate report rather than a generic free-form map feed.",
)
def insight(
    report_name: str = Path(
        ...,
        description="Report selector. Supported values today are `cam`, `station`, `total`, and `coordinates`.",
    ),
    session: Session = Depends(get_session),
):
    return event_service.get_insight(session, report_name)


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
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    stations: Optional[str] = Query(None),
    cross_station_confirmed: Optional[str] = Query(None),
    candidate: bool = Query(False),
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
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    stations: Optional[str] = Query(None),
    cross_station_confirmed: Optional[str] = Query(None),
    candidate: bool = Query(False),
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
    response_model=MeteorEventListResponse,
    summary="List events for admin board",
    description="Admin-authenticated event-board list. This currently reuses the same event list payload as `/api/events`, but is intended for the protected moderation or admin board rather than the public list.",
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
