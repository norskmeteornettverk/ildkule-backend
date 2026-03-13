from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class Cam(Base):
    __tablename__ = "cam"

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    station_id = Column(unsigned_int(), ForeignKey("station.id"), nullable=False)
    cam_name = Column(String(100), nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)

    station = relationship("Station", back_populates="cams")
    observations = relationship(
        "ObservationCamData", back_populates="cam", cascade="all,delete-orphan"
    )
