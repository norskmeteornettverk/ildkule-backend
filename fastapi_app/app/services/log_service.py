from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..models import Cam, LogStation, ObservationCamData, Station
from ..utils.serialization import serialize_observation

settings = get_settings()


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

    def station_network(self, session: Session) -> dict:
        offline_delta = timedelta(minutes=settings.station_network_offline_minutes)
        offline_cutoff = datetime.utcnow() - offline_delta

        latest_station_logs = {
            station_name: log_time
            for station_name, log_time in session.execute(
                select(LogStation.station_name, func.max(LogStation.log_time)).group_by(
                    LogStation.station_name
                )
            ).all()
        }

        stations = session.scalars(
            select(Station)
            .options(selectinload(Station.cams))
            .order_by(Station.station_name.asc())
        ).all()

        response_stations = []
        for station in stations:
            camera_rows = []
            station_last_seen = latest_station_logs.get(station.station_name)
            station_coordinate = session.scalars(
                select(ObservationCamData)
                .join(ObservationCamData.cam)
                .where(Cam.station_id == station.id)
                .where(ObservationCamData.summary_latitude.isnot(None))
                .where(ObservationCamData.summary_longitude.isnot(None))
                .order_by(
                    ObservationCamData.event_start_utc.desc().nullslast(),
                    ObservationCamData.created.desc().nullslast(),
                    ObservationCamData.id.desc(),
                )
                .limit(1)
            ).first()
            for cam in sorted(station.cams, key=lambda item: item.cam_name):
                observation = session.scalars(
                    select(ObservationCamData)
                    .options(
                        selectinload(ObservationCamData.cam).selectinload(Cam.station),
                        selectinload(ObservationCamData.event),
                    )
                    .where(ObservationCamData.cam_id == cam.id)
                    .order_by(
                        ObservationCamData.event_start_utc.desc().nullslast(),
                        ObservationCamData.created.desc().nullslast(),
                        ObservationCamData.id.desc(),
                    )
                    .limit(1)
                ).first()
                last_seen = None
                last_image_url = None
                snapshot_url = None
                if observation:
                    last_seen = observation.event_start_utc or observation.created
                    payload = serialize_observation(observation)
                    last_image_url = payload.get("preview", {}).get("thumbnail_url")
                if settings.station_snapshot_base_url:
                    snapshot_url = (
                        f"{settings.station_snapshot_base_url.rstrip('/')}/"
                        f"{station.station_name}/{cam.cam_name}/snapshot.jpg"
                    )
                elif last_image_url:
                    snapshot_url = last_image_url
                camera_connected = bool(last_seen and last_seen >= offline_cutoff)
                camera_rows.append(
                    {
                        "cam_name": cam.cam_name,
                        "last_seen": last_seen,
                        "connected": camera_connected,
                        "snapshot_url": snapshot_url,
                        "last_image_url": last_image_url,
                    }
                )
                if last_seen and (station_last_seen is None or last_seen > station_last_seen):
                    station_last_seen = last_seen

            station_connected = bool(
                station_last_seen and station_last_seen >= offline_cutoff
            )
            response_stations.append(
                {
                    "station_name": station.station_name,
                    "last_seen": station_last_seen,
                    "latitude": (
                        station_coordinate.summary_latitude if station_coordinate else None
                    ),
                    "longitude": (
                        station_coordinate.summary_longitude if station_coordinate else None
                    ),
                    "connected": station_connected,
                    "camera_count": len(camera_rows),
                    "cameras": camera_rows,
                }
            )

        return {
            "offline_after_minutes": settings.station_network_offline_minutes,
            "stations": response_stations,
        }
