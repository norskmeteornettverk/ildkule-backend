from __future__ import annotations

import pytest
import requests
from fastapi import HTTPException

from fastapi_app.app.routers import forms as forms_router
from fastapi_app.app.services import contact_service as contact_service_module
from fastapi_app.app.services.contact_service import ContactService
from fastapi_app.app.utils import emailer, recaptcha


def test_contact_route_success(client, monkeypatch):
    recorded = {}
    monkeypatch.setattr(
        forms_router.service,
        "handle_contact",
        lambda payload: recorded.update({"email": payload.form.epost}),
    )

    response = client.post(
        "/api/forms/contact",
        json={
            "rcToken": "ok",
            "form": {
                "fornavn": "Ada",
                "etternavn": "Lovelace",
                "epost": "ada@example.com",
                "melding": "Hei",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Kontaktskjema mottatt og sendt"
    assert recorded["email"] == "ada@example.com"


def test_report_meteor_requires_rc_token_in_multipart(client):
    response = client.post(
        "/api/forms/meteor-report",
        files={"attachments": ("meteor.jpg", b"data", "image/jpeg")},
        data={"navn": "Ada", "epost": "ada@example.com"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "rcToken is required"


def test_report_meteor_rejects_invalid_json_shape(client):
    response = client.post(
        "/api/forms/meteor-report",
        json={"rcToken": "ok", "form": {"epost": "ada@example.com"}},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["loc"][-1] == "navn"


def test_report_meteor_accepts_multipart_without_payload_wrapper(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(forms_router.service, "handle_report", lambda payload, attachments=None: captured.update({"payload": payload, "attachments": attachments}))

    response = client.post(
        "/api/forms/meteor-report",
        data={
            "rcToken": "ok",
            "navn": "Ada",
            "epost": "ada@example.com",
            "observationTime": "2024-01-01T01:02:03",
        },
        files={"attachments": ("meteor.jpg", b"data", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Observasjon sendt"
    assert captured["payload"].form.navn == "Ada"
    assert captured["attachments"][0]["filename"] == "meteor.jpg"


def test_report_meteor_accepts_multipart_with_payload_wrapper(client, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        forms_router.service,
        "handle_report",
        lambda payload, attachments=None: captured.update(
            {"payload": payload, "attachments": attachments}
        ),
    )

    response = client.post(
        "/api/forms/meteor-report",
        files=[
            ("rcToken", (None, "ok")),
            ("payload", (None, '{"form": {"navn": "Ada", "epost": "ada@example.com", "melding": "Hei"}}')),
        ],
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Observasjon sendt"
    assert captured["payload"].rcToken == "ok"
    assert captured["payload"].form.navn == "Ada"


def test_contact_service_missing_recipients_raise_http_500(monkeypatch):
    monkeypatch.setattr(contact_service_module, "verify_recaptcha", lambda _token: True)
    monkeypatch.setattr(contact_service_module.settings, "contact_recipient", None)
    monkeypatch.setattr(contact_service_module.settings, "smtp_sender", None)

    service = ContactService()

    with pytest.raises(HTTPException) as exc:
        service.handle_contact(
            forms_router.ContactRequest.parse_obj(
                {
                    "rcToken": "ok",
                    "form": {
                        "fornavn": "Ada",
                        "etternavn": "Lovelace",
                        "epost": "ada@example.com",
                        "melding": "Hei",
                    },
                }
            )
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Contact recipient not configured"


def test_contact_route_reraises_non_recaptcha_http_exception(monkeypatch):
    monkeypatch.setattr(
        forms_router.service,
        "handle_contact",
        lambda payload: (_ for _ in ()).throw(
            HTTPException(status_code=500, detail="smtp down")
        ),
    )

    with pytest.raises(HTTPException) as exc:
        forms_router.contact(
            forms_router.ContactRequest.parse_obj(
                {
                    "rcToken": "ok",
                    "form": {
                        "fornavn": "Ada",
                        "etternavn": "Lovelace",
                        "epost": "ada@example.com",
                        "melding": "Hei",
                    },
                }
            )
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "smtp down"


def test_report_service_missing_recipient_raises_http_500(monkeypatch):
    monkeypatch.setattr(contact_service_module, "verify_recaptcha", lambda _token: True)
    monkeypatch.setattr(contact_service_module.settings, "meteor_report_recipient", None)
    monkeypatch.setattr(contact_service_module.settings, "contact_recipient", None)
    monkeypatch.setattr(contact_service_module.settings, "smtp_sender", None)

    service = ContactService()

    with pytest.raises(HTTPException) as exc:
        service.handle_report(
            forms_router.ReportEventRequest.parse_obj(
                {
                    "rcToken": "ok",
                    "form": {"navn": "Ada", "epost": "ada@example.com"},
                }
            )
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "Recipient missing"


def test_verify_recaptcha_branches(monkeypatch):
    monkeypatch.setattr(recaptcha.settings, "recaptcha_secret", None)
    assert recaptcha.verify_recaptcha("ignored") is True

    monkeypatch.setattr(recaptcha.settings, "recaptcha_secret", "secret")

    def raising_post(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr(recaptcha.requests, "post", raising_post)
    assert recaptcha.verify_recaptcha("token") is False

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"success": False}

    monkeypatch.setattr(recaptcha.requests, "post", lambda *args, **kwargs: FakeResponse())
    assert recaptcha.verify_recaptcha("token") is False


def test_send_mail_handles_missing_settings_success_and_failure(monkeypatch):
    monkeypatch.setattr(emailer.settings, "smtp_host", None)
    monkeypatch.setattr(emailer.settings, "smtp_username", None)
    monkeypatch.setattr(emailer.settings, "smtp_password", None)
    monkeypatch.setattr(emailer.settings, "smtp_sender", None)
    emailer.send_mail("ada@example.com", "Subject", "<b>body</b>")

    monkeypatch.setattr(emailer.settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(emailer.settings, "smtp_port", 465)
    monkeypatch.setattr(emailer.settings, "smtp_username", "user")
    monkeypatch.setattr(emailer.settings, "smtp_password", "pw")
    monkeypatch.setattr(emailer.settings, "smtp_sender", "noreply@example.com")

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port):
            sent["host"] = host
            sent["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["subject"] = message["Subject"]
            sent["to"] = message["To"]

    monkeypatch.setattr(emailer.smtplib, "SMTP_SSL", FakeSMTP)
    emailer.send_mail(
        "ada@example.com",
        "Subject",
        "<b>body</b>",
        "body",
        attachments=[
            {
                "filename": "meteor.jpg",
                "content_type": "image/jpeg",
                "maintype": "image",
                "subtype": "jpeg",
                "content": b"image-bytes",
            },
            {"filename": "skip.bin"},
        ],
    )
    assert sent["host"] == "smtp.example.com"
    assert sent["subject"] == "Subject"
    assert sent["to"] == "ada@example.com"

    class BrokenSMTP(FakeSMTP):
        def send_message(self, message):
            raise RuntimeError("smtp failure")

    monkeypatch.setattr(emailer.smtplib, "SMTP_SSL", BrokenSMTP)
    with pytest.raises(RuntimeError):
        emailer.send_mail("ada@example.com", "Subject", "<b>body</b>")
