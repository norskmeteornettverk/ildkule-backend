# Ildkule Backend

This repository contains the active FastAPI backend for the Ildkule project.

## Project Structure

- `fastapi_app/` - the API application, routers, services, models, schemas, and tests
- `database/` - SQL setup and schema bootstrap files
- `scripts/` - local debug and validation tools
- `docs/` - backend notes and lineage documentation

Useful docs:

- `docs/glossary.md` - current backend and API terms
- `docs/api-db-file-lineage.md` - API, database, and file lineage

## What This Backend Does

- stores users, events, cameras, and stations
- reads meteor data from files
- saves data to MySQL
- serves data to frontend clients through the API
- keeps raw trail data and raw `.res` data for later use

## Run The API

Use Python 3.10 for this repo. Python 3.14 breaks the current FastAPI/Pydantic stack.

```bash
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
py -3.10 -m pip install --upgrade pip
py -3.10 -m pip install -r fastapi_app/requirements.txt
py -3.10 -m pip install -r fastapi_app/requirements-dev.txt
Copy-Item fastapi_app/.env.example fastapi_app/.env
py -3.10 -m uvicorn fastapi_app.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to see the API docs.

If `uvicorn` starts and then crashes with a Pydantic import error, check that
you are really using Python 3.10 and not a newer global Python install.

## MySQL Setup

You need a running MySQL server before you start the API.

Basic steps:

1. Create a database, for example `ildkule`
2. Put the correct MySQL login in `fastapi_app/.env`
3. Make sure the MySQL service is running

Example `DATABASE_URL`:

```text
mysql+pymysql://root:password@localhost:3306/ildkule
```

If your MySQL user uses `caching_sha2_password`, the Python app also needs
`cryptography`. This is already included in `fastapi_app/requirements.txt`.

## Database Script

The main SQL setup file is `database/build_db.sql`.

Use this file when you want to create a fresh database from scratch.

Important:

- this script drops and recreates tables
- do not run it on a database you want to keep

## If The Database Already Has Data

Be careful here.

The FastAPI app does not clear the database by itself when it starts.
It uses the existing tables and data.

If you already have important data:

- make a backup first
- do not run `database/build_db.sql`
- update the schema with safe SQL changes instead of full reset

Right now, `build_db.sql` is best for a new database, not for an old live one.

## Settings

The app reads settings from `fastapi_app/.env`.

Important values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `DATA_DIRECTORY`

## Tests

Run tests with:

```bash
pytest -q fastapi_app/tests
```

The test suite uses SQLite and does not need your local MySQL database.

## Import Behavior

`/api/admin/event-imports` reads event folders from `DATA_DIRECTORY`.

What it does:

- creates or updates events
- creates or updates observations
- stores raw trail data and raw `.res` rows
- keeps the full event folder tag in `event.datetimetag`, including short suffixes like `010101b` when they exist
- makes `thumbnail.jpg` from `image.jpg` when possible

If a meteor or observation was in the database before, but is not found in the
imported date range now, it is marked as deleted.

This is a soft delete:

- the row stays in the database
- `is_deleted` becomes `true`
- the API hides it by default

## Orbit Validation

To compare the current orbit runtime against published `tables.html` files, run:

```bash
py -3.10 scripts/validate_orbit_against_tables.py --data-root "D:\\My files\\Coding\\ildkule backup\\prod\\data" --date-from 20220101 --date-to 20220131
```

The script has two run profiles:

- `--profile dev` for short checks. This is the default.
- `--profile final` for a full run.

Useful options:

- `--show-worst` controls how many bad cases are shown
- `--limit` caps the number of folders in a dev run
- `--policy A|B|C` picks the policy used in the detailed report
- `--compare-policies A,B,C` prints a short side-by-side summary
- `--label` adds a free text tag for the run
- `--workers N` runs the validation in parallel across many events
