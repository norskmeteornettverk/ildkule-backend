from __future__ import annotations

from datetime import datetime
from math import isfinite
from math import ceil
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Integer,
    SmallInteger,
    and_,
    case,
    delete,
    func,
    or_,
    select,
    text,
)
from sqlalchemy.orm import Session, selectinload

from ..models import (
    Cam,
    Meteor,
    MeteorResEntry,
    ObservationCamData,
    ObservationTrailPoint,
    Station,
    UserReview,
)
from .file_mapper import FileToObjectMapper, MeteorRecord, ObservationRecord
from ..utils.serialization import (
    serialize_meteor,
    serialize_meteor_list,
    serialize_res_entry,
    serialize_trail_point,
)


class MeteorService:
    MISSING_FROM_IMPORT = "missing_from_import"

    def _visibility_filter(self, include_deleted: bool):
        if include_deleted:
            return None
        return Meteor.is_deleted.is_(False)

    def _ratings_subquery(self):
        return (
            select(
                UserReview.meteor_id.label("meteor_id"),
                func.sum(case((UserReview.confirmed == 1, 1), else_=0)).label(
                    "positive_ratings"
                ),
                func.sum(case((UserReview.confirmed == 0, 1), else_=0)).label(
                    "negative_ratings"
                ),
                func.count().label("ratings"),
            )
            .group_by(UserReview.meteor_id)
            .subquery()
        )

    def _base_filter(self, include_deleted: bool = False):
        filters = [or_(Meteor.user_confirmed.is_(None), Meteor.user_confirmed != 0)]
        visibility_filter = self._visibility_filter(include_deleted)
        if visibility_filter is not None:
            filters.append(visibility_filter)
        return and_(*filters)

    def list_meteors(
        self,
        session: Session,
        page: int,
        limit: int,
        order_by: str,
        order: str,
        include_deleted: bool = False,
    ) -> dict:
        ratings_subquery = self._ratings_subquery()
        sortable_columns = {
            "date": Meteor.date,
            "crossbearing": Meteor.camera_confirmed,
            "ratings": ratings_subquery.c.ratings,
        }
        column = sortable_columns.get(order_by, Meteor.date)
        direction = column.desc() if order.lower() == "desc" else column.asc()

        offset = max(page - 1, 0) * limit
        stmt = (
            select(
                Meteor,
                ratings_subquery.c.ratings,
                ratings_subquery.c.positive_ratings,
                ratings_subquery.c.negative_ratings,
            )
            .outerjoin(ratings_subquery, Meteor.id == ratings_subquery.c.meteor_id)
            .where(self._base_filter(include_deleted))
            .order_by(direction)
            .limit(limit)
            .offset(offset)
        )
        results = session.execute(stmt).all()

        meteors = []
        for meteor, ratings, positive_ratings, negative_ratings in results:
            payload = serialize_meteor(meteor)
            payload["ratings"] = ratings or 0
            payload["positive_ratings"] = positive_ratings or 0
            payload["negative_ratings"] = negative_ratings or 0
            meteors.append(payload)

        total_items = session.scalar(
            select(func.count()).select_from(Meteor).where(self._base_filter(include_deleted))
        )
        total_pages = ceil(total_items / limit) if limit else 1
        current_page = page if page > 0 else 1
        return {
            "totalItems": total_items,
            "meteors": meteors,
            "totalPages": total_pages,
            "currentPage": current_page,
        }

    def search(
        self,
        session: Session,
        search_term: str,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> dict:
        stmt = (
            select(Meteor)
            .where(
                self._base_filter(include_deleted),
                or_(
                    Meteor.location.ilike(f"%{search_term}%"),
                    Meteor.datetimetag.ilike(f"%{search_term}%"),
                ),
            )
            .order_by(Meteor.date.desc())
            .limit(limit)
        )
        meteors = session.scalars(stmt).all()
        return {
            "totalItems": len(meteors),
            "meteors": serialize_meteor_list(meteors),
            "totalPages": 1,
            "currentPage": 1,
        }

    def filter(
        self,
        session: Session,
        station_names: Optional[List[str]],
        years: Optional[List[int]],
        classes: Optional[List[str]],
        include_deleted: bool = False,
    ) -> List[dict]:
        stmt = select(Meteor).where(self._base_filter(include_deleted))

        if station_names:
            stmt = (
                stmt.join(
                    ObservationCamData,
                    Meteor.id == ObservationCamData.meteor_id,
                )
                .join(Cam, ObservationCamData.cam_id == Cam.id)
                .join(Station, Cam.station_id == Station.id)
                .where(Station.station_name.in_(station_names))
            )

        if years:
            stmt = stmt.where(func.extract("year", Meteor.date).in_(years))

        if classes:
            meteor_class_case = case(
                (
                    func.coalesce(Meteor.track_endheight, 0) < 40,
                    "Meteorittkandidat",
                ),
                (
                    Meteor.track_endheight.isnot(None),
                    "Krysspeilet",
                ),
                else_="Upeilet",
            )
            stmt = stmt.where(meteor_class_case.in_(classes))

        stmt = stmt.order_by(Meteor.datetimetag.desc()).limit(100)
        meteors = session.scalars(stmt).unique().all()
        return serialize_meteor_list(meteors)

    def get_meteor(
        self, session: Session, meteor_id: int, include_deleted: bool = False
    ) -> dict:
        stmt = (
            select(Meteor)
            .options(
                selectinload(Meteor.observation_data)
                .selectinload(ObservationCamData.trail_points),
                selectinload(Meteor.observation_data)
                .selectinload(ObservationCamData.cam)
                .selectinload(Cam.station),
                selectinload(Meteor.res_entries),
                selectinload(Meteor.reviews),
            )
            .where(Meteor.id == meteor_id, self._base_filter(include_deleted))
        )
        meteor = session.scalars(stmt).first()
        if not meteor:
            raise HTTPException(status_code=404, detail="Meteor not found")
        return serialize_meteor(
            meteor,
            include_relationships=True,
            include_deleted=include_deleted,
        )

    def get_meteor_res_entries(
        self,
        session: Session,
        meteor_id: int,
        limit: int = 500,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> dict:
        """Return paginated raw .res rows for one meteor."""

        meteor = session.get(Meteor, meteor_id)
        if not meteor or (meteor.is_deleted and not include_deleted):
            raise HTTPException(status_code=404, detail="Meteor not found")

        total_items = session.scalar(
            select(func.count())
            .select_from(MeteorResEntry)
            .where(MeteorResEntry.meteor_id == meteor_id)
        ) or 0
        stmt = (
            select(MeteorResEntry)
            .where(MeteorResEntry.meteor_id == meteor_id)
            .order_by(MeteorResEntry.line_no.asc())
            .offset(max(offset, 0))
            .limit(max(limit, 1))
        )
        entries = session.scalars(stmt).all()
        return {
            "totalItems": total_items,
            "limit": limit,
            "offset": offset,
            "resEntries": [serialize_res_entry(entry) for entry in entries],
        }

    def get_observation_trail_points(
        self,
        session: Session,
        observation_id: int,
        limit: int = 500,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> dict:
        """Return paginated frame-aligned trail points for one observation."""

        observation = session.get(ObservationCamData, observation_id)
        if not observation or (observation.is_deleted and not include_deleted):
            raise HTTPException(status_code=404, detail="Observation not found")

        total_items = session.scalar(
            select(func.count())
            .select_from(ObservationTrailPoint)
            .where(ObservationTrailPoint.observation_id == observation_id)
        ) or 0
        stmt = (
            select(ObservationTrailPoint)
            .where(ObservationTrailPoint.observation_id == observation_id)
            .order_by(ObservationTrailPoint.frame_index.asc())
            .offset(max(offset, 0))
            .limit(max(limit, 1))
        )
        points = session.scalars(stmt).all()
        return {
            "totalItems": total_items,
            "limit": limit,
            "offset": offset,
            "trailPoints": [serialize_trail_point(point) for point in points],
        }

    def review_meteor(
        self, session: Session, meteor_id: int, user_id: int, rating: int
    ) -> bool:
        meteor = session.get(Meteor, meteor_id)
        if not meteor:
            raise HTTPException(status_code=404, detail="Meteor not found")
        review = session.get(UserReview, (user_id, meteor_id))
        if not review:
            review = UserReview(user_id=user_id, meteor_id=meteor_id)
        review.confirmed = rating
        session.add(review)
        return True

    def update_user_confirmation(
        self, session: Session, meteor_id: int, classification: Optional[str]
    ) -> Meteor:
        meteor = session.get(Meteor, meteor_id)
        if not meteor:
            raise HTTPException(status_code=404, detail="Meteor not found")
        confirmed = -1
        if classification in {"1", "Positive"}:
            confirmed = 1
        elif classification in {"0", "Negative"}:
            confirmed = 0
        meteor.user_confirmed = confirmed
        session.add(meteor)
        return meteor

    def get_insight(self, session: Session, report_name: str) -> list[dict]:
        dialect = session.bind.dialect.name if session.bind else ""
        if dialect == "sqlite":
            station_name_expr = "upper(substr(s.station_name, 1, 1)) || substr(s.station_name, 2)"
            days_since_expr = "CAST(julianday('now') - julianday(max(m.date)) AS INTEGER)"
        else:
            station_name_expr = "CONCAT(UCASE(LEFT( s.station_name, 1)), SUBSTRING( s.station_name, 2))"
            days_since_expr = "DATEDIFF(now(),max(m.date))"

        if report_name == "cam":
            sql = f"""
            select  {station_name_expr} as Stasjonsnavn,
            c.cam_name as Kameranavn,
            min(m.date) ForsteObservasjonsTidspunkt,
            max(m.date) SisteObervasjonsTidspunkt,
            count(distinct date(m.date)) DagerMedObservasjoner,
            {days_since_expr} as DagerSidenSisteObservasjon,
            count(*) as Kameraopptak,
            count(distinct m.id) as Meteorer,
            count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
            COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
            from station as s
            left outer join cam as c on s.id = c.station_id
            left outer join observation_cam_data as d on c.id = d.cam_id
            left outer join meteor as m on d.meteor_id = m.id
            group by {station_name_expr}, c.cam_name
            order by {station_name_expr},c.cam_name
            """
        elif report_name == "station":
            sql = f"""
            select {station_name_expr} as Stasjonsnavn,
            min(m.date) ForsteObservasjonsTidspunkt,
            max(m.date) SisteObervasjonsTidspunkt,
            count(distinct date(m.date)) DagerMedObservasjoner,
            {days_since_expr} as DagerSidenSisteObservasjon,
            count(*) as Kameraopptak,
            count(distinct m.id) as Meteorer,
            count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
            COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
            from station as s
            left outer join cam as c on s.id = c.station_id
            left outer join observation_cam_data as d on c.id = d.cam_id
            left outer join meteor as m on d.meteor_id = m.id
            group by {station_name_expr}
            order by {station_name_expr}
            """
        elif report_name == "total":
            sql = f"""
            select min(m.date) ForsteObservasjonsTidspunkt,
            max(m.date) SisteObervasjonsTidspunkt,
            count(distinct date(m.date)) DagerMedObservasjoner,
            {days_since_expr} as DagerSidenSisteObservasjon,
            count(*) as Kameraopptak,
            count(distinct m.id) as Meteorer,
            count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
            COUNT(DISTINCT CASE WHEN m.track_startheight is not null and m.track_startheight < 40 THEN m.id END) Meteorittkandidater
            from station as s
            left outer join cam as c on s.id = c.station_id
            left outer join observation_cam_data as d on c.id = d.cam_id
            left outer join meteor as m on d.meteor_id = m.id
            """
        elif report_name == "coordinates":
            sql = """
            SELECT track_endlat as lat, track_endlong as lng
            FROM meteor
            WHERE track_endlat IS NOT NULL
            """
        else:
            raise HTTPException(status_code=404, detail="Unknown insight report")

        records = session.execute(text(sql)).mappings().all()
        if report_name == "total" and records:
            return [dict(records[0])]
        return [dict(row) for row in records]

    def load_from_files(
        self,
        session: Session,
        data_directory: str,
        date_from: str,
        date_to: str,
    ) -> int:
        self._validate_date(date_from)
        self._validate_date(date_to)
        mapper = FileToObjectMapper(data_directory, date_from, date_to)
        records = mapper.map()
        import_started_at = datetime.utcnow()
        station_cache: dict[str, int] = {}
        cam_cache: dict[tuple[int, str], int] = {}
        processed = 0
        seen_meteor_tags: set[str] = set()
        seen_observation_keys: set[str] = set()
        for record in records:
            meteor_obj = self._upsert_meteor(session, record, import_started_at)
            self._replace_res_entries(session, meteor_obj.id, record)
            processed += 1
            seen_meteor_tags.add(meteor_obj.datetimetag)
            for observation in record.observations:
                station_id = self._get_station_id(session, observation, station_cache)
                cam_id = self._get_cam_id(session, observation, station_id, cam_cache)
                self._upsert_observation(
                    session,
                    meteor_obj.id,
                    cam_id,
                    observation,
                    import_started_at,
                )
                seen_observation_keys.add(observation.observation_key)
        self._mark_missing_meteors_deleted(
            session,
            mapper.date_strings,
            seen_meteor_tags,
            import_started_at,
        )
        self._mark_missing_observations_deleted(
            session,
            mapper.date_strings,
            seen_observation_keys,
            import_started_at,
        )
        return processed

    def _validate_date(self, date_value: str) -> None:
        try:
            datetime.strptime(date_value, "%Y%m%d")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provided dates are not valid: {date_value}",
            ) from exc

    def _upsert_meteor(
        self,
        session: Session,
        record: MeteorRecord,
        import_started_at: datetime,
    ) -> Meteor:
        datetimetag = record.meteor.get("datetimetag")
        stmt = select(Meteor).where(Meteor.datetimetag == datetimetag)
        meteor = session.scalars(stmt).first()
        meteor_columns = {column.name: column for column in Meteor.__table__.columns}

        payload = {
            key: self._coerce_column_value(meteor_columns[key], value)
            for key, value in record.meteor.items()
            if key in meteor_columns
        }
        if meteor:
            for key, value in payload.items():
                setattr(meteor, key, value)
        else:
            meteor = Meteor(**payload)
            meteor.first_seen_at = import_started_at
        meteor.last_seen_at = import_started_at
        meteor.deleted_at = None
        meteor.is_deleted = False
        meteor.deletion_reason = None
        session.add(meteor)
        session.flush()
        return meteor

    def _get_station_id(
        self,
        session: Session,
        observation: ObservationRecord,
        cache: dict[str, int],
    ) -> int:
        name = observation.station_name
        if name in cache:
            return cache[name]
        stmt = select(Station).where(Station.station_name == name)
        station = session.scalars(stmt).first()
        if not station:
            station = Station(station_name=name)
            session.add(station)
            session.flush()
        cache[name] = station.id
        return station.id

    def _get_cam_id(
        self,
        session: Session,
        observation: ObservationRecord,
        station_id: int,
        cache: dict[tuple[int, str], int],
    ) -> int:
        key = (station_id, observation.cam_name)
        if key in cache:
            return cache[key]
        stmt = select(Cam).where(
            Cam.station_id == station_id, Cam.cam_name == observation.cam_name
        )
        cam = session.scalars(stmt).first()
        if not cam:
            cam = Cam(cam_name=observation.cam_name, station_id=station_id)
            session.add(cam)
            session.flush()
        cache[key] = cam.id
        return cam.id

    def _upsert_observation(
        self,
        session: Session,
        meteor_id: int,
        cam_id: int,
        observation: ObservationRecord,
        import_started_at: datetime,
    ) -> None:
        """Upsert by stable observation key so regrouped meteors do not duplicate data."""

        stmt = select(ObservationCamData).where(
            ObservationCamData.observation_key == observation.observation_key
        )
        existing = session.scalars(stmt).first()
        columns = {column.name: column for column in ObservationCamData.__table__.columns}

        payload = {
            key: self._coerce_column_value(columns[key], value)
            for key, value in observation.values.items()
            if key in columns
        }
        payload["meteor_id"] = meteor_id
        payload["cam_id"] = cam_id
        payload["observation_key"] = observation.observation_key
        payload["source_hash"] = observation.source_hash
        payload["event_start_utc"] = observation.event_start_utc

        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
        else:
            existing = ObservationCamData(**payload)
            existing.first_seen_at = import_started_at
        existing.last_seen_at = import_started_at
        existing.deleted_at = None
        existing.is_deleted = False
        existing.deletion_reason = None
        session.add(existing)
        session.flush()
        self._replace_trail_points(session, existing.id, observation)

    def _mark_missing_meteors_deleted(
        self,
        session: Session,
        imported_dates: List[str],
        seen_meteor_tags: set[str],
        import_started_at: datetime,
    ) -> None:
        """Soft-delete meteors in the imported date window that were not seen this run."""

        if not imported_dates:
            return

        stmt = select(Meteor).where(func.substr(Meteor.datetimetag, 1, 8).in_(imported_dates))
        if seen_meteor_tags:
            stmt = stmt.where(Meteor.datetimetag.not_in(seen_meteor_tags))
        missing = session.scalars(stmt).all()
        for meteor in missing:
            meteor.is_deleted = True
            meteor.deleted_at = import_started_at
            meteor.deletion_reason = self.MISSING_FROM_IMPORT
            session.add(meteor)

    def _mark_missing_observations_deleted(
        self,
        session: Session,
        imported_dates: List[str],
        seen_observation_keys: set[str],
        import_started_at: datetime,
    ) -> None:
        """Soft-delete observations linked to imported-date meteors when they disappear."""

        if not imported_dates:
            return

        stmt = (
            select(ObservationCamData)
            .join(Meteor, ObservationCamData.meteor_id == Meteor.id)
            .where(func.substr(Meteor.datetimetag, 1, 8).in_(imported_dates))
        )
        if seen_observation_keys:
            stmt = stmt.where(ObservationCamData.observation_key.not_in(seen_observation_keys))
        missing = session.scalars(stmt).all()
        for observation in missing:
            observation.is_deleted = True
            observation.deleted_at = import_started_at
            observation.deletion_reason = self.MISSING_FROM_IMPORT
            session.add(observation)

    def _replace_res_entries(
        self,
        session: Session,
        meteor_id: int,
        record: MeteorRecord,
    ) -> None:
        """Replace all persisted .res rows for one meteor during reload."""

        session.execute(
            delete(MeteorResEntry).where(MeteorResEntry.meteor_id == meteor_id)
        )
        if not record.res_entries:
            return
        session.add_all(
            [
                MeteorResEntry(
                    meteor_id=meteor_id,
                    line_no=entry.line_no,
                    entry_type=entry.entry_type,
                    label=entry.label,
                    long1=entry.long1,
                    lat1=entry.lat1,
                    long2=entry.long2,
                    lat2=entry.lat2,
                    height=entry.height,
                    raw_line=entry.raw_line,
                )
                for entry in record.res_entries
            ]
        )

    def _replace_trail_points(
        self,
        session: Session,
        observation_id: int,
        observation: ObservationRecord,
    ) -> None:
        """Replace all persisted trail rows for one observation during reload."""

        session.execute(
            delete(ObservationTrailPoint).where(
                ObservationTrailPoint.observation_id == observation_id
            )
        )
        if not observation.trail_points:
            return
        session.add_all(
            [
                ObservationTrailPoint(
                    observation_id=observation_id,
                    frame_index=point.frame_index,
                    pixel_x=point.pixel_x,
                    pixel_y=point.pixel_y,
                    event_timestamp=point.event_timestamp,
                    coord_long=point.coord_long,
                    coord_lat=point.coord_lat,
                    gnomonic_x=point.gnomonic_x,
                    gnomonic_y=point.gnomonic_y,
                    brightness=point.brightness,
                    dct=point.dct,
                    size=point.size,
                    frame_brightness=point.frame_brightness,
                )
                for point in observation.trail_points
            ]
        )

    def _coerce_column_value(self, column, value):
        """Normalise file-derived values to the SQLAlchemy column type."""

        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

        column_type = column.type
        if isinstance(column_type, DateTime):
            return self._coerce_datetime(value)
        if isinstance(column_type, (Float, Integer, BigInteger, SmallInteger)):
            return self._coerce_number(value, column_type)
        return value

    def _coerce_datetime(self, value):
        if isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None
        parsed = FileToObjectMapper._parse_event_datetime(value)
        if parsed is not None:
            return parsed
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def _coerce_number(self, value, column_type):
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not isfinite(value):
                return None
            if isinstance(column_type, (Integer, BigInteger, SmallInteger)):
                return int(value)
            return float(value)
        if not isinstance(value, str):
            return None
        match = None
        for token in value.replace(",", ".").split():
            try:
                numeric = float(token)
                match = numeric
                break
            except ValueError:
                continue
        if match is None:
            return None
        if not isfinite(match):
            return None
        if isinstance(column_type, (Integer, BigInteger, SmallInteger)):
            return int(match)
        return float(match)
