from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.user import PasswordChangeRequest, TutorialUpdate, UserCreate, UserPatch
from ..security import enforce_role, get_current_user, verify_password
from ..services.user_service import UserService
from ..utils.serialization import serialize_user

router = APIRouter(tags=["users"])
user_service = UserService()


@router.post(
    "/user",
    status_code=201,
    summary="Create user",
    description="Creates a new user account.",
)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    user = user_service.create_user(session, payload.username, payload.password)
    return serialize_user(user)


@router.get(
    "/user/{user_id}",
    summary="Get user",
    description="Returns public account fields for one user.",
)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user)


@router.get(
    "/user/{user_id}/details",
    summary="Get user details",
    description="Returns account fields for one user. Currently the same shape as /user/{user_id}.",
)
def get_user_details(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user)


@router.patch("/user/{user_id}")
def patch_user(
    user_id: int,
    payload: UserPatch,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    if payload.id != user_id:
        raise HTTPException(status_code=400, detail="Payload id mismatch")
    user = user_service.patch_user(session, payload.dict(exclude_unset=True))
    return serialize_user(user)


@router.get(
    "/users",
    summary="List users",
    description="Returns a paginated user list with rating counters.",
)
def list_users(
    page: int = Query(-1),
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


@router.put("/user/{user_id}/tutorialcomplete")
def update_tutorial(
    user_id: int,
    payload: TutorialUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and current_user.role != "ROLE_ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized")
    user = user_service.tutorial_performed(session, user_id, payload.tutorialComplete)
    return serialize_user(user)


@router.put("/user/{user_id}/password")
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


@router.put("/user/{user_id}/userlevel")
def set_user_level(
    user_id: int,
    payload: UserPatch,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.user_level is None:
        raise HTTPException(status_code=400, detail="user_level missing")
    user.user_level = str(payload.user_level)
    session.add(user)
    return serialize_user(user)


@router.put("/user/{user_id}/userrole")
def set_user_role(
    user_id: int,
    payload: UserPatch,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.role:
        raise HTTPException(status_code=400, detail="role missing")
    user.role = payload.role
    session.add(user)
    return serialize_user(user)


@router.put("/user/{user_id}/active")
def set_user_active(
    user_id: int,
    payload: TutorialUpdate,
    session: Session = Depends(get_session),
    __: User = Depends(enforce_role(["ROLE_ADMIN"])),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.confirmed = payload.tutorialComplete
    session.add(user)
    return serialize_user(user)
