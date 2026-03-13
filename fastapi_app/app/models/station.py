from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class Station(Base):
    __tablename__ = "station"

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    station_name = Column(String(100), unique=True, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)

    cams = relationship("Cam", back_populates="station", cascade="all,delete-orphan")
