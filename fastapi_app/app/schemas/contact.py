from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ContactForm(BaseModel):
    fornavn: str = Field(
        ...,
        description="Sender first name. The public contact form currently uses Norwegian field names.",
    )
    etternavn: str = Field(
        ...,
        description="Sender last name. The public contact form currently uses Norwegian field names.",
    )
    epost: EmailStr = Field(
        ...,
        description="Sender e-mail address. The public contact form currently uses Norwegian field names.",
    )
    melding: str = Field(
        ...,
        description="Contact message text. The public contact form currently uses Norwegian field names.",
    )


class ContactRequest(BaseModel):
    rcToken: str = Field(..., description="Required reCAPTCHA token.")
    form: ContactForm


class ReportEventForm(BaseModel):
    navn: str = Field(..., description="Reporter name.")
    epost: EmailStr = Field(..., description="Reporter e-mail address.")
    telefon: Optional[str] = Field(default=None, description="Reporter phone number.")
    observation_time: Optional[datetime] = Field(
        default=None,
        alias="observationTime",
        description="Observation time when known.",
    )
    latitude: Optional[float] = Field(
        default=None,
        description="Reporter latitude when the form includes map position.",
    )
    longitude: Optional[float] = Field(
        default=None,
        description="Reporter longitude when the form includes map position.",
    )
    firstdirection: Optional[str] = Field(
        default=None,
        description="Direction at first sighting.",
    )
    firstheight: Optional[str] = Field(
        default=None,
        description="Height angle at first sighting.",
    )
    lastdirection: Optional[str] = Field(
        default=None,
        description="Direction at last sighting.",
    )
    lastheight: Optional[str] = Field(
        default=None,
        description="Height angle at last sighting.",
    )
    direction_text: Optional[str] = Field(
        default=None,
        alias="directionText",
        description="Free-text direction fallback when the reporter cannot place the event on a map.",
    )
    farge: Optional[str] = Field(default=None, alias="farge")
    lysstyrke: Optional[str] = Field(default=None, description="Brightness description.")
    varighet: Optional[str] = Field(default=None, description="Duration description.")
    melding: Optional[str] = Field(default=None, description="Free-text observation note.")

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ReportEventRequest(BaseModel):
    rcToken: str = Field(..., description="Required reCAPTCHA token.")
    form: ReportEventForm

