from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db import get_session
from ..models import User
from ..schemas.user import (
    PasswordChangeRequest,
    TutorialUpdate,
    UserCreate,
    UserListResponse,
    UserPatch,
    UserReviewHistoryResponse,
    TutorialContentResponse,
)
from ..security import enforce_role, get_current_user, verify_password
from ..services.user_service import UserService
from ..utils.serialization import serialize_user

router = APIRouter(tags=["users"])
user_service = UserService()

TUTORIAL_CONTENT = TutorialContentResponse(
    title="Meteorvurderingstutorial",
    intro="Kort veiledning for aa kjenne igjen en mulig ildkule og forstaa hva som er nyttig aa rapportere eller vurdere.",
    sections=[
        {
            "id": "checklist",
            "title": "Sjekkliste for mulig ildkule",
            "bullets": [
                "Beveger seg raskt over himmelen, klart raskere enn et fly.",
                "Beveger seg i rett linje og snur eller svinger ikke.",
                "Lyser sterkere enn klare stjerner eller planeter.",
                "Er ikke synlig foran terreng, traer eller tett skydekke.",
                "Er vanligvis synlig kort tid, ofte 1 til 10 sekunder og sjelden mer enn et halvt minutt.",
            ],
        },
        {
            "id": "other-signs",
            "title": "Andre tegn som kan vaere nyttige",
            "bullets": [
                "Plutselig opplysning av terrenget eller tydelige skygger kan vaere et viktig tegn.",
                "En lysende stripe eller flekk paa himmelen som gradvis blir svakere kan hoere til samme hendelse.",
                "Droenn eller smell kan vaere relevante hvis de ikke passer med torden eller menneskelig aktivitet.",
                "Et droenn etter en ildkule kommer ofte lenge etter lyset, gjerne over ett minutt senere.",
            ],
        },
        {
            "id": "distance",
            "title": "Hvor den ser ut til aa lande",
            "bullets": [
                "Mange opplever at ildkula faller rett bak en aas eller like ved, men den er ofte mye lenger unna.",
                "Ildkuler slokner typisk 20 til 60 kilometer over bakken.",
                "Beskrivelsen av hvor den ser ut til aa lande er fortsatt nyttig, selv om inntrykket av avstand ofte er feil.",
            ],
        },
        {
            "id": "what-is-fireball",
            "title": "Hva en ildkule er",
            "bullets": [
                "Små stein- eller isbiter i solsystemet kalles meteoroider eller mikrometeoroider.",
                "De begynner ofte aa lyse rundt 100 kilometer over bakken og er ofte borte innen de kommer ned til rundt 50 kilometer.",
                "Ildkuler er meteorer som lyser sterkere enn Venus, og spesielt kraftige hendelser kalles ofte bolider.",
                "Noen rester kan overleve helt ned til bakken og kalles da meteoritter.",
            ],
        },
        {
            "id": "strong-fireballs",
            "title": "Kraftige ildkuler og varighet",
            "bullets": [
                "Svaert kraftige ildkuler kan lyse helt ned til 20 til 30 kilometer over bakken.",
                "De kan gi overlydssmell og i noen tilfeller etterlate meteoritter paa bakken.",
                "De fleste ildkuler lyser i noen faa sekunder, men noen kan vare over 10 sekunder ved lav innfallsvinkel.",
                "Meteorer kan ogsaa observeres om dagen, men da maa de vanligvis vaere ekstra kraftige.",
            ],
        },
        {
            "id": "quality-and-level",
            "title": "Hvorfor tutorialen betyr noe",
            "bullets": [
                "Gjennomgaatt tutorial kan loefte brukernivaaet fra 0 til 1.",
                "Tutorialen er del av kvalitetssystemet, ikke bare onboarding.",
                "Frontend-modalen har ogsaa bilder, eksempelvideoer og en publiseringsfot som ikke ennaa er egne felter i API-responsen.",
            ],
        },
    ],
)


@router.post(
    "/users",
    status_code=201,
    summary="Create user",
    description="Creates a new user account.",
)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    user = user_service.create_user(session, payload.identifier, payload.password)
    return serialize_user(user)


@router.get(
    "/users/{user_id}",
    summary="Get user",
    description="Returns account fields for one authenticated user. This is not a public profile endpoint.",
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


@router.patch(
    "/users/{user_id}",
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
    response_model=TutorialContentResponse,
    summary="Get tutorial content",
    description="Returns the current tutorial content used for the review guide. The runtime keeps tutorial content and tutorial status as separate API surfaces. This API now mirrors the main text sections from the frontend tutorial modal, but does not yet expose the modal's image, example video links, or publication footer as separate fields.",
)
def get_tutorial_content(_: User = Depends(get_current_user)):
    return TUTORIAL_CONTENT


@router.put(
    "/users/{user_id}/tutorial-completion",
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
