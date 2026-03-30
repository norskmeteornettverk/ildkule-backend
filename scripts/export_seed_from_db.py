from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import MetaData, Table, create_engine, inspect, select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TABLE_ORDER = [
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
]

OUTPUT_FILES = {
    "mysql": REPO_ROOT / "database" / "seed_mysql.sql",
    "postgresql": REPO_ROOT / "database" / "seed_postgres.sql",
}

INSERT_BATCH_SIZE = {
    "mysql": 250,
    "postgresql": 500,
}

POSTGRES_BOOLEAN_COLUMNS = {
    ("user", "tutorial_completed"),
    ("user", "confirmed"),
    ("event", "is_deleted"),
    ("observation_cam_data", "is_deleted"),
}


def normalize_database_url(database_url: str) -> str:
    lowered = database_url.lower()
    if lowered.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://") :]
    if lowered.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url[len("postgres://") :]
    return database_url


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


def quote_identifier(identifier: str, dialect: str) -> str:
    if dialect == "mysql":
        return f"`{identifier}`"
    return f'"{identifier}"'


def quote_table(table_name: str, dialect: str) -> str:
    return quote_identifier(table_name, dialect)


def coerce_value_for_target(table_name: str, column_name: str, value: object, dialect: str) -> object:
    if (
        dialect == "postgresql"
        and (table_name, column_name) in POSTGRES_BOOLEAN_COLUMNS
        and isinstance(value, (int, float))
    ):
        return bool(value)
    return value


def render_value(value: object, dialect: str) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, datetime):
        return "'" + value.isoformat(sep=" ", timespec="microseconds").replace("'", "''") + "'"
    if isinstance(value, date):
        return "'" + value.isoformat().replace("'", "''") + "'"
    if isinstance(value, time):
        return "'" + value.isoformat(timespec="microseconds").replace("'", "''") + "'"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (bytes, bytearray)):
        hex_payload = bytes(value).hex()
        if dialect == "mysql":
            return f"X'{hex_payload}'"
        return f"'\\x{hex_payload}'"
    return "'" + str(value).replace("'", "''") + "'"


def sort_key_for_row(row: dict[str, object], primary_keys: list[str], columns: list[str]) -> tuple:
    key_columns = primary_keys or columns
    return tuple(row.get(column) for column in key_columns)


def batched_rows(rows: list[dict[str, object]], batch_size: int) -> list[list[dict[str, object]]]:
    if batch_size <= 0:
        return [rows]
    return [rows[index : index + batch_size] for index in range(0, len(rows), batch_size)]


def load_rows(engine, dialect: str) -> dict[str, list[dict[str, object]]]:
    metadata = MetaData()
    inspector = inspect(engine)
    rows_by_table: dict[str, list[dict[str, object]]] = {}
    with engine.connect() as connection:
        for table_name in TABLE_ORDER:
            if table_name not in inspector.get_table_names():
                rows_by_table[table_name] = []
                continue
            table = Table(table_name, metadata, autoload_with=engine)
            primary_keys = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
            stmt = select(table)
            order_columns = [table.c[column] for column in primary_keys if column in table.c]
            if order_columns:
                stmt = stmt.order_by(*order_columns)
            result = [dict(row) for row in connection.execute(stmt).mappings()]
            result.sort(key=lambda row: sort_key_for_row(row, primary_keys, list(table.c.keys())))
            rows_by_table[table_name] = result
    return rows_by_table


def render_seed(rows_by_table: dict[str, list[dict[str, object]]], dialect: str) -> str:
    lines = [
        "-- Generated seed file for Ildkule.",
        "-- Source: current DATABASE_URL contents at export time.",
        "-- Regenerate with: python scripts/export_seed_from_db.py",
        f"-- Insert batch size for {dialect}: {INSERT_BATCH_SIZE[dialect]} rows.",
        "",
    ]
    for table_name in TABLE_ORDER:
        rows = rows_by_table.get(table_name, [])
        if not rows:
            continue
        lines.append(f"-- Table {table_name}")
        columns = list(rows[0].keys())
        quoted_columns = ", ".join(quote_identifier(column, dialect) for column in columns)
        table_ref = quote_table(table_name, dialect)
        for batch in batched_rows(rows, INSERT_BATCH_SIZE[dialect]):
            value_groups: list[str] = []
            for row in batch:
                values = ", ".join(
                    render_value(
                        coerce_value_for_target(table_name, column, row[column], dialect),
                        dialect,
                    )
                    for column in columns
                )
                value_groups.append(f"({values})")
            lines.append(
                f"INSERT INTO {table_ref} ({quoted_columns}) VALUES\n  "
                + ",\n  ".join(value_groups)
                + ";"
            )
        lines.append("")
    if len(lines) == 5:
        lines.append("-- No rows exported.")
    lines.append("")
    return "\n".join(lines)


def total_row_count(rows_by_table: dict[str, list[dict[str, object]]]) -> int:
    return sum(len(rows) for rows in rows_by_table.values())


def log(message: str) -> None:
    print(message, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export deterministic seed SQL from the configured database.")
    parser.add_argument("--source-url", help="Optional SQLAlchemy database URL. Defaults to DATABASE_URL.")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow writing seed files even when the source database has zero rows.",
    )
    args = parser.parse_args()

    source_url = normalize_database_url(args.source_url or load_database_url())
    engine = create_engine(source_url, future=True)
    source_dialect = detect_dialect(source_url)
    log(f"Connecting to {source_dialect} source database...")
    rows_by_table = load_rows(engine, source_dialect)
    row_count = total_row_count(rows_by_table)

    if row_count == 0 and not args.allow_empty:
        raise SystemExit(
            "Refusing to write empty seed files because the source database returned zero rows. "
            "Check DATABASE_URL/--source-url, or pass --allow-empty if this is intentional."
        )

    for table_name in TABLE_ORDER:
        log(f"Loaded {len(rows_by_table.get(table_name, []))} rows from {table_name}.")

    for target_dialect, output_path in OUTPUT_FILES.items():
        log(f"Writing {output_path.name} for {target_dialect}...")
        output_path.write_text(render_seed(rows_by_table, target_dialect), encoding="utf-8")
        log(f"Wrote {output_path.name}")
    log(f"Exported {row_count} rows from {source_dialect}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
