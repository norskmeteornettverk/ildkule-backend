from sqlalchemy import Column, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class ObservationTrailPoint(Base):
    """Stores one frame-aligned trail point extracted from event.txt."""

    __tablename__ = "observation_trail_point"
    __table_args__ = (
        UniqueConstraint(
            "observation_id",
            "frame_index",
            name="uq_observation_trail_point_frame",
        ),
        Index("ix_observation_trail_point_observation_id", "observation_id"),
    )

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    observation_id = Column(
        unsigned_int(),
        ForeignKey("observation_cam_data.id"),
        nullable=False,
    )
    frame_index = Column(Integer, nullable=False)
    pixel_x = Column(Float, nullable=True)
    pixel_y = Column(Float, nullable=True)
    event_timestamp = Column(Float, nullable=True)
    coord_long = Column(Float, nullable=True)
    coord_lat = Column(Float, nullable=True)
    ams_coord_long = Column(Float, nullable=True)
    ams_coord_lat = Column(Float, nullable=True)
    gnomonic_x = Column(Float, nullable=True)
    gnomonic_y = Column(Float, nullable=True)
    brightness = Column(Float, nullable=True)
    dct = Column(Float, nullable=True)
    size = Column(Float, nullable=True)
    frame_brightness = Column(Float, nullable=True)

    observation = relationship("ObservationCamData", back_populates="trail_points")
