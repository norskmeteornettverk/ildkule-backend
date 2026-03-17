from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import admin, auth, forms, logs, events, users

settings = get_settings()

app = FastAPI(
    title="Ildkule API",
    version="2.0.0",
    description=(
        "Public and administrative API for Ildkule. "
        "The current OpenAPI document prioritises the new meteor-event contract, "
        "Utforsk data, ingestion, users, and public forms."
    ),
    openapi_tags=[
        {"name": "events", "description": "Meteor-event list, meteor-event detail, raw event supplements, and Utforsk endpoints."},
        {"name": "forms", "description": "Public contact and observation-reporting endpoints."},
        {"name": "auth", "description": "Authentication and password reset endpoints."},
        {"name": "users", "description": "Account creation, account reads, and administrative user management."},
        {"name": "station logs", "description": "Station log intake and read endpoints."},
        {"name": "admin", "description": "Administrative ingestion endpoints."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_directory = settings.data_directory
if data_directory:
    data_path = Path(data_directory)
    if data_path.exists() and data_path.is_dir():
        app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(forms.router, prefix="/api/forms")
app.include_router(logs.router, prefix="/api")
app.include_router(admin.router, prefix="/api/admin")
