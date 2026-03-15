from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import admin, auth, forms, logs, events, users

settings = get_settings()

app = FastAPI(title="Ildkule API", version="2.0.0")

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

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(forms.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
