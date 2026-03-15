from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.event import (
    EventClassificationUpdate,
    EventReviewRequest,
)
from ..security import enforce_role, get_current_user
from ..services.event_service import EventService

router = APIRouter(tags=["events"])
event_service = EventService()


def _parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("/events")
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


@router.get("/event/{event_id}")
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


@router.get("/event/{event_id}/res")
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


@router.get("/observation/{observation_id}/trail")
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


@router.get("/insight/{report_name}")
def insight(report_name: str, session: Session = Depends(get_session)):
    return event_service.get_insight(session, report_name)


@router.get("/report/coordinates")
def report_coordinates(session: Session = Depends(get_session)):
    return event_service.get_insight(session, "coordinates")


@router.get("/events/filters")
def get_event_filter_options(
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return event_service.get_filter_options(session, include_deleted=includeDeleted)


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


@router.get("/event/{date_tag}/{time_tag}")
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
