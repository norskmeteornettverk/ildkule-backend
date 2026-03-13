from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..schemas.contact import ContactRequest, ReportMeteorRequest
from ..services.contact_service import ContactService

router = APIRouter(tags=["forms"])
service = ContactService()


@router.post("/contact")
def contact(payload: ContactRequest):
    try:
        service.handle_contact(payload)
    except HTTPException as exc:
        if exc.status_code == 401 and exc.detail == "reCAPTCHA validation failed":
            message = (
                "Kontaktskjema mottatt, men foresporsel ble ikke autentisert som en "
                "vanlig bruker med reCAPTCHA"
            )
            return JSONResponse(
                status_code=401,
                content={"error": message, "message": message},
            )
        raise
    return {"message": "Kontaktskjema mottatt og sendt"}


@router.post("/reportmeteor")
def report_meteor(payload: ReportMeteorRequest):
    try:
        service.handle_report(payload)
    except HTTPException as exc:
        if exc.status_code == 401 and exc.detail == "reCAPTCHA validation failed":
            message = (
                "Kontaktskjema mottatt, men foresporsel ble ikke autentisert som en "
                "vanlig bruker med reCAPTCHA"
            )
            return JSONResponse(
                status_code=401,
                content={"error": message, "message": message},
            )
        raise
    return {"message": "Observasjon sendt"}
