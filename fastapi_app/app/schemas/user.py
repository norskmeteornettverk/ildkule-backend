from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, root_validator


class UserCreate(BaseModel):
    identifier: EmailStr = Field(
        ...,
        description="Account identifier for the new user. The current runtime stores this as the user's e-mail based identifier.",
    )
    password: str = Field(min_length=8)

    @root_validator(pre=True)
    def _accept_legacy_username(cls, values):
        if "identifier" not in values and "username" in values:
            values["identifier"] = values["username"]
        return values


class UserPatch(BaseModel):
    role: Optional[str] = Field(
        default=None,
        description="Admin-managed role value for the account.",
    )
    user_level: Optional[str] = Field(
        default=None,
        description="Admin-managed user level.",
    )
    account_confirmed: Optional[bool] = Field(
        default=None,
        description="Admin-managed account confirmation flag.",
    )
    tutorial_completed: Optional[bool] = Field(
        default=None,
        description="Admin-managed tutorial completion flag. This can be set both true and false.",
    )


class UserSummary(BaseModel):
    id: int
    identifier: EmailStr = Field(
        ...,
        description="Public account identifier for the user.",
    )
    role: str
    user_level: Optional[str] = None
    tutorial_completed: bool
    account_confirmed: bool
    ratings: int = 0
    positive_ratings: int = 0
    negative_ratings: int = 0

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    message: str
    users: List[UserSummary]


class TutorialUpdate(BaseModel):
    completed: bool = Field(
        ...,
        description="Tutorial completion state for the user. Set true to mark it completed, or false to clear the completed state.",
    )


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserReviewHistoryItem(BaseModel):
    event_id: int = Field(..., description="Reviewed event id.")
    event_path: Optional[str] = Field(
        default=None,
        description="Event path in `YYYYMMDD/HHMMSS` form when available.",
    )
    location: Optional[str] = Field(
        default=None,
        description="Event location text when available.",
    )
    confirmed: Optional[int] = Field(
        default=None,
        description="Stored review value. Current runtime uses 1 for yes, 0 for no, and -1 or null for unclear or reset values.",
    )
    review_label: str = Field(
        ...,
        description="Human-readable review label for the stored value.",
    )


class UserReviewHistoryResponse(BaseModel):
    message: str
    reviews: List[UserReviewHistoryItem]


class TutorialMetadataResponse(BaseModel):
    version: str = Field(
        ...,
        description="Current tutorial version identifier owned by the backend.",
    )
    content_owner: str = Field(
        ...,
        description="Which layer owns the tutorial text and translations. The current runtime uses `frontend`.",
    )
    delivery_surface: str = Field(
        ...,
        description="How tutorial content is delivered. The current runtime uses `frontend_i18n` because text and language handling live in the frontend.",
    )
    status_field: str = Field(
        ...,
        description="User field that stores tutorial completion status.",
    )
    completion_route: str = Field(
        ...,
        description="Route used to update tutorial completion status.",
    )
    minimum_level_after_completion: int = Field(
        ...,
        description="Minimum user level reached when tutorial completion lifts the account from level 0.",
    )
