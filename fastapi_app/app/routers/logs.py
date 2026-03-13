from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_session
from ..schemas.log import StationLogPayload
from ..services.log_service import LogService
from ..utils.serialization import model_to_dict

router = APIRouter(tags=["station log"])
settings = get_settings()
service = LogService()


@router.get("/stationlog")
def list_station_logs(session: Session = Depends(get_session)):
    logs = service.list(session)
    return [model_to_dict(log) for log in logs]


@router.post("/stationlog")
def insert_station_log(
    payload: StationLogPayload,
    authorization: str = Header(None),
    session: Session = Depends(get_session),
):
    if not settings.station_log_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Station log token not configured",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed"
        )
    token = authorization.split(" ", 1)[1]
    if token != settings.station_log_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed"
        )

    record = service.log(
        session,
        payload.station.name,
        payload.station.code,
        payload.station.log_time,
    )
    return {"msg": "Success!", "id": record.id}

