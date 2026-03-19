from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import argparse

from tools_common import parse_build_db_schema, print_json, read_live_db_schema, resolve_repo_root


def build_diff(expected: dict[str, dict[str, str]], live: dict[str, dict[str, str]], table_filter: str | None) -> dict:
    expected_tables = set(expected)
    live_tables = set(live)
    if table_filter:
        expected_tables = {table_filter} if table_filter in expected else set()
        live_tables = {table_filter} if table_filter in live else set()
    shared_tables = sorted(expected_tables & live_tables)
    missing_tables = sorted(expected_tables - live_tables)
    extra_tables = sorted(live_tables - expected_tables)
    table_diffs: list[dict] = []
    for table_name in shared_tables:
        expected_columns = expected[table_name]
        live_columns = live[table_name]
        missing_columns = sorted(set(expected_columns) - set(live_columns))
        extra_columns = sorted(set(live_columns) - set(expected_columns))
        type_mismatches = []
        for column_name in sorted(set(expected_columns) & set(live_columns)):
            expected_type = expected_columns[column_name]
            live_type = live_columns[column_name]
            if expected_type != live_type:
                type_mismatches.append(
                    {
                        "column": column_name,
                        "expected_type": expected_type,
                        "live_type": live_type,
                    }
                )
        if missing_columns or extra_columns or type_mismatches:
            table_diffs.append(
                {
                    "table": table_name,
                    "missing_columns": missing_columns,
                    "extra_columns": extra_columns,
                    "type_mismatches": type_mismatches,
                }
            )
    return {
        "missing_tables": missing_tables,
        "extra_tables": extra_tables,
        "table_diffs": table_diffs,
    }


def print_report(diff: dict) -> None:
    print("DB schema diff")
    print(f"- missing tables: {len(diff['missing_tables'])}")
    for table in diff["missing_tables"]:
        print(f"  - {table}")
    print(f"- extra tables: {len(diff['extra_tables'])}")
    for table in diff["extra_tables"]:
        print(f"  - {table}")
    print(f"- tables with column or type diffs: {len(diff['table_diffs'])}")
    for item in diff["table_diffs"]:
        print(f"  - {item['table']}")
        if item["missing_columns"]:
            print(f"    missing columns: {', '.join(item['missing_columns'])}")
        if item["extra_columns"]:
            print(f"    extra columns: {', '.join(item['extra_columns'])}")
        for mismatch in item["type_mismatches"]:
            print(
                f"    type mismatch: {mismatch['column']} expected={mismatch['expected_type']} live={mismatch['live_type']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare live DB schema with database/build_db.sql.")
    parser.add_argument("--table", help="Only compare one table.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    repo_root = resolve_repo_root()
    expected = parse_build_db_schema(repo_root / "database" / "build_db.sql")
    live = read_live_db_schema()
    diff = build_diff(expected, live, args.table)
    if args.json:
        print_json(diff)
    else:
        print_report(diff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
