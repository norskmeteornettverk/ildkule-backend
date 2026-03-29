# Ildkule FastAPI API

The active backend code lives under `fastapi_app/` and exposes the API route
structure used by the project (`/api/auth/login`, `/api/users`, `/api/events`,
and related endpoints).

## Getting started

Use Python 3.10 for this repo. Python 3.14 is not a safe choice here and can
break FastAPI/Pydantic imports.

1. Use a local virtual environment for this project. Do not rely on global Python packages.
   Example:
   ```bash
   py -3.10 -m venv .venv
   ```
2. Activate the virtual environment.
   Example on Windows PowerShell:
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies with the same Python interpreter that owns the virtual environment:
   ```bash
   py -3.10 -m pip install --upgrade pip
   py -3.10 -m pip install -r fastapi_app/requirements.txt
   ```
4. Optional for tests:
   ```bash
   py -3.10 -m pip install -r fastapi_app/requirements-dev.txt
   ```
5. Copy the sample environment file and adjust the values so they match your
   infrastructure:
   ```bash
   cp fastapi_app/.env.example fastapi_app/.env
   ```
6. Start the API server with the same Python interpreter:
   ```bash
   py -3.10 -m uvicorn fastapi_app.app.main:app --reload
   ```

The application reads configuration from `fastapi_app/.env` regardless of the
current working directory. At a minimum set
`DATABASE_URL` and `JWT_SECRET_KEY`. SMTP and reCAPTCHA settings
are optional but required if you want to send contact/report forms.  The station
log endpoint validates a bearer token configured via `STATION_LOG_TOKEN`.

Supported DB URL formats:

```text
mysql+pymysql://user:pass@host:3306/dbname
postgresql+psycopg://user:pass@host:5432/dbname
```

If startup fails with import or dependency errors, first check that the virtual
environment is active and that the packages were installed inside that
environment. A mixed global/local Python setup can load the wrong package
versions.

If the app crashes with a Pydantic import error, double-check that you are not
running it with Python 3.14 from the global install.

## Notes

- `/api/admin/event-imports` ingests meteor observations directly from the data
  directory configured via `DATA_DIRECTORY`.
- `PyMySQL` needs `cryptography` when MySQL uses `caching_sha2_password`, so it
  is included in `requirements.txt`.
- PostgreSQL support also depends on the PostgreSQL driver being added to
  `requirements.txt` by the DB/runtime slice.
- The API keeps the expected JWT payload structure and pagination data used by
  the current clients.
- Automated tests live in `fastapi_app/tests/` (run with `pytest -q` after
  installing `requirements-dev.txt`).

## Fresh Database Bootstrap

The dual-database rollout is intended to use:

- `database/build_db.sql` for MySQL schema bootstrap
- `database/build_db_postgres.sql` for PostgreSQL schema bootstrap
- `database/seed_mysql.sql` for optional large exported MySQL seed data
- `database/seed_postgres.sql` for optional large exported PostgreSQL seed data
- `scripts/bootstrap_db.py` for schema-only or schema+seed setup
- `scripts/export_seed_from_db.py` for regenerating the exported seed data from
  the current loaded DB

These files and commands depend on the schema/bootstrap slice being merged.

## Media Source Modes

The deployment target is intended to support two media source modes through
config only:

- `local` mode: serve event/media files from a mounted local data directory
- `remote` mode: point event/media links at a published web resource

Planned config values:

```text
EVENT_MEDIA_SOURCE_MODE=local|remote
EVENT_MEDIA_BASE_URL=/data
```

Example remote setup:

```text
EVENT_MEDIA_SOURCE_MODE=remote
EVENT_MEDIA_BASE_URL=https://norskmeteornettverk.no/meteor
```

The serializer/runtime slice must implement the actual URL switching behavior.

## Vercel Deployment

This repo now includes repo-root deploy glue for Vercel:

- root `app.py` re-exports `fastapi_app.app.main:app`
- root `requirements.txt` delegates to `fastapi_app/requirements.txt`

Recommended Vercel setup:

1. Use the repo root as the project root.
2. Use a free Neon Postgres database.
3. Set these Vercel environment variables:
   - `DATABASE_URL`
   - `JWT_SECRET_KEY`
   - `FRONT_URL`
   - `EVENT_MEDIA_SOURCE_MODE=remote`
   - `EVENT_MEDIA_BASE_URL=https://norskmeteornettverk.no/meteor`
4. Leave `DATA_DIRECTORY` unset on Vercel.

Important:

- Vercel should host the API only.
- File-backed import and local file hosting belong on another environment.
- Full PostgreSQL runtime support and remote media URL support depend on the
  runtime/config slices being merged.
