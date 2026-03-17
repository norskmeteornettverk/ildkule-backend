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
    message: str = Field(..., description="Human-readable login result message.")
    token: str = Field(
        ...,
        description="JWT access token. This field and `accessToken` currently carry the same token value for compatibility.",
    )
    accessToken: str = Field(
        ...,
        description="Compatibility copy of `token`. Both fields currently contain the same JWT access token.",
    )
    id: int = Field(..., description="Authenticated user id.")
    email: EmailStr = Field(..., description="Authenticated account e-mail.")
    username: EmailStr = Field(
        ...,
        description="Authenticated account identifier as returned by the backend.",
    )
    user_role: str = Field(..., description="Primary role for the authenticated user.")
    roles: List[str] = Field(
        ...,
        description="Role list for compatibility. The current backend returns the same role as `user_role` inside a one-item list.",
    )
    user_level: Optional[str] = Field(
        default=None,
        description="Current user level when one is set.",
    )
    tutorial_completed: bool = Field(
        ...,
        description="Whether the authenticated user has completed the tutorial.",
    )
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
