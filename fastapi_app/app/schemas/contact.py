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


class ReportMeteorForm(BaseModel):
    navn: str
    epost: EmailStr
    telefon: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    firstdirection: Optional[str] = None
    firstheight: Optional[str] = None
    lastdirection: Optional[str] = None
    lastheight: Optional[str] = None
    farge: Optional[str] = Field(default=None, alias="farge")
    lysstyrke: Optional[str] = None
    varighet: Optional[str] = None
    melding: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class ReportMeteorRequest(BaseModel):
    rcToken: str
    form: ReportMeteorForm

