from datetime import datetime

from pydantic import BaseModel


class StationInfo(BaseModel):
    name: str
    code: str
    log_time: datetime


class StationLogPayload(BaseModel):
    station: StationInfo

