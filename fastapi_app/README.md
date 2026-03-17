# FastAPI version of the ildkule API

The PHP API located in `api/` has been ported to Python using FastAPI. The new
code lives under `fastapi_app/` and exposes the active route structure
(`/api/auth/login`, `/api/users`, `/api/events`, etc.).

## Getting started

1. Use a local virtual environment for this project. Do not rely on global Python packages.
   Example:
   ```bash
   python -m venv .venv
   ```
2. Activate the virtual environment.
   Example on Windows PowerShell:
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies with the same Python interpreter that owns the virtual environment:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r fastapi_app/requirements.txt
   ```
4. Optional for tests:
   ```bash
   python -m pip install -r fastapi_app/requirements-dev.txt
   ```
5. Copy the sample environment file and adjust the values so they match your
   infrastructure:
   ```bash
   cp fastapi_app/.env.example fastapi_app/.env
   ```
6. Start the API server with the same Python interpreter:
   ```bash
   python -m uvicorn fastapi_app.app.main:app --reload
   ```

The application reads configuration from `fastapi_app/.env` regardless of the
current working directory. At a minimum set
`DATABASE_URL` (MySQL DSN) and `JWT_SECRET_KEY`.  SMTP and reCAPTCHA settings
are optional but required if you want to send contact/report forms.  The station
log endpoint validates a bearer token configured via `STATION_LOG_TOKEN`.

If startup fails with import or dependency errors, first check that the virtual
environment is active and that the packages were installed inside that
environment. A mixed global/local Python setup can load the wrong package
versions.

## Notes

- `/api/admin/event-imports` now uses the Python port of the legacy file mapper to
  ingest meteor observations directly from the data directory configured via
  `DATA_DIRECTORY`.
- `PyMySQL` needs `cryptography` when MySQL uses `caching_sha2_password`, so it
  is included in `requirements.txt`.
- All other endpoints are available in FastAPI and return the same payloads that
  the PHP version exposed, including JWT payload structure and pagination data.
- Automated tests live in `fastapi_app/tests/` (run with `pytest -q` after
  installing `requirements-dev.txt`).
