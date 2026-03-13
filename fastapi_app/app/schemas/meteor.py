from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class MeteorFilterParams(BaseModel):
    stationName: Optional[str] = None
    year: Optional[str] = None
    meteorClass: Optional[str] = None
    searchTerm: Optional[str] = None
    page: int = 1
    limit: int = 20
    orderby: str = "date"
    order: str = "desc"


class MeteorReviewRequest(BaseModel):
    meteorID: Optional[int] = Field(default=None, alias="meteorID")
    userID: Optional[int] = Field(default=None, alias="userID")
    confirmed: str


class MeteorClassificationUpdate(BaseModel):
    id: int
    user_confirmed: Optional[str] = None


class MeteorListResponse(BaseModel):
    totalItems: int
    meteors: List[dict]
    totalPages: int
    currentPage: int
