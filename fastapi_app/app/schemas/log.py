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


class StationNetworkCamera(BaseModel):
    cam_name: str = Field(..., description="Camera name for the station.")
    last_seen: datetime | None = Field(
        default=None,
        description="Best current last-seen timestamp for this camera.",
    )
    connected: bool = Field(
        ...,
        description="Derived online or offline flag for this camera.",
    )
    snapshot_url: str | None = Field(
        default=None,
        description="Snapshot or latest image URL for this camera when available.",
    )
    last_image_url: str | None = Field(
        default=None,
        description="Latest known stored observation preview image for this camera when available.",
    )


class StationNetworkStation(BaseModel):
    station_name: str = Field(..., description="Station name.")
    last_seen: datetime | None = Field(
        default=None,
        description="Best current last-seen timestamp for the station.",
    )
    connected: bool = Field(
        ...,
        description="Derived online or offline flag for the station.",
    )
    camera_count: int = Field(..., description="Number of cameras registered for the station.")
    cameras: list[StationNetworkCamera] = Field(
        ...,
        description="Per-camera status rows for this station.",
    )


class StationNetworkResponse(BaseModel):
    offline_after_minutes: int = Field(
        ...,
        description="Threshold used when deriving connected versus offline status.",
    )
    stations: list[StationNetworkStation] = Field(
        ...,
        description="Aggregated station and camera status rows.",
    )
