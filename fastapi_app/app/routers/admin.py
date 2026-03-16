from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_session
from ..schemas.file_loader import FileLoadRequest
from ..services.event_service import EventService

router = APIRouter(tags=["admin"])
security = HTTPBasic()
settings = get_settings()
service = EventService()


@router.post(
    "/eventload",
    summary="Load events from files",
    description="Administrative ingestion endpoint that reads event folders from DATA_DIRECTORY and upserts events and observations.",
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
