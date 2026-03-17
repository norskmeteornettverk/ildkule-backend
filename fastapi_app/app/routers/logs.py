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


@router.get(
    "/stationlog",
    summary="List stored station log rows",
    description="Returns stored log rows pushed from stations. This endpoint is currently open in runtime and lists persisted log entries, not the richer station and camera last-seen status dataset tracked separately.",
)
def list_station_logs(session: Session = Depends(get_session)):
    logs = service.list(session)
    return [model_to_dict(log) for log in logs]


@router.post(
    "/stationlog",
    summary="Store a station log row",
    description="Stores one pushed station log entry after bearer-token validation. Requests without a valid `Authorization: Bearer <token>` header are rejected with 401.",
)
def insert_station_log(
    payload: StationLogPayload,
    authorization: str = Header(
        None,
        description="Bearer token for station-log ingestion, formatted as `Bearer <token>`.",
    ),
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
