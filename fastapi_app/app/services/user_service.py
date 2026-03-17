from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Event, User, UserReview
from ..security import get_password_hash, verify_password
from ..utils.emailer import send_mail

settings = get_settings()


class UserService:
    def _verification_target(self, token: str) -> str:
        if settings.front_url:
            return f"{settings.front_url.rstrip('/')}/brukerprofil/verifiser?token={token}"
        return token

    def _send_verification_mail(self, email: str, token: str) -> None:
        verification_target = self._verification_target(token)
        subject = "Bekreft brukerkontoen din hos ildkule.net"
        body = (
            "Hei!<br/>Du kan bekrefte brukerkontoen din hos ildkule.net ved å bruke lenken under."
            f"<br/><a href=\"{verification_target}\">Bekreft kontoen</a>"
            "<br/><br/>Hvis du ikke ventet denne e-posten, kan du se bort fra den."
        )
        send_mail(email, subject, body, body)

    def create_user(self, session: Session, username: str, password: str) -> User:
        existing = session.scalar(
            select(User).where(func.lower(User.username) == username.lower())
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        user = User(
            username=username,
            password=get_password_hash(password),
            confirm_token=secrets.token_hex(20),
        )
        session.add(user)
        session.flush()
        if user.confirm_token:
            self._send_verification_mail(user.username, user.confirm_token)
        return user

    def authenticate(
        self, session: Session, username: str, password: str
    ) -> Optional[User]:
        user = session.scalar(
            select(User).where(func.lower(User.username) == username.lower())
        )
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    def tutorial_performed(
        self, session: Session, user_id: int, tutorial_complete: bool
    ) -> User:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.tutorial_completed = tutorial_complete
        if not user.user_level or int(user.user_level) == 0:
            user.user_level = "1"
        session.add(user)
        return user

    def list_users(
        self,
        session: Session,
        limit: int,
        offset: int,
        order_by: str,
        order: str,
    ) -> List[Tuple[User, dict]]:
        ratings_subquery = (
            select(
                UserReview.user_id.label("user_id"),
                func.sum(case((UserReview.confirmed == 1, 1), else_=0)).label(
                    "positive_ratings"
                ),
                func.sum(case((UserReview.confirmed == 0, 1), else_=0)).label(
                    "negative_ratings"
                ),
                func.count().label("ratings"),
            )
            .group_by(UserReview.user_id)
            .subquery()
        )

        sortable_columns = {
            "username": User.username,
            "role": User.role,
            "user_level": User.user_level,
            "tutorial_completed": User.tutorial_completed,
            "confirmed": User.confirmed,
            "ratings": ratings_subquery.c.ratings,
            "create_time": User.create_time,
        }
        column = sortable_columns.get(order_by, User.create_time)
        direction = column.desc() if order.lower() == "desc" else column.asc()

        stmt = (
            select(
                User,
                ratings_subquery.c.ratings,
                ratings_subquery.c.positive_ratings,
                ratings_subquery.c.negative_ratings,
            )
            .outerjoin(ratings_subquery, User.id == ratings_subquery.c.user_id)
            .order_by(direction)
            .limit(limit)
            .offset(offset)
        )
        results = session.execute(stmt).all()
        formatted: List[Tuple[User, dict]] = []
        for user, ratings, positive_ratings, negative_ratings in results:
            formatted.append(
                (
                    user,
                    {
                        "ratings": ratings or 0,
                        "positive_ratings": positive_ratings or 0,
                        "negative_ratings": negative_ratings or 0,
                    },
                )
            )
        return formatted

    def list_user_reviews(self, session: Session, user_id: int) -> list[dict]:
        stmt = (
            select(UserReview, Event)
            .join(Event, UserReview.event_id == Event.id)
            .where(UserReview.user_id == user_id)
            .order_by(Event.date.desc().nullslast(), UserReview.event_id.desc())
        )
        rows = session.execute(stmt).all()
        reviews: list[dict] = []
        for review, event in rows:
            event_path = (
                f"{event.datetimetag[:8]}/{event.datetimetag[8:]}"
                if event and event.datetimetag
                else None
            )
            reviews.append(
                {
                    "event_id": review.event_id,
                    "event_path": event_path,
                    "location": event.location if event else None,
                    "confirmed": review.confirmed,
                    "review_label": (
                        "Ja"
                        if review.confirmed == 1
                        else "Nei"
                        if review.confirmed == 0
                        else "Usikker"
                    ),
                }
            )
        return reviews

    def request_password_reset(self, session: Session, email: str) -> bool:
        user = session.scalar(
            select(User).where(func.lower(User.username) == email.lower())
        )
        if not user:
            return False
        user.password_reset_token = secrets.token_hex(20)
        user.password_reset_request_time = datetime.utcnow()
        session.add(user)

        if settings.front_url:
            reset_url = f"{settings.front_url.rstrip('/')}/brukerprofil/nullstillpassord?passwordResetId={user.password_reset_token}"
        else:
            reset_url = user.password_reset_token
        subject = "Forespørsel om nullstilling av passord"
        body = (
            "Hei!<br/>Vi har mottatt forespørsel om å resette ditt passord på ildkule.net."
            "<br/>Om du ikke har gjort dette, kan du se bort fra denne e-posten."
            f"<br/>Om du vil resette passordet, <a href=\"{reset_url}\">klikker du her</a>."
            "<br/><br/>Hilsen ildkule.net"
        )
        send_mail(email, subject, body, body)
        return True

    def resend_verification(self, session: Session, email: str) -> bool:
        user = session.scalar(
            select(User).where(func.lower(User.username) == email.lower())
        )
        if not user:
            return False
        if user.confirmed:
            return True
        user.confirm_token = secrets.token_hex(20)
        session.add(user)
        self._send_verification_mail(email, user.confirm_token)
        return True

    def confirm_user(self, session: Session, token: str) -> Optional[User]:
        user = session.scalar(select(User).where(User.confirm_token == token))
        if not user:
            return None
        user.confirmed = True
        user.confirm_token = None
        session.add(user)
        return user

    def reset_password(
        self, session: Session, email: str, token: str, new_password: str
    ) -> bool:
        user = session.scalar(
            select(User).where(func.lower(User.username) == email.lower())
        )
        if not user or not user.password_reset_token:
            return False
        if secrets.compare_digest(user.password_reset_token, token):
            user.password = get_password_hash(new_password)
            user.password_reset_token = None
            user.password_reset_request_time = None
            session.add(user)
            return True
        return False

    def patch_user(self, session: Session, payload: dict) -> User:
        user = session.get(User, payload["id"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if "role" in payload and payload["role"]:
            user.role = payload["role"]
        if "user_level" in payload and payload["user_level"] is not None:
            user.user_level = str(payload["user_level"])
        if "confirmed" in payload and payload["confirmed"] is not None:
            user.confirmed = bool(payload["confirmed"])
        if (
            "tutorial_completed" in payload
            and payload["tutorial_completed"] is not None
        ):
            user.tutorial_completed = bool(payload["tutorial_completed"])
        session.add(user)
        return user

    def update_password(
        self, session: Session, user: User, new_password: str
    ) -> User:
        user.password = get_password_hash(new_password)
        session.add(user)
        return user
