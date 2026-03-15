from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, SmallInteger, String
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class Event(Base):
    """Represents one event event and its import lifecycle state."""

    __tablename__ = "event"

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    datetimetag = Column(String(14), unique=True, nullable=False)
    location = Column(String(100), nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    track_startheight = Column(Float)
    track_endheight = Column(Float)
    track_groundtrack = Column(Float)
    track_course = Column(Float)
    track_incidence = Column(Float)
    track_speed = Column(Float)
    track_speed_source = Column(String(100))
    track_startlat = Column(Float)
    track_startlong = Column(Float)
    track_endlat = Column(Float)
    track_endlong = Column(Float)
    fit_error = Column(Float)
    fit_quality = Column(Float)
    radiant_ra = Column(Float)
    radiant_dec = Column(Float)
    radiant_ecl_long = Column(Float)
    radiant_ecl_lat = Column(Float)
    radiant_shower = Column(String(100))
    radiant_zenith_attractor = Column(String(100))
    timestamp = Column(String(100))
    date = Column(DateTime)
    camera_confirmed = Column(SmallInteger)
    user_confirmed = Column(SmallInteger)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deletion_reason = Column(String(50), nullable=True)

    observation_data = relationship(
        "ObservationCamData", back_populates="event", cascade="all,delete-orphan"
    )
    res_entries = relationship(
        "EventResEntry", back_populates="event", cascade="all,delete-orphan"
    )
    reviews = relationship(
        "UserReview", back_populates="event", cascade="all,delete-orphan"
    )
