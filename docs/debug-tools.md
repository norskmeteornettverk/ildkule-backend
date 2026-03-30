# Debug Tools

Use these local CLI tools before reading a lot of files by hand. They are meant to save time and tokens.

## Schema checks

- `py -3.10 scripts\db_schema_diff.py`
  - compares the live database schema with `C:\Users\Nikolai\Desktop\Kode\Ildkule (Norsk meteornettverk)\ildkule-backend\database\build_db.sql`
  - shows missing tables, missing columns, extra columns, and type mismatches
  - useful before blaming loader or API code for missing data
  - depends on:
    - working DB connection in `fastapi_app/.env`
    - live MySQL database
- `py -3.10 scripts\db_schema_diff.py --table observation_trail_point`
  - same tool, but narrowed to one table

## Dataset inventory

- `py -3.10 scripts\data_inventory.py --data-root "D:\My files\Coding\ildkule backup\prod\data"`
  - scans the dataset root without doing a full import
  - counts date folders, event folders, suffix folders, camera folders, and key files like `event.txt`, `centroid.txt`, `centroid2.txt`, and `tables.html`
  - useful for checking what data really exists before working on ingestion or orbit coverage
  - depends on:
    - dataset root from `--data-root`, or `DATA_DIRECTORY` in `fastapi_app/.env`

## Single-event inspection

- `py -3.10 scripts\event_inspect.py --datetimetag 20220103181852 --data-root "D:\My files\Coding\ildkule backup\prod\data"`
  - shows one event from DB and disk in one report
  - includes:
    - event fields
    - observations in DB
    - trail point counts
    - AMS / centroid counts
    - which files exist in the event folder
  - use `--event-id` instead of `--datetimetag` if needed
  - useful before opening many model, service, and raw data files by hand
  - depends on:
    - live DB
    - optional dataset root for file lookup

- `py -3.10 scripts\orbit_diagnose.py --datetimetag 20220103181852 --data-root "D:\My files\Coding\ildkule backup\prod\data"`
  - diagnoses one event in the orbit flow
  - compares:
    - old simple calculation
    - `policy_a`
    - `policy_b`
    - `policy_c`
    - `reserve`
    - final API choice
  - reports which stage the new point-based calculation stops at, for example:
    - no usable station track
    - fewer than two usable stations
    - speed or direction could not be solved
    - full new orbit built but rejected before final API choice
  - shows errors against `tables.html` when that file exists
  - useful for orbit debugging before running the larger validation script
  - depends on:
    - live DB
    - optional dataset root for `tables.html`

## Batch orbit validation

- `py -3.10 scripts\validate_orbit_against_tables.py --data-root "D:\My files\Coding\ildkule backup\prod\data" --profile final --workers 4 --show-worst 10`
  - runs the larger orbit validation against published `tables.html` files
  - use this when you need the big picture, not just one event
  - reports:
    - how many comparable events were found
    - how many old published tables look physically reasonable
    - how many events the new point-based calculation can build a full orbit for
    - how many of those look physically reasonable
    - how often the new point-based result is nearer to `tables.html` than the old simple calculation
    - how often the final API choice uses the new orbit
    - funnel stages and common failure reasons
    - per-policy comparison for `policy_a`, `policy_b`, `policy_c`, and `reserve`
    - timing breakdown for tables read, loading, new orbit solve, old simple calculation, and final API choice
  - use `--profile dev` for a small sample and `--profile final` for the full run
  - use `--workers` to speed it up with CPU multiprocessing
  - depends on:
    - dataset root with `tables.html`, `event.txt`, and related event files
    - current orbit solver code in `fastapi_app/app/utils/orbit_solver.py`
  - this is the main tool for orbit coverage and orbit quality tracking

- `py -3.10 scripts\mass_orbit_sql_candidates.py`
  - takes the SQL-filtered candidate set and runs the orbit solver on all of them in batch
  - reports:
    - how many candidates each policy can solve
    - how many are solved by any from-scratch policy (`policy_a`, `policy_b`, `policy_c`)
    - how many are solved only by `reserve`
    - how many final runtime results are usable and physically wild
    - a few example events that still fail completely
  - use this when you want to test the solver against the full SQL candidate set without hand-picking events
  - depends on:
    - live DB
    - the orbit solver in `fastapi_app/app/utils/orbit_solver.py`
    - the same SQL quality filter used for the candidate set
  - supports the same local DB and dataset setup as the other orbit tools

## Shared notes

- All orbit tools listed above support `--json`.
  - use that for piping into later scripts or for quick machine-readable checks
  - shared helper code lives in `C:\Users\Nikolai\Desktop\Kode\Ildkule (Norsk meteornettverk)\ildkule-backend\scripts\tools_common.py`

Prefer these tools when they answer the question directly. Do not manually inspect many raw event folders or DB tables first if one of these tools already covers the job.
