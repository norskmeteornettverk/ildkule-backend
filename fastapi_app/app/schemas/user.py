from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)


class UserPatch(BaseModel):
    id: int
    role: Optional[str] = None
    user_level: Optional[str] = None


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
    tutorialComplete: bool


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)

