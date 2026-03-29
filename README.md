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

## Deploy Notes

- Root `app.py` re-exports the FastAPI app for platforms like Vercel.
- Root `requirements.txt` delegates to `fastapi_app/requirements.txt` so a
  repo-root deploy can install the backend dependencies without custom path
  tricks.

## What This Backend Does

- stores users, events, cameras, and stations
- reads meteor data from files
- saves data to SQL databases
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

## Database Setup

The runtime DB is selected by `DATABASE_URL`.

Supported DSN formats:

```text
mysql+pymysql://root:password@localhost:3306/ildkule
postgresql+psycopg://postgres:password@localhost:5432/ildkule
```

Today the live codebase still needs the DB/runtime slice for full PostgreSQL
support. The Vercel/docs slice in this commit prepares the deploy glue and the
operator docs, while the DB/runtime and schema workers add the matching backend
behavior.

### MySQL Setup

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

### PostgreSQL Setup

You also need a running PostgreSQL server before you start the API in a
PostgreSQL environment.

Example `DATABASE_URL`:

```text
postgresql+psycopg://postgres:password@localhost:5432/ildkule
```

PostgreSQL support depends on:

- the PostgreSQL driver being present in `fastapi_app/requirements.txt`
- the PostgreSQL schema bootstrap file
- the DB/runtime slice updating dialect-specific SQL paths

## Database Script

The current main SQL setup file is `database/build_db.sql`.

That file is the MySQL bootstrap.

Planned fresh-install layout for the dual-database work:

- `database/build_db.sql` - MySQL schema bootstrap
- `database/build_db_postgres.sql` - PostgreSQL schema bootstrap
- `database/seed_mysql.sql` - optional large exported seed for MySQL
- `database/seed_postgres.sql` - optional large exported seed for PostgreSQL
- `scripts/bootstrap_db.py` - schema or schema+seed runner
- `scripts/export_seed_from_db.py` - exports the current loaded DB into
  deterministic seed SQL files

Use the schema file that matches your engine when you want to create a fresh
database from scratch.

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

Right now, the shipped `build_db.sql` is best for a new MySQL database, not for
an old live one.

## Settings

The app reads settings from `fastapi_app/.env`.

Important values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `DATA_DIRECTORY`

The deployment plan also depends on these config values being supported by the
runtime/config slice:

- `EVENT_MEDIA_SOURCE_MODE=local|remote`
- `EVENT_MEDIA_BASE_URL`

Target behavior:

- `local` mode points event/media URLs to files exposed from a mounted data
  directory
- `remote` mode points event/media URLs to a published web resource such as
  `https://norskmeteornettverk.no/meteor`

## Tests

Run tests with:

```bash
pytest -q fastapi_app/tests
```

The test suite uses SQLite and does not need your local MySQL database.

The current automated suite does not yet prove full PostgreSQL runtime support.
That coverage belongs to the DB/runtime implementation slice.

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

## Vercel + Neon Deployment

For Vercel, use PostgreSQL and keep the deployment API-only.

Recommended target setup:

1. Connect the repo to Vercel.
2. Use the repo root as the deploy root.
3. Let Vercel discover `app.py` at the repo root.
4. Install a free Neon Postgres database through the Vercel integration.
5. Set at least these environment variables in Vercel:
   - `DATABASE_URL`
   - `JWT_SECRET_KEY`
   - `FRONT_URL`
   - `EVENT_MEDIA_SOURCE_MODE=remote`
   - `EVENT_MEDIA_BASE_URL=https://norskmeteornettverk.no/meteor`
6. Leave `DATA_DIRECTORY` unset on Vercel.

Operational notes:

- Vercel should serve the API only.
- File-backed import and local `/data` hosting should stay outside the Vercel
  deployment.
- Event and media links should point to the existing published website in remote
  mode.
- Automatic schema/seed commands depend on the bootstrap/export slice being
  merged.
