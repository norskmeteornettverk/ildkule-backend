from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_session
from ..schemas.common import MessageResponse
from ..schemas.file_loader import FileLoadRequest
from ..services.event_service import EventService

router = APIRouter(tags=["admin"])
security = HTTPBasic()
settings = get_settings()
service = EventService()


@router.post(
    "/event-imports",
    response_model=MessageResponse,
    summary="Import events from files",
    description=(
        "Administrative ingestion endpoint that reads `YYYYMMDD/HHMMSS` event folders from `DATA_DIRECTORY` for the requested date window. "
        "Events are upserted by `datetimetag`, observations are upserted by stable `observation_key`, stored `.res` rows are replaced per event reload, "
        "and stored trail points are replaced per observation reload. Items inside the imported date window that are not seen in the current run are soft-deleted "
        "with `deletion_reason = missing_from_import`. Renamed event folders therefore become new events, while moved observations can be reattached when the same "
        "`observation_key` is still produced."
    ),
)
def event_load(
    payload: FileLoadRequest,
    credentials: HTTPBasicCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    if (
        credentials.username != settings.eventload_username
        or credentials.password != settings.eventload_password
    ):
        raise HTTPException(status_code=401, detail="Feil brukernavn eller passord")
    if not settings.data_directory:
        raise HTTPException(
            status_code=500,
            detail="DATA_DIRECTORY is not configured",
        )
    processed = service.load_from_files(
        session, settings.data_directory, payload.date_from, payload.date_to
    )
    return {"message": f"Innlasting av data fullført ({processed} hendelse(r))"}
