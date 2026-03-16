from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
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
    eventType: Optional[str] = Query(None),
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
    "/event/{event_id}",
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
    "/event/{event_id}/res",
    response_model=MeteorResEntriesResponse,
    summary="Get stored .res rows for one event",
    description="Returns paginated raw .res rows that belong to one event.",
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
    "/observation/{observation_id}/trail",
    response_model=MeteorObservationTrailResponse,
    summary="Get stored trail points for one observation",
    description="Returns paginated frame-aligned trail points extracted from source observation files.",
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


@router.post("/event/{event_id}/review")
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


@router.put("/event/{event_id}")
def update_event_classification(
    event_id: int,
    payload: EventClassificationUpdate,
    session: Session = Depends(get_session),
    __: User = Depends(get_current_user),
):
    event_service.update_user_confirmation(
        session, event_id, payload.user_confirmed
    )
    return {"msg": "Success!"}


@router.put("/event/{event_id}/classification")
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
    "/insight/{report_name}",
    summary="Get aggregate report",
    description="Returns a named aggregate report such as cam, station, total, or coordinates.",
)
def insight(report_name: str, session: Session = Depends(get_session)):
    return event_service.get_insight(session, report_name)


@router.get(
    "/report/coordinates",
    summary="Get coordinate report",
    description="Convenience endpoint for the public coordinate report.",
)
def report_coordinates(session: Session = Depends(get_session)):
    return event_service.get_insight(session, "coordinates")


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
    "/explore/export.csv",
    response_class=PlainTextResponse,
    summary="Export Utforsk CSV",
    description="Exports the same filtered Utforsk data set as CSV.",
    response_description="CSV export built from the filtered Utforsk data set.",
)
def explore_export_csv(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    stations: Optional[str] = Query(None),
    cross_station_confirmed: Optional[str] = Query(None),
    candidate: bool = Query(False),
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.explore_csv(
        session,
        from_date=from_date,
        to_date=to_date,
        stations=_parse_csv(stations),
        cross_station_confirmed=_parse_optional_bool(cross_station_confirmed),
        candidate_only=candidate,
        include_deleted=includeDeleted,
    )


@router.get("/eventboard")
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
    "/event/{date_tag}/{time_tag}",
    response_model=MeteorEvent,
    summary="Get meteor event detail by date/time tag",
    description="Same meteor-event detail contract as /event/{event_id}, looked up by date and time path.",
    response_description="Meteor-event detail object.",
)
def get_event_by_tag(
    date_tag: str,
    time_tag: str,
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.get_event_by_datetimetag(
        session,
        date_tag,
        time_tag,
        include_deleted=includeDeleted,
    )
