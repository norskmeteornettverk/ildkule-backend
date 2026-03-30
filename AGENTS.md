# Repository Guidelines

## Project Structure & Module Organization
This repository contains one active backend implementation:
- `fastapi_app/`: Python/FastAPI app (`app/routers`, `app/services`, `app/models`, `app/schemas`, `app/utils`).
Supporting folders:
- `fastapi_app/tests/`: pytest suite for FastAPI endpoints and ingestion.
- `database/build_db.sql`: database bootstrap schema.
- `scripts/`: local debug and validation tools.

## Build, Test, and Development Commands
Use these commands from repository root.
- `pip install -r fastapi_app/requirements.txt` - install FastAPI runtime dependencies.
- `pip install -r fastapi_app/requirements-dev.txt` - install test-only Python dependencies.
- `uvicorn fastapi_app.app.main:app --reload` - run FastAPI locally with auto-reload.
- `pytest -q fastapi_app/tests` - run Python tests.

## Local Debug Tools
Use these local CLI tools before reading many files by hand. Prefer them when they answer the question directly.
- For schema drift, use `scripts\db_schema_diff.py`.
- For dataset shape and file coverage, use `scripts\data_inventory.py`.
- For single-event debugging, use `scripts\event_inspect.py` and `scripts\orbit_diagnose.py`.
- For batch orbit coverage or quality checks, use `scripts\validate_orbit_against_tables.py` or `scripts\mass_orbit_sql_candidates.py`.
- Orbit tools support `--json` for machine-readable output.
- Full commands, flags, dependencies, and examples live in `docs/debug-tools.md`.

## Orbit Work Discipline
- Start narrow. Lock the exact event or metric first. Do not mix data import, SQL filtering, solver math, runtime payloads, and docs in the same pass unless the task really needs all of them.
- Use tools before code. For orbit work, start with `event_inspect.py`, `orbit_diagnose.py`, SQL, or `mass_orbit_sql_candidates.py` before opening large code files.
- Do not reread `fastapi_app/app/utils/orbit_solver.py` broadly. Search for the exact function, then open only the small code slice you need.
- Keep a short working note with three buckets: directly observed, inferred, and still unproven. Do not keep reloading files just to reconstruct the same state.
- Work one concrete case at a time. Prove one failure reason, make one focused change, run one focused check, then move on.
- Verify runtime separately from helper scripts. If `build_orbit_payload(...)` and a local debug script disagree, treat runtime as truth and fix the script.

## Coding Style & Naming Conventions
- Follow normal Python/FastAPI conventions: PEP 8, 4-space indentation, `snake_case` for functions/modules, and `PascalCase` for classes.
- Keep API route naming aligned with the active FastAPI contracts, and prefer small service-layer methods over controller-heavy logic.

## Documentation Language
- Be a direct, concise writer. No corporate jargon. No flowery language. Write like a human. No AI-slop.
- Aim for B1 level language: shorter sentences, common words, (and clear step-by-step instructions where it may add value).
- Write README files and other user-facing docs in simple English.
- Write docstrings and technical documentation in simple English too.
- Avoid extra jargon when plain words are enough.
- Explain setup risks clearly, especially for MySQL, SQL scripts, and existing data.

## Analysis And Documentation Discipline
- For deep feature specs, migration specs, or broader gap analysis, use the `deep-feature-spec` skill.
- In repo docs, keep a hard distinction between directly observed behavior, directly observed code, and inferences.

## Large File And Data Handling
- Sample large raw data before full reads, and start with filenames, headers, suffix patterns, and structure.
- For file analysis, describe what the file contains, how it is used, and whether it exists in published output, local data, and current ingestion.

## Runtime Verification And Delivery Discipline
- Treat code, runtime responses, and tests as the source of truth. Do not describe planned behavior as if it already exists.
- Do not say a route, field, schema, or payload is finished until it is:
  - implemented in code
  - checked in the actual response or OpenAPI output
  - covered by a relevant test when possible
- The common failure mode in this repo is contract drift:
  - runtime, OpenAPI, tests, and repo-tracked docs say slightly different things
  - fix that drift directly instead of only patching one layer
- Do not say a file was updated unless it was actually edited on disk.
- Do not say work was committed or pushed until `git status`, `git log -1`, and `git push` have been checked.
- Work in small complete slices: (1) inspect the code, (2) make the change, (3) update or add tests, (4) run the relevant tests, and then (5) update repo-tracked docs that depend on the change
- Prefer one verified completed slice over several half-finished changes.
- When checking API work, verify all three layers when relevant:
  - router and request or response model
  - service or serialization logic
  - actual runtime response or test assertion
- For FastAPI work, prefer declarative contract wiring over manual prose or ad-hoc headers:
  - use `response_model`, `responses`, typed schemas, `Depends(...)`, and shared auth/security helpers
  - do not rely on route descriptions alone to express auth, error responses, nullability, or payload shape
- Do not assume a field is available just because it appears in a schema.
- Do not assume a field is documented correctly just because it appears in runtime.
- If serializer output is broader than the public schema, decide explicitly what the public contract is and lock that in tests.
- When a route gains or changes public contract details, add both positive and negative assertions where useful:
  - assert the wanted field, response, or security metadata exists
  - assert the old weak/manual contract is gone when that matters
- Keep a hard distinction between:
  - directly observed in backend code
  - directly observed in frontend code or UI
  - inferred by combining sources
- Mark uncertainty clearly and verify it before updating main docs.
- If you use subagents, give them narrow file or feature ownership and verify their results before reporting completion.
- Do not present subagent output as final until the main agent has checked the affected files, tests, and git state.
- If a command fails, stop and correct course.
- Do not continue from a failed assumption.
- If a test, coverage run, schema check, or push fails, report that clearly and fix it before claiming success.
- Respect local repo state:
  - check `git status` before starting and before committing
  - do not include unrelated local changes in commits
  - if another repo has local changes, leave them alone unless the task explicitly includes them
- Update dependent docs whenever runtime truth changes:
  - `docs/api-db-file-lineage.md` for API, DB, ingestion, or file-mapping changes
  - other repo-tracked docs when contract or behavior changes
- Docs must reflect current verified behavior first. Open gaps should be listed separately as gaps.
- Use clear English in repository docs.
- Avoid vague AI wording, unnecessary jargon, and completion language that hides uncertainty.
- When writing Norwegian text in linked spec work or user-facing content, use proper Norwegian characters.

## Live OpenAPI Verification
- Treat `http://127.0.0.1:8000/docs#/` and `http://127.0.0.1:8000/openapi.json` as the final source of truth for Swagger/OpenAPI.
- After any backend change that affects routes, schemas, serialization, response models, query parameters, or endpoint descriptions, verify the affected endpoints in the live docs before stopping.
- For API cleanup work, check these four layers together before calling it done:
  - router metadata
  - schema / response model
  - live OpenAPI
  - explicit test assertions
- Prefer fixing OpenAPI by improving FastAPI declarations in code, not by leaving the truth only in prose or comments.
- Do not assume any static OpenAPI file or previously exported schema is current unless it has been regenerated and checked against the running app.
- If code, tests, docs, and live OpenAPI disagree, fix the mismatch before finishing the task.

## Issue And Project Tracking
- This repo uses both GitHub Issues and the org GitHub Project `Ildkule`.
- Use repo issues for concrete backend, API, ingestion, or test work that should be implemented in code.
- Use GitHub Project draft tasks for broader spec work, review follow-up, open questions, and contract clarification that is not yet ready to become a code issue.
- When a draft task becomes concrete engineering work, create or link a repo issue and keep both items aligned.
- When an issue belongs to active planning, add it to the GitHub Project so status, priority, and follow-up are visible in one place.
- Keep spec and tracking in sync:
  - update `OPEN_QUESTIONS.md` when an open question is clarified, moved to a task, or moved to an issue
  - update `API_SPEC.md` and other deep docs with short references to the related issue or project task when that helps traceability
  - update lineage docs after API or model decisions are implemented
  - update `docs/api-db-file-lineage.md` whenever code changes affect API fields, DB columns, serialization, ingestion, or file-to-DB mapping

## Testing Guidelines
- Python tests use `pytest`; name files `test_*.py` and test functions `test_*`.
- Add/adjust tests for any behavior change in routers/controllers, auth, or data ingestion.

## Commit & Pull Request Guidelines
Recent history uses short, imperative subjects (for example: `Refactoring of controller layer - improving security`, `reCaptcha validation ...`). Follow that style:
- Keep subject line concise and action-oriented.
- Mention scope when useful (`fastapi`, `api`, `tests`, `security`).

For pull requests:
- Describe what changed and why.
- Link related issue/task.
- Include test evidence (`pytest` output or equivalent).
- For API behavior changes, include example request/response.
- Call out database or `.env` changes explicitly.
