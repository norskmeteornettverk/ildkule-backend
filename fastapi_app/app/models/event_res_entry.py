from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class EventResEntry(Base):
    """Stores every parsed line from a event .res file."""

    __tablename__ = "event_res_entry"
    __table_args__ = (
        UniqueConstraint("event_id", "line_no", name="uq_event_res_entry_line"),
        Index("ix_event_res_entry_event_id", "event_id"),
    )

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    event_id = Column(unsigned_int(), ForeignKey("event.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    entry_type = Column(String(20), nullable=False)
    label = Column(String(20), nullable=True)
    long1 = Column(Float, nullable=True)
    lat1 = Column(Float, nullable=True)
    long2 = Column(Float, nullable=True)
    lat2 = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    raw_line = Column(String(500), nullable=False)

    event = relationship("Event", back_populates="res_entries")
