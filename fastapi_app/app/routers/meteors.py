from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.meteor import (
    MeteorClassificationUpdate,
    MeteorReviewRequest,
)
from ..security import enforce_role, get_current_user
from ..services.meteor_service import MeteorService

router = APIRouter(tags=["meteors"])
meteor_service = MeteorService()


def _parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("/meteors")
def get_meteors(
    searchTerm: Optional[str] = Query(None),
    stationName: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    meteorClass: Optional[str] = Query(None),
    includeDeleted: bool = Query(False),
    page: int = Query(1),
    limit: int = Query(20),
    orderby: str = Query("date"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
):
    if searchTerm:
        return meteor_service.search(session, searchTerm, include_deleted=includeDeleted)
    if stationName or year or meteorClass:
        years = [int(y) for y in _parse_csv(year) or []]
        classes = _parse_csv(meteorClass)
        stations = _parse_csv(stationName)
        return meteor_service.filter(
            session,
            stations,
            years,
            classes,
            include_deleted=includeDeleted,
        )
    return meteor_service.list_meteors(
        session,
        page,
        limit,
        orderby,
        order,
        include_deleted=includeDeleted,
    )


@router.get("/meteor/{meteor_id}")
def get_meteor(
    meteor_id: int,
    includeDeleted: bool = Query(False),
    session: Session = Depends(get_session),
):
    return meteor_service.get_meteor(
        session,
        meteor_id,
        include_deleted=includeDeleted,
    )


@router.get("/meteor/{meteor_id}/res")
def get_meteor_res_entries(
    meteor_id: int,
    includeDeleted: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return meteor_service.get_meteor_res_entries(
        session,
        meteor_id,
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
    return meteor_service.get_observation_trail_points(
        session,
        observation_id,
        limit,
        offset,
        include_deleted=includeDeleted,
    )


@router.post("/meteor/{meteor_id}/review")
def review_meteor(
    meteor_id: int,
    payload: MeteorReviewRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if payload.meteorID is not None and payload.meteorID != meteor_id:
        raise HTTPException(status_code=400, detail="meteorID does not match URL id")
    if payload.userID is not None and payload.userID != current_user.id:
        raise HTTPException(status_code=400, detail="userID does not match token user")

    classification = payload.confirmed
    rating = -1
    if classification in {"Positive", "1"}:
        rating = 1
    elif classification in {"Negative", "0"}:
        rating = 0
    meteor_service.review_meteor(session, meteor_id, current_user.id, rating)
    if rating == 1:
        message = "Takk for din anbefaling (Ja)"
    elif rating == 0:
        message = "Takk for din anbefaling (Nei)"
    else:
        message = "Anbefalingen er nullstilt"
    return {"msg": message}


@router.put("/meteor/{meteor_id}")
def update_meteor_classification(
    meteor_id: int,
    payload: MeteorClassificationUpdate,
    session: Session = Depends(get_session),
    __: User = Depends(get_current_user),
):
    meteor_service.update_user_confirmation(
        session, meteor_id, payload.user_confirmed
    )
    return {"msg": "Success!"}


@router.put("/meteor/{meteor_id}/classification")
def admin_classification(
    meteor_id: int,
    payload: MeteorClassificationUpdate,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    meteor_service.update_user_confirmation(
        session, meteor_id, payload.user_confirmed
    )
    return {"msg": "Success!"}


@router.get("/insight/{report_name}")
def insight(report_name: str, session: Session = Depends(get_session)):
    return meteor_service.get_insight(session, report_name)


@router.get("/meteorboard")
def meteor_board(
    includeDeleted: bool = Query(False),
    page: int = Query(1),
    limit: int = Query(50),
    orderby: str = Query("date"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    return meteor_service.list_meteors(
        session,
        page=page,
        limit=limit,
        order_by=orderby,
        order=order,
        include_deleted=includeDeleted,
    )
