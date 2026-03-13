# FastAPI version of the ildkule API

The PHP API located in `api/` has been ported to Python using FastAPI.  The new
code lives under `fastapi_app/` and exposes the same HTTP resources
(`/api/login`, `/api/user`, `/api/meteors`, etc.).

## Getting started

1. Create and activate a virtual environment (recommended).
2. Install dependencies:
   ```bash
   pip install -r fastapi_app/requirements.txt
   ```
3. Optional for tests:
   ```bash
   pip install -r fastapi_app/requirements-dev.txt
   ```
4. Copy the sample environment file and adjust the values so they match your
   infrastructure:
   ```bash
   cp fastapi_app/.env.example fastapi_app/.env
   ```
5. Start the API server:
   ```bash
   uvicorn fastapi_app.app.main:app --reload
   ```

The application reads configuration from `fastapi_app/.env` regardless of the
current working directory. At a minimum set
`DATABASE_URL` (MySQL DSN) and `JWT_SECRET_KEY`.  SMTP and reCAPTCHA settings
are optional but required if you want to send contact/report forms.  The station
log endpoint validates a bearer token configured via `STATION_LOG_TOKEN`.

## Notes

- `/api/meteorload` now uses the Python port of the legacy file mapper to
  ingest meteor observations directly from the data directory configured via
  `DATA_DIRECTORY`.
- `PyMySQL` needs `cryptography` when MySQL uses `caching_sha2_password`, so it
  is included in `requirements.txt`.
- All other endpoints are available in FastAPI and return the same payloads that
  the PHP version exposed, including JWT payload structure and pagination data.
- Automated tests live in `fastapi_app/tests/` (run with `pytest -q` after
  installing `requirements-dev.txt`).
