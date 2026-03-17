from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)


class UserPatch(BaseModel):
    role: Optional[str] = Field(
        default=None,
        description="Admin-managed role value for the account.",
    )
    user_level: Optional[str] = Field(
        default=None,
        description="Admin-managed user level.",
    )
    confirmed: Optional[bool] = Field(
        default=None,
        description="Admin-managed account confirmation flag.",
    )
    tutorial_completed: Optional[bool] = Field(
        default=None,
        description="Admin-managed tutorial completion flag. This can be set both true and false.",
    )


class UserSummary(BaseModel):
    id: int
    username: EmailStr
    role: str
    user_level: Optional[str] = None
    tutorial_completed: bool
    confirmed: bool
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
