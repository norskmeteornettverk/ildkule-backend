from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from ..db import Base


class LogStation(Base):
    __tablename__ = "log_station"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False)
    log_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

