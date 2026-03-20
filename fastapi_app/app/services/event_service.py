from __future__ import annotations

import csv
from datetime import datetime
import io
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

from ..config import get_settings
from ..models import (
    Cam,
    Event,
    EventResEntry,
    ObservationCamData,
    ObservationTrailPoint,
    Station,
    UserReview,
)
from .file_mapper import FileToObjectMapper, EventRecord, ObservationRecord
from ..utils.sql_ordering import desc_nulls_last
from ..utils.serialization import (
    serialize_event,
    serialize_event_list,
    serialize_res_entry,
    serialize_trail_point,
)

settings = get_settings()


class EventService:
    MISSING_FROM_IMPORT = "missing_from_import"
    EVENT_IMPORT_PRESERVED_COLUMNS = {
        "id",
        "datetimetag",
        "create_time",
        "user_confirmed",
        "first_seen_at",
        "last_seen_at",
        "deleted_at",
        "is_deleted",
        "deletion_reason",
    }
    OBSERVATION_IMPORT_PRESERVED_COLUMNS = {
        "id",
        "observation_key",
        "created",
        "first_seen_at",
        "last_seen_at",
        "deleted_at",
        "is_deleted",
        "deletion_reason",
    }

    def _visibility_filter(self, include_deleted: bool):
        if include_deleted:
            return None
        return Event.is_deleted.is_(False)

    def _ratings_subquery(self):
        return (
            select(
                UserReview.event_id.label("event_id"),
                func.sum(case((UserReview.confirmed == 1, 1), else_=0)).label(
                    "positive_ratings"
                ),
                func.sum(case((UserReview.confirmed == 0, 1), else_=0)).label(
                    "negative_ratings"
                ),
                func.count().label("ratings"),
            )
            .group_by(UserReview.event_id)
            .subquery()
        )

    def _base_filter(self, include_deleted: bool = False):
        filters = [or_(Event.user_confirmed.is_(None), Event.user_confirmed != 0)]
        visibility_filter = self._visibility_filter(include_deleted)
        if visibility_filter is not None:
            filters.append(visibility_filter)
        return and_(*filters)

    def _event_type_case(self):
        return case(
            (
                and_(
                    Event.track_endheight.isnot(None),
                    Event.track_endheight <= settings.candidate_max_end_height_km,
                ),
                "Meteorittkandidat",
            ),
            (
                Event.camera_confirmed == 1,
                "Krysspeilet",
            ),
            else_="Upeilet",
        )

    def _event_list_load_options(self):
        return selectinload(Event.observation_data).selectinload(
            ObservationCamData.cam
        ).selectinload(Cam.station)

    def _filtered_events_stmt(
        self,
        include_deleted: bool = False,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        stations: Optional[List[str]] = None,
        cross_station_confirmed: Optional[bool] = None,
        candidate_only: bool = False,
        require_coordinates: bool = False,
    ):
        stmt = (
            select(Event)
            .options(self._event_list_load_options())
            .where(self._base_filter(include_deleted))
        )
        if require_coordinates:
            stmt = stmt.where(
                Event.track_endlat.isnot(None),
                Event.track_endlong.isnot(None),
            )
        if from_date:
            stmt = stmt.where(Event.date >= self._parse_iso_date(from_date))
        if to_date:
            stmt = stmt.where(
                Event.date <= self._parse_iso_date(to_date, inclusive_end=True)
            )
        if stations:
            stmt = (
                stmt.join(ObservationCamData, Event.id == ObservationCamData.event_id)
                .join(Cam, ObservationCamData.cam_id == Cam.id)
                .join(Station, Cam.station_id == Station.id)
                .where(Station.station_name.in_(stations))
            )
        if cross_station_confirmed is not None:
            stmt = stmt.where(
                Event.camera_confirmed == (1 if cross_station_confirmed else 0)
            )
        if candidate_only:
            stmt = stmt.where(
                Event.track_endheight.isnot(None),
                Event.track_endheight <= settings.candidate_max_end_height_km,
                or_(
                    Event.track_speed.is_(None),
                    Event.track_speed <= settings.candidate_max_speed_kms,
                ),
            )
        return stmt

    def _proper_triangulation(self, event: Event) -> Optional[bool]:
        if (
            event.track_speed is None
            or event.track_endheight is None
            or event.track_startheight is None
        ):
            return None
        return bool(
            event.track_speed > 0
            and event.track_speed < 1000
            and event.track_endheight > 0
            and event.track_startheight > 0
            and event.track_startheight < 1000
            and event.track_startheight > event.track_endheight
        )

    def get_coordinate_insight(
        self,
        session: Session,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        stations: Optional[List[str]] = None,
        cross_station_confirmed: Optional[bool] = None,
        candidate_only: bool = False,
        include_deleted: bool = False,
    ) -> list[dict]:
        stmt = self._filtered_events_stmt(
            include_deleted=include_deleted,
            from_date=from_date,
            to_date=to_date,
            stations=stations,
            cross_station_confirmed=cross_station_confirmed,
            candidate_only=candidate_only,
            require_coordinates=True,
        ).order_by(*desc_nulls_last(Event.date), Event.id.desc())
        events = session.scalars(stmt).unique().all()
        rows: list[dict] = []
        for event in events:
            observations = event.observation_data or []
            station_names = sorted(
                {
                    record.cam.station.station_name
                    for record in observations
                    if record.cam and record.cam.station and record.cam.station.station_name
                }
            )
            camera_labels = sorted(
                {
                    f"{record.cam.cam_name}@{record.cam.station.station_name}"
                    for record in observations
                    if record.cam
                    and record.cam.cam_name
                    and record.cam.station
                    and record.cam.station.station_name
                }
            )
            ai_scores = [
                float(record.summary_meteor_probability)
                for record in observations
                if record.summary_meteor_probability is not None
            ]
            rows.append(
                {
                    "id": event.id,
                    "datetimetag": event.datetimetag,
                    "station_cam": ", ".join(camera_labels),
                    "number_of_stations": len(station_names),
                    "lat": event.track_endlat,
                    "lng": event.track_endlong,
                    "slat": event.track_startlat,
                    "slng": event.track_startlong,
                    "radiant_ra": event.radiant_ra,
                    "radiant_dec": event.radiant_dec,
                    "radiant_ecl_lat": event.radiant_ecl_lat,
                    "radiant_ecl_long": event.radiant_ecl_long,
                    "track_speed": event.track_speed,
                    "track_endheight": event.track_endheight,
                    "radiant_shower": event.radiant_shower,
                    "date": event.date.isoformat() if event.date else None,
                    "triangulation": bool(
                        event.radiant_ra is not None
                        and event.radiant_dec is not None
                        and event.radiant_ecl_lat is not None
                        and event.radiant_ecl_long is not None
                        and event.track_speed is not None
                        and event.track_endheight is not None
                    ),
                    "proper_triangulation": self._proper_triangulation(event),
                    "ai_score": max(ai_scores) if ai_scores else None,
                }
            )
        return rows

    def _admin_event_payload(
        self,
        event: Event,
        ratings: Optional[int],
        positive_ratings: Optional[int],
        negative_ratings: Optional[int],
    ) -> dict:
        payload = serialize_event(event, include_relationships=True)
        payload["datetimetag"] = event.datetimetag
        payload["date"] = event.date.isoformat() if event.date else None
        payload["camera_confirmed"] = 1 if event.camera_confirmed == 1 else 0
        payload["user_confirmed"] = (
            event.user_confirmed if event.user_confirmed is not None else -1
        )
        payload["ratings"] = ratings or 0
        payload["positive_ratings"] = positive_ratings or 0
        payload["negative_ratings"] = negative_ratings or 0
        return payload

    def list_events(
        self,
        session: Session,
        page: int,
        limit: int,
        order_by: str,
        order: str,
        include_deleted: bool = False,
        include_ratings: bool = False,
    ) -> dict:
        ratings_subquery = self._ratings_subquery()
        sortable_columns = {
            "date": Event.date,
            "crossbearing": Event.camera_confirmed,
            "ratings": ratings_subquery.c.ratings,
        }
        column = sortable_columns.get(order_by, Event.date)
        direction = column.desc() if order.lower() == "desc" else column.asc()

        offset = max(page - 1, 0) * limit
        stmt = (
            select(
                Event,
                ratings_subquery.c.ratings,
                ratings_subquery.c.positive_ratings,
                ratings_subquery.c.negative_ratings,
            )
            .options(self._event_list_load_options())
            .outerjoin(ratings_subquery, Event.id == ratings_subquery.c.event_id)
            .where(self._base_filter(include_deleted))
            .order_by(direction)
            .limit(limit)
            .offset(offset)
        )
        results = session.execute(stmt).all()

        events = []
        for event, ratings, positive_ratings, negative_ratings in results:
            if include_ratings:
                payload = self._admin_event_payload(
                    event,
                    ratings,
                    positive_ratings,
                    negative_ratings,
                )
            else:
                payload = serialize_event(event, include_relationships=True)
            events.append(payload)

        total_items = session.scalar(
            select(func.count()).select_from(Event).where(self._base_filter(include_deleted))
        )
        total_pages = ceil(total_items / limit) if limit else 1
        current_page = page if page > 0 else 1
        return {
            "totalItems": total_items,
            "events": events,
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
            select(Event)
            .options(self._event_list_load_options())
            .where(
                self._base_filter(include_deleted),
                or_(
                    Event.location.ilike(f"%{search_term}%"),
                    Event.datetimetag.ilike(f"%{search_term}%"),
                ),
            )
            .order_by(Event.date.desc())
            .limit(limit)
        )
        events = session.scalars(stmt).all()
        return {
            "totalItems": len(events),
            "events": serialize_event_list(events, include_relationships=True),
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
        limit: int = 100,
    ) -> dict:
        stmt = select(Event).options(self._event_list_load_options()).where(self._base_filter(include_deleted))

        if station_names:
            stmt = (
                stmt.join(
                    ObservationCamData,
                    Event.id == ObservationCamData.event_id,
                )
                .join(Cam, ObservationCamData.cam_id == Cam.id)
                .join(Station, Cam.station_id == Station.id)
                .where(Station.station_name.in_(station_names))
            )

        if years:
            stmt = stmt.where(func.extract("year", Event.date).in_(years))

        if classes:
            event_class_case = self._event_type_case()
            stmt = stmt.where(event_class_case.in_(classes))

        stmt = stmt.order_by(Event.datetimetag.desc()).limit(limit)
        events = session.scalars(stmt).unique().all()
        return {
            "totalItems": len(events),
            "events": serialize_event_list(events, include_relationships=True),
            "totalPages": 1,
            "currentPage": 1,
        }

    def get_event(
        self, session: Session, event_id: int, include_deleted: bool = False
    ) -> dict:
        stmt = (
            select(Event)
            .options(
                selectinload(Event.observation_data)
                .selectinload(ObservationCamData.trail_points),
                selectinload(Event.observation_data)
                .selectinload(ObservationCamData.cam)
                .selectinload(Cam.station),
                selectinload(Event.res_entries),
                selectinload(Event.reviews),
            )
            .where(Event.id == event_id, self._base_filter(include_deleted))
        )
        event = session.scalars(stmt).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return serialize_event(
            event,
            include_relationships=True,
            include_deleted=include_deleted,
        )

    def get_event_by_datetimetag(
        self,
        session: Session,
        date_tag: str,
        time_tag: str,
        include_deleted: bool = False,
    ) -> dict:
        datetimetag = f"{date_tag}{time_tag}"
        stmt = (
            select(Event)
            .options(
                selectinload(Event.observation_data)
                .selectinload(ObservationCamData.trail_points),
                selectinload(Event.observation_data)
                .selectinload(ObservationCamData.cam)
                .selectinload(Cam.station),
                selectinload(Event.res_entries),
                selectinload(Event.reviews),
            )
            .where(Event.datetimetag == datetimetag, self._base_filter(include_deleted))
        )
        event = session.scalars(stmt).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return serialize_event(
            event,
            include_relationships=True,
            include_deleted=include_deleted,
        )

    def get_event_res_entries(
        self,
        session: Session,
        event_id: int,
        limit: int = 500,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> dict:
        """Return paginated raw .res rows for one event."""

        event = session.get(Event, event_id)
        if not event or (event.is_deleted and not include_deleted):
            raise HTTPException(status_code=404, detail="Event not found")

        total_items = session.scalar(
            select(func.count())
            .select_from(EventResEntry)
            .where(EventResEntry.event_id == event_id)
        ) or 0
        stmt = (
            select(EventResEntry)
            .where(EventResEntry.event_id == event_id)
            .order_by(EventResEntry.line_no.asc())
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
            "has_ams_coords": bool(getattr(observation, "trail_ams_coords", None)),
            "has_centroid": bool(getattr(observation, "trail_centroid", None)),
            "has_centroid2": bool(getattr(observation, "trail_centroid2", None)),
            "trailPoints": [serialize_trail_point(point) for point in points],
        }

    def review_event(
        self, session: Session, event_id: int, user_id: int, rating: int
    ) -> bool:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        review = session.get(UserReview, (user_id, event_id))
        if not review:
            review = UserReview(user_id=user_id, event_id=event_id)
        review.confirmed = rating
        session.add(review)
        return True

    def update_user_confirmation(
        self, session: Session, event_id: int, classification: Optional[str]
    ) -> Event:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        confirmed = -1
        if classification in {"1", "Positive"}:
            confirmed = 1
        elif classification in {"0", "Negative"}:
            confirmed = 0
        event.user_confirmed = confirmed
        session.add(event)
        return event

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
            count(distinct m.id) as Hendelser,
            count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
            COUNT(DISTINCT CASE WHEN m.track_endheight is not null and m.track_endheight <= {settings.candidate_max_end_height_km} THEN m.id END) Meteorittkandidater
            from station as s
            left outer join cam as c on s.id = c.station_id
            left outer join observation_cam_data as d on c.id = d.cam_id
            left outer join event as m on d.event_id = m.id
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
            count(distinct m.id) as Hendelser,
            count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
            COUNT(DISTINCT CASE WHEN m.track_endheight is not null and m.track_endheight <= {settings.candidate_max_end_height_km} THEN m.id END) Meteorittkandidater
            from station as s
            left outer join cam as c on s.id = c.station_id
            left outer join observation_cam_data as d on c.id = d.cam_id
            left outer join event as m on d.event_id = m.id
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
            count(distinct m.id) as Hendelser,
            count(distinct case when m.track_startheight is not null then m.id end) Krysspeilede,
            COUNT(DISTINCT CASE WHEN m.track_endheight is not null and m.track_endheight <= {settings.candidate_max_end_height_km} THEN m.id END) Meteorittkandidater
            from station as s
            left outer join cam as c on s.id = c.station_id
            left outer join observation_cam_data as d on c.id = d.cam_id
            left outer join event as m on d.event_id = m.id
            """
        elif report_name == "coordinates":
            return self.get_coordinate_insight(session)
        else:
            raise HTTPException(status_code=404, detail="Unknown insight report")

        records = session.execute(text(sql)).mappings().all()
        if report_name == "total" and records:
            return [dict(records[0])]
        return [dict(row) for row in records]

    def get_filter_options(
        self, session: Session, include_deleted: bool = False
    ) -> dict:
        years_query = (
            select(func.extract("year", Event.date))
            .where(self._base_filter(include_deleted), Event.date.isnot(None))
            .distinct()
            .order_by(func.extract("year", Event.date).desc())
        )
        station_query = (
            select(Station.station_name)
            .join(Cam, Cam.station_id == Station.id)
            .join(ObservationCamData, ObservationCamData.cam_id == Cam.id)
            .join(Event, ObservationCamData.event_id == Event.id)
            .where(self._base_filter(include_deleted))
            .distinct()
            .order_by(Station.station_name.asc())
        )
        type_query = (
            select(self._event_type_case().label("event_type"))
            .where(self._base_filter(include_deleted))
            .distinct()
        )
        years = [str(int(year)) for year in session.scalars(years_query).all() if year]
        stations = session.scalars(station_query).all()
        event_types = sorted(session.scalars(type_query).all())
        return {
            "years": years,
            "stations": stations,
            "eventTypes": event_types,
        }

    def explore(
        self,
        session: Session,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        stations: Optional[List[str]] = None,
        cross_station_confirmed: Optional[bool] = None,
        candidate_only: bool = False,
        include_deleted: bool = False,
    ) -> dict:
        stmt = self._filtered_events_stmt(
            include_deleted=include_deleted,
            from_date=from_date,
            to_date=to_date,
            stations=stations,
            cross_station_confirmed=cross_station_confirmed,
        ).order_by(Event.date.desc())
        events = session.scalars(stmt).unique().all()
        serialised = [serialize_event(event, include_relationships=True) for event in events]
        if candidate_only:
            serialised = [
                event_payload
                for event_payload in serialised
                if event_payload["candidate"]["is_candidate"]
            ]

        kpi = {
            "total_events": len(serialised),
            "cross_station_confirmed": sum(
                1 for event_payload in serialised if event_payload["cross_station_confirmed"]
            ),
            "candidates": sum(
                1 for event_payload in serialised if event_payload["candidate"]["is_candidate"]
            ),
            "stations": sorted(
                {
                    station
                    for event_payload in serialised
                    for station in event_payload["station_summary"]["stations"]
                }
            ),
        }
        return {
            "filters": {
                "from_date": from_date,
                "to_date": to_date,
                "stations": stations or [],
                "cross_station_confirmed": cross_station_confirmed,
                "candidate": candidate_only,
            },
            "candidate_settings": {
                "max_end_height_km": settings.candidate_max_end_height_km,
                "max_speed_kms": settings.candidate_max_speed_kms,
            },
            "kpi": kpi,
            "events": [
                {
                    "id": event_payload["id"],
                    "event_path": event_payload["event_path"],
                    "title": event_payload["title"],
                    "times": event_payload["times"],
                    "location": event_payload["location"],
                    "cross_station_confirmed": event_payload["cross_station_confirmed"],
                    "candidate": event_payload["candidate"],
                    "shower": event_payload["shower"],
                    "ai_score": event_payload["ai_score"],
                    "technical_validity": event_payload["technical_validity"],
                    "station_summary": event_payload["station_summary"],
                    "preview": event_payload["preview"],
                    "radiant": {
                        "ra": event_payload["radiant_ra"],
                        "dec": event_payload["radiant_dec"],
                    },
                    "ground": {
                        "lat": event_payload["track_endlat"],
                        "lng": event_payload["track_endlong"],
                        "slat": event_payload["track_startlat"],
                        "slng": event_payload["track_startlong"],
                    },
                    "final_classification": event_payload["final_classification"],
                }
                for event_payload in serialised
            ],
        }

    def explore_csv(
        self,
        session: Session,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        stations: Optional[List[str]] = None,
        cross_station_confirmed: Optional[bool] = None,
        candidate_only: bool = False,
        include_deleted: bool = False,
    ) -> str:
        payload = self.explore(
            session,
            from_date=from_date,
            to_date=to_date,
            stations=stations,
            cross_station_confirmed=cross_station_confirmed,
            candidate_only=candidate_only,
            include_deleted=include_deleted,
        )
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "id",
                "event_path",
                "title",
                "utc_time",
                "local_time",
                "location",
                "cross_station_confirmed",
                "is_candidate",
                "max_end_height_km",
                "max_speed_kms",
                "station_count",
                "observation_count",
                "shower",
                "ra",
                "dec",
                "lat",
                "lng",
                "final_classification",
            ],
        )
        writer.writeheader()
        for event_payload in payload["events"]:
            writer.writerow(
                {
                    "id": event_payload["id"],
                    "event_path": event_payload["event_path"],
                    "title": event_payload["title"],
                    "utc_time": event_payload["times"]["utc"],
                    "local_time": event_payload["times"]["local"],
                    "location": event_payload["location"],
                    "cross_station_confirmed": event_payload["cross_station_confirmed"],
                    "is_candidate": event_payload["candidate"]["is_candidate"],
                    "max_end_height_km": event_payload["candidate"]["max_end_height_km"],
                    "max_speed_kms": event_payload["candidate"]["max_speed_kms"],
                    "station_count": event_payload["station_summary"]["station_count"],
                    "observation_count": event_payload["station_summary"]["observation_count"],
                    "shower": event_payload["shower"],
                    "ra": event_payload["radiant"]["ra"],
                    "dec": event_payload["radiant"]["dec"],
                    "lat": event_payload["ground"]["lat"],
                    "lng": event_payload["ground"]["lng"],
                    "final_classification": event_payload["final_classification"],
                }
            )
        return buffer.getvalue()

    def _parse_iso_date(self, raw_value: str, inclusive_end: bool = False) -> datetime:
        try:
            parsed = datetime.fromisoformat(raw_value)
        except ValueError as exc:
            try:
                parsed = datetime.strptime(raw_value, "%Y-%m-%d")
            except ValueError as inner_exc:
                raise HTTPException(status_code=400, detail=f"Invalid date: {raw_value}") from inner_exc
        if inclusive_end and parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0:
            parsed = parsed.replace(hour=23, minute=59, second=59)
        return parsed

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
        seen_event_tags: set[str] = set()
        seen_observation_keys: set[str] = set()
        for record in records:
            event_obj = self._upsert_event(session, record, import_started_at)
            self._replace_res_entries(session, event_obj.id, record)
            processed += 1
            seen_event_tags.add(event_obj.datetimetag)
            for observation in record.observations:
                station_id = self._get_station_id(session, observation, station_cache)
                cam_id = self._get_cam_id(session, observation, station_id, cam_cache)
                self._upsert_observation(
                    session,
                    event_obj.id,
                    cam_id,
                    observation,
                    import_started_at,
                )
                seen_observation_keys.add(observation.observation_key)
        self._mark_missing_events_deleted(
            session,
            mapper.date_strings,
            seen_event_tags,
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

    def _upsert_event(
        self,
        session: Session,
        record: EventRecord,
        import_started_at: datetime,
    ) -> Event:
        datetimetag = record.event.get("datetimetag")
        stmt = select(Event).where(Event.datetimetag == datetimetag)
        event = session.scalars(stmt).first()
        event_columns = {column.name: column for column in Event.__table__.columns}

        payload = {
            key: self._coerce_column_value(event_columns[key], value)
            for key, value in record.event.items()
            if key in event_columns
        }
        if event:
            self._sync_import_columns(
                event,
                event_columns,
                payload,
                self.EVENT_IMPORT_PRESERVED_COLUMNS,
            )
        else:
            event = Event(**payload)
            event.first_seen_at = import_started_at
        event.last_seen_at = import_started_at
        event.deleted_at = None
        event.is_deleted = False
        event.deletion_reason = None
        session.add(event)
        session.flush()
        return event

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
        event_id: int,
        cam_id: int,
        observation: ObservationRecord,
        import_started_at: datetime,
    ) -> None:
        """Upsert by stable observation key so regrouped events do not duplicate data."""

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
        payload["event_id"] = event_id
        payload["cam_id"] = cam_id
        payload["observation_key"] = observation.observation_key
        payload["source_hash"] = observation.source_hash
        payload["event_start_utc"] = observation.event_start_utc

        if existing:
            self._sync_import_columns(
                existing,
                columns,
                payload,
                self.OBSERVATION_IMPORT_PRESERVED_COLUMNS,
            )
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

    def _mark_missing_events_deleted(
        self,
        session: Session,
        imported_dates: List[str],
        seen_event_tags: set[str],
        import_started_at: datetime,
    ) -> None:
        """Soft-delete events in the imported date window that were not seen this run."""

        if not imported_dates:
            return

        stmt = select(Event).where(func.substr(Event.datetimetag, 1, 8).in_(imported_dates))
        if seen_event_tags:
            stmt = stmt.where(Event.datetimetag.not_in(seen_event_tags))
        missing = session.scalars(stmt).all()
        for event in missing:
            event.is_deleted = True
            event.deleted_at = import_started_at
            event.deletion_reason = self.MISSING_FROM_IMPORT
            session.add(event)

    def _mark_missing_observations_deleted(
        self,
        session: Session,
        imported_dates: List[str],
        seen_observation_keys: set[str],
        import_started_at: datetime,
    ) -> None:
        """Soft-delete observations linked to imported-date events when they disappear."""

        if not imported_dates:
            return

        stmt = (
            select(ObservationCamData)
            .join(Event, ObservationCamData.event_id == Event.id)
            .where(func.substr(Event.datetimetag, 1, 8).in_(imported_dates))
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
        event_id: int,
        record: EventRecord,
    ) -> None:
        """Replace all persisted .res rows for one event during reload."""

        session.execute(
            delete(EventResEntry).where(EventResEntry.event_id == event_id)
        )
        if not record.res_entries:
            return
        session.add_all(
            [
                EventResEntry(
                    event_id=event_id,
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
                    event_timestamp_us=point.event_timestamp_us,
                    coord_long=point.coord_long,
                    coord_lat=point.coord_lat,
                    ams_coord_long=point.ams_coord_long,
                    ams_coord_lat=point.ams_coord_lat,
                    centroid_coord_long=point.centroid_coord_long,
                    centroid_coord_lat=point.centroid_coord_lat,
                    centroid2_coord_long=point.centroid2_coord_long,
                    centroid2_coord_lat=point.centroid2_coord_lat,
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

    def _sync_import_columns(self, target, columns, payload, preserved_columns: set[str]) -> None:
        """Keep source-derived columns in sync, clearing values that disappeared on reimport."""

        for key in columns:
            if key in preserved_columns:
                continue
            setattr(target, key, payload.get(key))

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
