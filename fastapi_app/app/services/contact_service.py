from fastapi import HTTPException, status

from ..config import get_settings
from ..schemas.contact import ContactRequest, ReportEventRequest
from ..utils.emailer import send_mail
from ..utils.recaptcha import verify_recaptcha

settings = get_settings()


class ContactService:
    def handle_contact(self, payload: ContactRequest) -> None:
        if not verify_recaptcha(payload.rcToken):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="reCAPTCHA validation failed",
            )

        recipient = settings.contact_recipient or settings.smtp_sender
        if not recipient:
            raise HTTPException(
                status_code=500,
                detail="Contact recipient not configured",
            )

        form = payload.form
        body = f"""
        Hei!<br>{form.fornavn} har sendt inn et kontaktskjema via ildkule.net.<br><br>
        <table style="border:1px solid #000;border-collapse:collapse;text-align:left;">
            <tr style="background-color:#D6EEEE;">
                <th>Felt</th>
                <th>Verdi</th>
            </tr>
            <tr><td>Fornavn</td><td>{form.fornavn}</td></tr>
            <tr style="background-color:#D6EEEE;"><td>Etternavn</td><td>{form.etternavn}</td></tr>
            <tr><td>E-post</td><td>{form.epost}</td></tr>
            <tr style="background-color:#D6EEEE;"><td>Melding</td><td>{form.melding}</td></tr>
        </table><br><br>
        Denne e-posten er automatisk sendt fra ildkule.net.
        """
        send_mail(
            recipient,
            "Ny kontaktmelding fra ildkule.net",
            body,
            body,
        )

    def handle_report(self, payload: ReportEventRequest) -> None:
        if not verify_recaptcha(payload.rcToken):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="reCAPTCHA validation failed",
            )

        recipient = (
            settings.meteor_report_recipient or settings.contact_recipient or settings.smtp_sender
        )
        if not recipient:
            raise HTTPException(status_code=500, detail="Recipient missing")

        form = payload.form
        body = f"""
        Hei!<br>{form.navn} har meldt inn en ny observasjon via ildkule.net.<br><br>
        <table style="border:1px solid #000;border-collapse:collapse;text-align:left;">
            <tr style="background-color:#D6EEEE;">
                <th>Felt</th>
                <th>Innrapportert data</th>
            </tr>
            <tr>
                <td>Kontaktinformasjon</td>
                <td>{form.navn}<br>{form.epost}<br>Tlf: {form.telefon or 'ukjent'}</td>
            </tr>
            <tr style="background-color:#D6EEEE;">
                <td>Observasjonssted</td>
                <td>Lat: {form.latitude or '-'}<br>Long: {form.longitude or '-'}</td>
            </tr>
            <tr>
                <td>Først sett</td>
                <td>Himmelretning: {form.firstdirection or '-'}<br>Høyde: {form.firstheight or '-'}</td>
            </tr>
            <tr style="background-color:#D6EEEE;">
                <td>Sist sett</td>
                <td>Himmelretning: {form.lastdirection or '-'}<br>Høyde: {form.lastheight or '-'}</td>
            </tr>
            <tr><td>Farge</td><td>{form.farge or '-'}</td></tr>
            <tr style="background-color:#D6EEEE;"><td>Lysstyrke</td><td>{form.lysstyrke or '-'}</td></tr>
            <tr><td>Varighet</td><td>{form.varighet or '-'}</td></tr>
            <tr style="background-color:#D6EEEE;"><td>Kommentarer</td><td>{form.melding or '-'}</td></tr>
        </table><br><br>
        Denne e-posten er automatisk sendt fra ildkule.net.
        """
        send_mail(
            recipient,
            "Ny observasjon fra ildkule.net",
            body,
            body,
        )

