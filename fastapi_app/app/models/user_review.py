from sqlalchemy import Column, ForeignKey, Integer, SmallInteger
from sqlalchemy.orm import relationship

from ..db import Base
from .types import unsigned_int


class UserReview(Base):
    __tablename__ = "user_review"

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    meteor_id = Column(unsigned_int(), ForeignKey("meteor.id"), primary_key=True)
    confirmed = Column(SmallInteger, nullable=True)

    user = relationship("User", back_populates="reviews")
    meteor = relationship("Meteor", back_populates="reviews")
