from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy import BigInteger, Column, Float, ForeignKey, Index, Integer, UniqueConstraint
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
    event_timestamp_us = Column(BigInteger, nullable=True)
    coord_long = Column(Float, nullable=True)
    coord_lat = Column(Float, nullable=True)
    ams_coord_long = Column(Float, nullable=True)
    ams_coord_lat = Column(Float, nullable=True)
    centroid_coord_long = Column(Float, nullable=True)
    centroid_coord_lat = Column(Float, nullable=True)
    centroid2_coord_long = Column(Float, nullable=True)
    centroid2_coord_lat = Column(Float, nullable=True)
    gnomonic_x = Column(Float, nullable=True)
    gnomonic_y = Column(Float, nullable=True)
    brightness = Column(Float, nullable=True)
    dct = Column(Float, nullable=True)
    size = Column(Float, nullable=True)
    frame_brightness = Column(Float, nullable=True)

    observation = relationship("ObservationCamData", back_populates="trail_points")

    @property
    def event_timestamp(self) -> float | None:
        if self.event_timestamp_us is None:
            return None
        return self.event_timestamp_us / 1_000_000.0

    @event_timestamp.setter
    def event_timestamp(self, value: float | int | str | None) -> None:
        if value is None:
            self.event_timestamp_us = None
            return
        try:
            parsed = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError("event_timestamp must be numeric seconds") from exc
        if not parsed.is_finite():
            raise ValueError("event_timestamp must be finite numeric seconds")
        self.event_timestamp_us = int(
            (parsed * Decimal("1000000")).to_integral_value(rounding=ROUND_HALF_UP)
        )
