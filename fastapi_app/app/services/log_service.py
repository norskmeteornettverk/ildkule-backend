from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import LogStation


class LogService:
    def log(self, session: Session, station_name: str, code: str, log_time):
        record = LogStation(
            station_name=station_name,
            code=code,
            log_time=log_time,
        )
        session.add(record)
        session.flush()
        return record

    def list(self, session: Session, limit: int = 200):
        stmt = select(LogStation).order_by(LogStation.id.desc()).limit(limit)
        return session.scalars(stmt).all()

