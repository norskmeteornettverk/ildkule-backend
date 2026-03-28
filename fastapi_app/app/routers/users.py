from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.common import MessageResponse
from ..schemas.user import (
    PasswordChangeRequest,
    TutorialMetadataResponse,
    TutorialUpdate,
    UserLookupResponse,
    UserCreate,
    UserListResponse,
    UserPatch,
    UserReviewHistoryResponse,
)
from ..security import enforce_role, get_current_user, verify_password
from ..services.user_service import UserService
from ..utils.serialization import serialize_user

router = APIRouter(tags=["users"])
user_service = UserService()

TUTORIAL_METADATA = TutorialMetadataResponse(
    version="frontend-modal-2026-03",
    content_owner="frontend",
    delivery_surface="frontend_i18n",
    status_field="tutorial_completed",
    completion_route="/api/users/{user_id}/tutorial-completion",
    minimum_level_after_completion=1,
)


@router.post(
    "/users",
    status_code=201,
    response_model=UserLookupResponse,
    summary="Create user",
    description="Creates a new user account.",
)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    user = user_service.create_user(session, payload.identifier, payload.password)
    return serialize_user(user)


@router.get(
    "/users/{user_id}",
    response_model=UserLookupResponse,
    summary="Get user",
    description="Returns account fields for one authenticated user. This is not a public profile endpoint.",
)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user)


@router.patch(
    "/users/{user_id}",
    response_model=UserLookupResponse,
    summary="Patch user",
    description=(
        "Admin-only partial update for account fields. "
        "Current supported fields are `role`, `user_level`, `account_confirmed`, and `tutorial_completed`. "
        "Regular users should use the dedicated tutorial and password routes for self-service actions."
    ),
)
def patch_user(
    user_id: int,
    payload: UserPatch,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    user = user_service.patch_user(
        session,
        {
            "id": user_id,
            **{
                ("confirmed" if key == "account_confirmed" else key): value
                for key, value in payload.dict(exclude_unset=True).items()
            },
        },
    )
    return serialize_user(user)


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List users",
    description="Returns a user list with rating counters. In current runtime `page=-1` is a compatibility shortcut that behaves like the first page because negative page numbers clamp to offset 0.",
)
def list_users(
    page: int = Query(
        -1,
        description="Page number. The compatibility default `-1` behaves like the first page because negative values clamp to offset 0.",
    ),
    limit: int = Query(20),
    orderby: str = Query("date"),
    order: str = Query("desc"),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    offset = max(page - 1, 0) * limit
    users = user_service.list_users(session, limit, offset, orderby, order)
    payload = [serialize_user(user, ratings=ratings) for user, ratings in users]
    return {"message": "User list created", "users": payload}


@router.get(
    "/users/{user_id}/reviews",
    response_model=UserReviewHistoryResponse,
    summary="Get user review history",
    description="Returns the authenticated user's own event review history. Admins can also read another user's history.",
)
def get_user_reviews(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")
    return {
        "message": "Review history loaded",
        "reviews": user_service.list_user_reviews(session, user_id),
    }


@router.get(
    "/tutorial",
    response_model=TutorialMetadataResponse,
    summary="Get tutorial metadata",
    description="Returns backend-owned tutorial metadata. The current runtime keeps tutorial text, media, and translations in the frontend, while the backend owns completion status and the current tutorial version identifier.",
)
def get_tutorial_content(_: User = Depends(get_current_user)):
    return TUTORIAL_METADATA


@router.put(
    "/users/{user_id}/tutorial-completion",
    response_model=UserLookupResponse,
    summary="Mark tutorial completion",
    description="Marks the user tutorial as completed or not completed. This remains a separate action because it can also lift the user's level from 0 to 1.",
)
def update_tutorial(
    user_id: int,
    payload: TutorialUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")
    user = user_service.tutorial_performed(session, user_id, payload.completed)
    return serialize_user(user)


@router.patch(
    "/users/{user_id}/password",
    response_model=MessageResponse,
    summary="Change user password",
    description="Partially updates the authenticated user's password.",
)
def update_password(
    user_id: int,
    payload: PasswordChangeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )
    user_service.update_password(session, current_user, payload.new_password)
    return {"message": "Passord oppdatert"}
