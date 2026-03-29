import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import check_database_connection
from .routers import admin, auth, events, forms, logs, users
from .utils.logging_utils import configure_logging

settings = get_settings()
logger = configure_logging(
    settings.app_log_level,
    settings.app_log_file,
    disable_file_logging=settings.disable_file_logging,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        check_database_connection()
    except Exception as exc:
        logger.exception("Database startup check failed")
        raise RuntimeError("Database startup check failed") from exc

    logger.info("Database startup check passed")
    yield


def create_app() -> FastAPI:
    configure_logging(
        settings.app_log_level,
        settings.app_log_file,
        disable_file_logging=settings.disable_file_logging,
    )

    app = FastAPI(
        title="Ildkule API",
        version="2.0.0",
        description=(
            "Public and administrative API for Ildkule. "
            "The current OpenAPI document prioritises the new meteor-event contract, "
            "event filters, insight reports, ingestion, users, and public forms."
        ),
        openapi_tags=[
            {"name": "events", "description": "Meteor-event list, meteor-event detail, raw event supplements, and event filter endpoints."},
            {"name": "forms", "description": "Public contact and observation-reporting endpoints."},
            {"name": "auth", "description": "Authentication, verification, and password reset endpoints."},
            {"name": "users", "description": "Account creation, account reads, tutorial metadata and status, review history, and administrative user management."},
            {"name": "station logs", "description": "Station log intake, raw log reads, and aggregated station-network status endpoints."},
            {"name": "admin", "description": "Administrative ingestion endpoints."},
        ],
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started_at = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id

        log_method = logger.info
        if response.status_code >= 500:
            log_method = logger.error
        elif response.status_code >= 400:
            log_method = logger.warning

        log_method(
            "%s %s -> %s in %.2f ms [request_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "Unhandled application exception for %s %s [request_id=%s]",
            request.method,
            request.url.path,
            request_id,
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )

    data_directory = settings.data_directory
    if settings.event_media_source_mode == "local" and data_directory:
        data_path = Path(data_directory)
        if data_path.exists() and data_path.is_dir():
            app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(users.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(forms.router, prefix="/api/forms")
    app.include_router(logs.router, prefix="/api")
    app.include_router(admin.router, prefix="/api/admin")

    return app


app = create_app()
