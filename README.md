# Ildkule Backend

This repository contains the backend code for the Ildkule project.

It has two parts:

- `api/` is the old PHP API
- `fastapi_app/` is the new FastAPI version

The goal is to move from the old API to the new one in a safe way.

## What This Project Does

This backend:

- stores users, events, cameras, and stations
- reads meteor data from files
- saves data to MySQL
- gives data to frontend clients through an API
- keeps raw trail data and raw `.res` data for later use

## Project Structure

- `api/` old PHP code
- `fastapi_app/` new Python API
- `database/` SQL setup files
- `thunder-tests/` old API request examples

## Run The FastAPI App

1. Use Python 3.10 for this repo. Python 3.14 breaks the current FastAPI/Pydantic stack.
2. Create a virtual environment
3. Install packages
4. Copy the example env file
5. Start the server

Example:

```bash
py -3.10 -m pip install -r fastapi_app/requirements.txt
py -3.10 -m pip install -r fastapi_app/requirements-dev.txt
cp fastapi_app/.env.example fastapi_app/.env
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

The main SQL setup file is:

```text
database/build_db.sql
```

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

## Orbit Validation

To compare the current orbit runtime against published `tables.html` files, run:

```bash
py -3.10 scripts/validate_orbit_against_tables.py --data-root "D:\\My files\\Coding\\ildkule backup\\prod\\data" --date-from 20220101 --date-to 20220131
```

The script has two run profiles:

- `--profile dev` for short checks. This is the default. It scans a small sample and prints a short summary.
- `--profile final` for a full run. It scans the full date range unless you also set `--limit`.

It prints a human-readable report in Norwegian. The report explains:

- what `q`, `e`, `i`, `node`, `argp`, and `M` mean
- how many folders were skipped, and why
- how often runtime beats fallback
- median orbit error for observed, fallback, and runtime payloads
- the worst remaining cases

Use `--show-worst` to control how many bad cases are shown, and `--limit` to cap the number of folders in a dev run. For the final check, prefer `--profile final` and a large period that gives about 1000 or more comparable events when the data allows it.

The script also supports policy labels for iterative benchmarking:

- `--policy A|B|C` picks the policy used in the detailed report
- `--compare-policies A,B,C` prints a short side-by-side summary
- `--label` adds a free text tag for the run, so it is easier to compare iterations later
- `--workers N` runs the validation in parallel across many events. Use this for large final runs.

In this workflow:

- `A` is the current runtime line with the safer linear path solve
- `B` is the same base solve with stronger trimming of late trail points
- `C` adds a weak deceleration model along the same straight path

The script also prints where the time goes:

- reading `tables.html`
- loading event data
- building observed solve candidates
- building fallback solve
- final runtime selection

This matters because the slow part is still the per-event CPU work and coordinate math. GPU or CUDA is not the first choice here yet. CPU multiprocessing gives a more practical speed-up for the current workload.

The report also makes the main product rule visible: for every cross-station solved event that already exists in the published solution, the new system should still try a cross-station solve. Small differences from `tables.html` are fine. Larger differences are only a problem when the published solution itself looks clearly wrong.

The detailed report now splits observed results into three states:

- no observed candidate built
- observed candidate built, but rejected by the runtime guard
- observed accepted in runtime

## Notes

- The new API supports meteor import from file data.
- The import can create thumbnails from `image.jpg`.
- Event import is done through `/api/admin/event-imports`.
- The import upserts existing events and observations when it finds the same
  data again.
- Missing events and observations are soft-deleted, not hard-deleted.
- Deleted items are hidden by default in API list calls.

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

## Current Status

The FastAPI port is active and tested.

The old PHP API is still in the repository for reference during the move.
