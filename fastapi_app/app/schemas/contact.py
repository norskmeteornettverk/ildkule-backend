from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ContactForm(BaseModel):
    fornavn: str
    etternavn: str
    epost: EmailStr
    melding: str


class ContactRequest(BaseModel):
    rcToken: str
    form: ContactForm


class ReportEventForm(BaseModel):
    navn: str
    epost: EmailStr
    telefon: Optional[str] = None
    observation_time: Optional[datetime] = Field(default=None, alias="observationTime")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    firstdirection: Optional[str] = None
    firstheight: Optional[str] = None
    lastdirection: Optional[str] = None
    lastheight: Optional[str] = None
    direction_text: Optional[str] = Field(default=None, alias="directionText")
    farge: Optional[str] = Field(default=None, alias="farge")
    lysstyrke: Optional[str] = None
    varighet: Optional[str] = None
    melding: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        allow_population_by_alias = True


class ReportEventRequest(BaseModel):
    rcToken: str
    form: ReportEventForm

