from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import admin, auth, forms, logs, meteors, users

settings = get_settings()

app = FastAPI(title="Ildkule API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(meteors.router, prefix="/api")
app.include_router(forms.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
