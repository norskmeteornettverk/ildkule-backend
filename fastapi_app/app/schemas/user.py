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
