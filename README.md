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

1. Create a virtual environment
2. Install packages
3. Copy the example env file
4. Start the server

Example:

```bash
pip install -r fastapi_app/requirements.txt
pip install -r fastapi_app/requirements-dev.txt
cp fastapi_app/.env.example fastapi_app/.env
uvicorn fastapi_app.app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to see the API docs.

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
