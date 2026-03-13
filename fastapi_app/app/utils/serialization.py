from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import inspect
from sqlalchemy.orm.attributes import NO_VALUE

from ..models import (
    Cam,
    Meteor,
    MeteorResEntry,
    ObservationCamData,
    ObservationTrailPoint,
    Station,
    User,
    UserReview,
)


def model_to_dict(instance, exclude: Optional[set[str]] = None) -> dict:
    if instance is None:
        return {}
    exclude = exclude or set()
    mapper = inspect(instance).mapper.column_attrs
    payload = {}
    for column in mapper:
        key = column.key
        if key in exclude:
            continue
        payload[key] = getattr(instance, key)
    return payload


def serialize_user(user: User, ratings: Optional[dict] = None) -> dict:
    payload = model_to_dict(
        user, exclude={"password", "confirm_token", "password_reset_token"}
    )
    payload["user_role"] = payload.get("role")
    payload["roles"] = [payload.get("role")]
    payload["id"] = user.id
    payload["username"] = user.username
    payload["tutorial_completed"] = bool(payload.get("tutorial_completed"))
    payload["confirmed"] = bool(payload.get("confirmed"))
    payload["user_level"] = payload.get("user_level")
    if ratings:
        payload.update(ratings)
    return payload


def serialize_review(review: UserReview) -> dict:
    return model_to_dict(review)


def serialize_cam(cam: Cam) -> dict:
    payload = model_to_dict(cam)
    if cam.station:
        payload["station"] = model_to_dict(cam.station)
    return payload


def serialize_observation(record: ObservationCamData) -> dict:
    payload = model_to_dict(record)
    trail_points_state = inspect(record).attrs.trail_points.loaded_value
    if trail_points_state is not NO_VALUE:
        payload["trail_point_count"] = len(trail_points_state or [])
    if record.cam:
        payload["cam"] = serialize_cam(record.cam)
    return payload


def serialize_res_entry(entry: MeteorResEntry) -> dict:
    return model_to_dict(entry)


def serialize_trail_point(point: ObservationTrailPoint) -> dict:
    return model_to_dict(point)


def serialize_meteor(
    meteor: Meteor,
    include_relationships: bool = False,
    include_deleted: bool = False,
) -> dict:
    payload = model_to_dict(meteor)
    res_entries_state = inspect(meteor).attrs.res_entries.loaded_value
    if res_entries_state is not NO_VALUE:
        payload["res_entry_count"] = len(res_entries_state or [])
    if include_relationships:
        observations = meteor.observation_data or []
        if not include_deleted:
            observations = [record for record in observations if not record.is_deleted]
        payload["observation_cam_data"] = [
            serialize_observation(record) for record in observations
        ]
        payload["user_review"] = [
            serialize_review(review) for review in meteor.reviews or []
        ]
    return payload


def serialize_meteor_list(
    meteors: Iterable[Meteor],
    include_relationships: bool = False,
    include_deleted: bool = False,
) -> List[dict]:
    return [
        serialize_meteor(
            meteor,
            include_relationships=include_relationships,
            include_deleted=include_deleted,
        )
        for meteor in meteors
    ]
