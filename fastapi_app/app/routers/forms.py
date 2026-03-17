import json

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..schemas.contact import ContactRequest, ReportEventRequest
from ..services.contact_service import ContactService

router = APIRouter(tags=["forms"])
service = ContactService()


@router.post(
    "/contact",
    summary="Send public contact form",
    description="Receives the public contact form and forwards it by e-mail after reCAPTCHA validation.",
    response_description="Contact form accepted.",
)
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


async def _parse_report_payload(request: Request) -> tuple[ReportEventRequest, list[dict]]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        payload = ReportEventRequest.parse_obj(await request.json())
        return payload, []

    form = await request.form()
    rc_token = form.get("rcToken")
    if not rc_token:
        raise HTTPException(status_code=422, detail="rcToken is required")

    payload_json = form.get("payload")
    if payload_json:
        payload_dict = json.loads(str(payload_json))
        payload_dict.setdefault("rcToken", str(rc_token))
        payload = ReportEventRequest.parse_obj(payload_dict)
    else:
        field_map = {
            "navn": form.get("navn"),
            "epost": form.get("epost"),
            "telefon": form.get("telefon"),
            "observationTime": form.get("observationTime") or form.get("observation_time"),
            "latitude": form.get("latitude"),
            "longitude": form.get("longitude"),
            "firstdirection": form.get("firstdirection"),
            "firstheight": form.get("firstheight"),
            "lastdirection": form.get("lastdirection"),
            "lastheight": form.get("lastheight"),
            "directionText": form.get("directionText") or form.get("direction_text"),
            "farge": form.get("farge"),
            "lysstyrke": form.get("lysstyrke"),
            "varighet": form.get("varighet"),
            "melding": form.get("melding"),
        }
        payload = ReportEventRequest.parse_obj({"rcToken": rc_token, "form": field_map})

    attachments: list[dict] = []
    for field_name in ("attachments", "files", "attachment"):
        for candidate in form.getlist(field_name):
            if hasattr(candidate, "filename") and hasattr(candidate, "read"):
                raw = await candidate.read()
                maintype, _, subtype = (candidate.content_type or "application/octet-stream").partition("/")
                attachments.append(
                    {
                        "filename": candidate.filename,
                        "content_type": candidate.content_type,
                        "maintype": maintype or "application",
                        "subtype": subtype or "octet-stream",
                        "content": raw,
                    }
                )
    return payload, attachments


@router.post(
    "/reportmeteor",
    summary="Send public observation report",
    description=(
        "Receives a public meteor observation report. "
        "Supports JSON and multipart form submissions. "
        "Multipart can include one or more attachments."
    ),
    response_description="Observation report accepted.",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ReportEventRequest"}
                },
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["rcToken"],
                        "properties": {
                            "rcToken": {
                                "type": "string",
                                "description": "Required reCAPTCHA token.",
                            },
                            "payload": {
                                "type": "string",
                                "description": "Optional JSON string version of `ReportEventRequest` for multipart submissions.",
                            },
                            "attachments": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Preferred multipart attachment field for one or more uploaded files.",
                            },
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "description": "Legacy multipart attachment field still accepted for compatibility.",
                            },
                            "attachment": {
                                "type": "string",
                                "format": "binary",
                                "description": "Legacy single-file attachment field still accepted for compatibility.",
                            },
                        },
                    }
                },
            },
        }
    },
)
async def report_meteor(request: Request):
    try:
        payload, attachments = await _parse_report_payload(request)
        service.handle_report(payload, attachments=attachments)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
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
