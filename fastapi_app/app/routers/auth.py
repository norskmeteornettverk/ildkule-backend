from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..schemas.common import MessageResponse
from ..schemas.auth import (
    LoginRequest,
    PasswordResetConfirmation,
    PasswordResetEmailRequest,
    TokenResponse,
    VerificationConfirmationResponse,
    VerificationResendRequest,
    VerificationResendResponse,
)
from ..security import create_access_token
from ..services.user_service import UserService

router = APIRouter(tags=["auth"])
user_service = UserService()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description=(
        "Authenticates a user and returns a JWT plus basic account data. "
        "The current runtime returns the token in the response body and expects clients to send it back in "
        "`Authorization: Bearer <token>` on protected routes. "
        "The current runtime does not set an HTTP-only session cookie and does not expose a refresh-token endpoint. "
        "Account verification is handled by the dedicated verification routes in this auth group."
    ),
    response_description="Authenticated session payload.",
)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = user_service.authenticate(session, payload.identifier, payload.password)
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
        identifier=user.username,
        user_role=user.role,
        roles=[user.role],
        user_level=user.user_level,
        tutorial_completed=bool(user.tutorial_completed),
        account_confirmed=bool(user.confirmed),
    )


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Starts the password-reset flow for the supplied e-mail address.",
)
def request_reset(
    payload: PasswordResetEmailRequest, session: Session = Depends(get_session)
):
    user_service.request_password_reset(session, payload.email)
    return {"message": "Passordreset sendt dersom brukeren finnes"}


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
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


@router.get(
    "/verification/confirm",
    response_model=VerificationConfirmationResponse,
    summary="Confirm account verification",
    description="Confirms one user account from the verification token sent by e-mail. Invalid or stale tokens return 401.",
)
def confirm_verification(token: str, session: Session = Depends(get_session)):
    user = user_service.confirm_user(session, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kunne ikke bekrefte kontoen",
        )
    return VerificationConfirmationResponse(
        message="Kontoen er bekreftet",
        account_confirmed=True,
    )


@router.post(
    "/verification/resend",
    response_model=VerificationResendResponse,
    summary="Resend account verification",
    description="Requests a new verification link for an unconfirmed account. The response is intentionally neutral when the account does not exist.",
)
def resend_verification(
    payload: VerificationResendRequest,
    session: Session = Depends(get_session),
):
    user_service.resend_verification(session, payload.email)
    return VerificationResendResponse(
        message="Ny verifiseringslenke sendt dersom kontoen finnes og ikke er bekreftet"
    )
