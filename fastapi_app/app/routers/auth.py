from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas.auth import (
    LoginRequest,
    PasswordResetConfirmation,
    PasswordResetEmailRequest,
    TokenResponse,
)
from ..security import create_access_token
from ..services.user_service import UserService

router = APIRouter(tags=["auth"])
user_service = UserService()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Authenticates a user and returns a JWT plus basic account data.",
    response_description="Authenticated session payload.",
)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = user_service.authenticate(session, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Feil brukernavn eller passord",
        )
    token_payload = {
        "username": user.username,
        "user_id": user.id,
        "role": user.role,
        "user_level": user.user_level,
    }
    jwt_token = create_access_token(token_payload)
    return TokenResponse(
        message="Innlogging utført",
        token=jwt_token,
        accessToken=jwt_token,
        id=user.id,
        email=user.username,
        username=user.username,
        user_role=user.role,
        roles=[user.role],
        user_level=user.user_level,
        tutorial_completed=bool(user.tutorial_completed),
        confirmed=bool(user.confirmed),
    )


@router.post(
    "/passwordresetrequest",
    summary="Request password reset",
    description="Starts the password-reset flow for the supplied e-mail address.",
)
def request_reset(
    payload: PasswordResetEmailRequest, session: Session = Depends(get_session)
):
    user_service.request_password_reset(session, payload.email)
    return {"message": "Passordreset sendt dersom brukeren finnes"}


@router.put(
    "/passwordresetrequest",
    summary="Confirm password reset",
    description="Completes the password-reset flow with token, e-mail, and new password.",
)
def confirm_reset(
    payload: PasswordResetConfirmation, session: Session = Depends(get_session)
):
    success = user_service.reset_password(
        session, payload.email, payload.passwordResetId, payload.password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kunne ikke oppdatere passordet",
        )
    return {"message": "Passordet ble endret"}
