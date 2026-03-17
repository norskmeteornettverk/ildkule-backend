from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: EmailStr = Field(
        ...,
        description="Compatibility login field. The current field name is username, but it is intended to accept the account identifier used for login.",
    )
    password: str


class TokenResponse(BaseModel):
    message: str
    token: str
    accessToken: str
    id: int
    email: EmailStr
    username: EmailStr
    user_role: str
    roles: List[str]
    user_level: Optional[str]
    tutorial_completed: bool
    confirmed: bool = Field(
        ...,
        description="Account confirmation status for the authenticated user.",
    )


class PasswordResetEmailRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmation(BaseModel):
    passwordResetId: str = Field(..., alias="passwordResetId")
    email: EmailStr
    password: str


class PasswordResetResponse(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
