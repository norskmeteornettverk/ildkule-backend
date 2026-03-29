from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

from sqlalchemy import create_engine, inspect, text

ACTIVE_TABLES = (
    "user",
    "manual_input_observation",
    "station",
    "cam",
    "event",
    "observation_cam_data",
    "event_res_entry",
    "observation_trail_point",
    "log_station",
    "user_review",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def detect_dialect(database_url: str) -> str:
    scheme = urlsplit(database_url).scheme.split("+", 1)[0].lower()
    if scheme in {"mysql", "mariadb"}:
        return "mysql"
    if scheme in {"postgresql", "postgres"}:
        return "postgresql"
    raise SystemExit(f"Unsupported DATABASE_URL dialect: {scheme}")


def load_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    env_path = REPO_ROOT / "fastapi_app" / ".env"
    if env_path.is_file():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DATABASE_URL":
                return value.strip().strip("\"'")

    raise SystemExit("DATABASE_URL is not set in the environment or fastapi_app/.env.")


def split_sql_statements(sql_text: str) -> list[str]:
    sql_text = "\n".join(
        line for line in sql_text.splitlines() if not line.lstrip().startswith("--")
    )
    statements: list[str] = []
    chunk: list[str] = []
    in_single = False
    in_double = False
    escape = False
    for character in sql_text:
        chunk.append(character)
        if escape:
            escape = False
            continue
        if character == "\\":
            escape = True
            continue
        if character == "'" and not in_double:
            in_single = not in_single
            continue
        if character == '"' and not in_single:
            in_double = not in_double
            continue
        if character == ";" and not in_single and not in_double:
            statement = "".join(chunk).strip()
            if statement:
                statements.append(statement)
            chunk = []
    tail = "".join(chunk).strip()
    if tail:
        statements.append(tail)
    return statements


def script_paths_for_dialect(dialect: str, include_seed: bool) -> list[Path]:
    database_dir = REPO_ROOT / "database"
    schema_map = {
        "mysql": database_dir / "build_db.sql",
        "postgresql": database_dir / "build_db_postgres.sql",
    }
    seed_map = {
        "mysql": database_dir / "seed_mysql.sql",
        "postgresql": database_dir / "seed_postgres.sql",
    }
    paths = [schema_map[dialect]]
    if include_seed:
        paths.append(seed_map[dialect])
    return paths


def apply_sql_scripts(database_url: str, script_paths: Iterable[Path]) -> None:
    engine = create_engine(database_url, future=True)
    with engine.begin() as connection:
        for script_path in script_paths:
            sql_text = script_path.read_text(encoding="utf-8")
            for statement in split_sql_statements(sql_text):
                if not statement or statement.startswith("--"):
                    continue
                connection.execute(text(statement))


def has_existing_schema(database_url: str) -> bool:
    engine = create_engine(database_url, future=True)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    return any(table_name in existing_tables for table_name in ACTIVE_TABLES)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the configured MySQL or PostgreSQL database.")
    parser.add_argument("--schema-only", action="store_true", help="Apply only the schema bootstrap.")
    parser.add_argument("--seed", metavar="NAME", help="Also apply the generated seed file. The value is informational only.")
    parser.add_argument("--rebuild", action="store_true", help="Acknowledge that the bootstrap may drop and recreate tables.")
    args = parser.parse_args()

    database_url = load_database_url()
    dialect = detect_dialect(database_url)
    include_seed = bool(args.seed) and not args.schema_only

    if has_existing_schema(database_url) and not args.rebuild:
        raise SystemExit(
            "Refusing to apply bootstrap to a non-empty schema without --rebuild."
        )

    paths = script_paths_for_dialect(dialect, include_seed=include_seed)
    apply_sql_scripts(database_url, paths)
    print(f"Applied {' + '.join(path.name for path in paths)} for {dialect}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
