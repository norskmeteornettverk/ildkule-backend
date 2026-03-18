from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class ObservationCamData(Base):
    """Stores one camera observation, raw trail rows, and import lifecycle state."""

    __tablename__ = "observation_cam_data"
    __table_args__ = (
        UniqueConstraint("observation_key", name="uq_observation_key"),
        Index("ix_observation_cam_data_event_id", "event_id"),
        Index("ix_observation_cam_data_cam_id", "cam_id"),
    )

    id = Column(unsigned_int(), primary_key=True, autoincrement=True)
    event_id = Column(unsigned_int(), ForeignKey("event.id"), nullable=False)
    cam_id = Column(unsigned_int(), ForeignKey("cam.id"), nullable=False)
    observation_key = Column(String(255), nullable=False, index=True)
    source_hash = Column(String(64), nullable=False)
    event_start_utc = Column(DateTime, nullable=True, index=True)
    created = Column(DateTime, nullable=False, default=datetime.utcnow)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deletion_reason = Column(String(50), nullable=True)
    trail_frames = Column(Integer)
    trail_duration = Column(Float)
    trail_slope = Column(Float)
    trail_offset = Column(Float)
    trail_speed = Column(Float)
    trail_correlation = Column(Float)
    trail_positions = Column(Text)
    trail_timestamps = Column(Text)
    trail_coordinates = Column(Text)
    trail_ams_coords = Column(Text)
    trail_gnomonic = Column(Text)
    trail_midpoint = Column(String(1000))
    trail_arc = Column(Float)
    trail_brightness = Column(Text)
    trail_dct_midpoint = Column(Integer)
    trail_dct = Column(Text)
    trail_size = Column(Text)
    trail_frame_brightness = Column(Text)
    video_start = Column(DateTime)
    video_end = Column(DateTime)
    video_wallclock = Column(DateTime)
    video_heigth = Column(Integer)
    video_raw = Column(Integer)
    video_flash = Column(Integer)
    config_swidth = Column(Integer)
    config_sheight = Column(Integer)
    config_swdec = Column(Integer)
    config_downscale_thr = Column(Integer)
    config_mintrail_sec = Column(Float)
    config_maxtrail_sec = Column(Float)
    config_mintrail = Column(Float)
    config_maxtrail = Column(Float)
    config_minspeed = Column(Float)
    config_maxspeed = Column(Float)
    config_minspeed_kms = Column(Float)
    config_maxspeed_kms = Column(Float)
    config_leveltest = Column(Integer)
    config_numspots = Column(Integer)
    config_brightness = Column(Integer)
    config_flash_thr = Column(Float)
    config_lookahead = Column(Integer)
    config_exit = Column(Integer)
    config_peak = Column(Float)
    config_filter = Column(Integer)
    config_dct_threshold = Column(Float)
    config_correlation = Column(Float)
    config_spacing_correlation = Column(Float)
    config_gnomonic_correlation = Column(Float)
    config_nothreads = Column(Integer)
    config_lastreport_ts = Column(BigInteger)
    config_ts_future = Column(Integer)
    config_snapshot_interval = Column(Integer)
    config_snapshot_integration = Column(Integer)
    config_log_file = Column(String(45))
    config_mask_file = Column(String(45))
    config_max_file = Column(String(45))
    config_save_file = Column(String(45))
    config_pto_file = Column(String(45))
    config_pto_scale = Column(Float)
    config_pto_width = Column(Float)
    config_pto_height = Column(Float)
    config_execute = Column(String(45))
    config_event_dir = Column(String(45))
    config_snapshot_dir = Column(String(45))
    summary_latitude = Column(Float)
    summary_longitude = Column(Float)
    summary_elevation = Column(Integer)
    summary_timestamp = Column(DateTime)
    summary_startpos = Column(Float)
    summary_endpos = Column(Float)
    summary_duration = Column(Float)
    summary_sunalt = Column(Float)
    summary_recalibrated = Column(Integer)
    summary_meteor_probability = Column(Float)

    event = relationship("Event", back_populates="observation_data")
    cam = relationship("Cam", back_populates="observations")
    trail_points = relationship(
        "ObservationTrailPoint",
        back_populates="observation",
        cascade="all,delete-orphan",
    )
