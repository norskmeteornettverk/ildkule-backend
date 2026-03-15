from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class EventFilterParams(BaseModel):
    stationName: Optional[str] = None
    year: Optional[str] = None
    eventType: Optional[str] = None
    searchTerm: Optional[str] = None
    page: int = 1
    limit: int = 20
    orderby: str = "date"
    order: str = "desc"


class EventReviewRequest(BaseModel):
    eventID: Optional[int] = Field(default=None, alias="eventID")
    userID: Optional[int] = Field(default=None, alias="userID")
    confirmed: str


class EventClassificationUpdate(BaseModel):
    id: int
    user_confirmed: Optional[str] = None


class EventListResponse(BaseModel):
    totalItems: int
    events: List[dict]
    totalPages: int
    currentPage: int
