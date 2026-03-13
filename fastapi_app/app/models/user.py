from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..db import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False, default="ROLE_USER")
    user_level = Column(String(255), nullable=True, default="0")
    tutorial_completed = Column(Boolean, nullable=False, default=False)
    confirmed = Column(Boolean, nullable=False, default=False)
    confirm_token = Column(String(1000), nullable=True)
    password_reset_token = Column(String(1000), nullable=True)
    password_reset_request_time = Column(DateTime, nullable=True)
    create_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    update_time = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    reviews = relationship("UserReview", back_populates="user", cascade="all,delete")

