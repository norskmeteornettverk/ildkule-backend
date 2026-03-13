from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class MeteorResEntry(Base):
    """Stores every parsed line from a meteor .res file."""

    __tablename__ = "meteor_res_entry"
    __table_args__ = (
        UniqueConstraint("meteor_id", "line_no", name="uq_meteor_res_entry_line"),
        Index("ix_meteor_res_entry_meteor_id", "meteor_id"),
    )

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    meteor_id = Column(unsigned_int(), ForeignKey("meteor.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    entry_type = Column(String(20), nullable=False)
    label = Column(String(20), nullable=True)
    long1 = Column(Float, nullable=True)
    lat1 = Column(Float, nullable=True)
    long2 = Column(Float, nullable=True)
    lat2 = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    raw_line = Column(String(500), nullable=False)

    meteor = relationship("Meteor", back_populates="res_entries")
