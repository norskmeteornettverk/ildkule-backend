from datetime import datetime

from pydantic import BaseModel, Field


class StationInfo(BaseModel):
    name: str
    code: str
    log_time: datetime


class StationLogPayload(BaseModel):
    station: StationInfo


class StationLogEntry(BaseModel):
    id: int = Field(..., description="Stored station-log row id.")
    station_name: str = Field(..., description="Station name from the pushed log row.")
    code: str = Field(..., description="Short station log code as stored by the backend.")
    log_time: datetime = Field(..., description="Timestamp sent by the station for this log row.")
    created_at: datetime = Field(..., description="Backend insert timestamp for this log row.")


class StationLogWriteResponse(BaseModel):
    msg: str = Field(..., description="Short write status message.")
    id: int = Field(..., description="Stored station-log row id.")
