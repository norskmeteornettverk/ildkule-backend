# Glossary

This glossary explains terms used by the current FastAPI backend, its API
payloads, the database models, and the file-ingestion flow.

Use current FastAPI names first. Older words should only be mentioned when they
still matter for compatibility fields, imported data, or debugging.

## Suggested Use

Keep this file in `docs/glossary.md`.
Link to it from `README.md` when a short repo overview is not enough.

## Core Domain Terms

`event`
A meteor event stored in the database. One event can contain one or more camera observations.

`observation`
One camera record of an event. In code this is mainly `ObservationCamData`.

`station`
A physical place that runs one or more cameras.

`cam`
One camera on a station, for example `cam1` or `cam4`.

`datetimetag`
A file-based event key built from the date folder and time folder, for example `20240512235404`. Some folders keep a short suffix, for example `20221030035410b`.

`location`
A text value that says where the event was seen or calculated to be.

`cross_station_confirmed`
The public FastAPI name for an event solved from more than one station or otherwise marked as cross-station solved by the imported data.

`event_type`
The public event class shown by the API. Common values are `Krysspeilet`, `Upeilet`, and `Meteorittkandidat`.

`candidate`
The candidate summary object used in event payloads and explore responses. It includes `is_candidate`, `max_end_height_km`, and `max_speed_kms`.

`res entries`
Parsed rows from a `.res` file. These rows hold solved geometry and station-level line data for an event.

`trail points`
Frame-by-frame observation rows built from `event.txt` and optional centroid files. They are exposed through `/api/observations/{id}/trail`.

## API Contract Terms

`identifier`
The public user-login and user-response field used instead of exposing the internal `username` column name.

`account_confirmed`
The public response field that tells whether a user account has been confirmed.

`user_role`
The primary role string returned in auth and user payloads.

`roles`
A compatibility list of roles. The current backend returns the same role as `user_role` inside a one-item list.

`token`
The JWT access token returned by login.

`accessToken`
A compatibility copy of `token`. The current backend returns the same token value in both fields.

`tutorial_completed`
The user status flag that says whether the account has completed the tutorial flow.

`station network`
The richer operational API view returned by `/api/station-network`, with per-station and per-camera status, connectivity, and snapshot or image links.

## File And Ingestion Terms

`event.txt`
The main per-observation source file. It contains summary data and trail arrays used during import.

`centroid.txt` and `centroid2.txt`
Optional files with extra point series that can be matched onto trail frames during import.

`tables.html`
A published event output used by local validation tools when comparing orbit results.

`soft delete`
Rows are kept in the database, but marked with `is_deleted = true` and hidden from normal API list calls unless deleted rows are explicitly requested.

`upsert`
Import behavior where an existing event or observation is updated when the same source item is seen again, instead of creating a duplicate row.
