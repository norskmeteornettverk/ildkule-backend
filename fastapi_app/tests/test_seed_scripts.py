from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORT_SCRIPT = REPO_ROOT / "scripts" / "export_seed_from_db.py"


def load_export_module():
    spec = importlib.util.spec_from_file_location("export_seed_from_db", EXPORT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_render_seed_batches_postgres_inserts_and_coerces_booleans():
    export_seed = load_export_module()
    rows = [
        {
            "id": index + 1,
            "username": f"user-{index + 1}",
            "password": "secret",
            "role": "ROLE_USER",
            "user_level": "0",
            "tutorial_completed": index % 2,
            "confirmed": (index + 1) % 2,
            "confirm_token": None,
            "password_reset_token": None,
            "password_reset_request_time": None,
            "create_time": None,
            "update_time": None,
        }
        for index in range(501)
    ]

    rendered = export_seed.render_seed({"user": rows}, "postgresql")

    assert "-- Insert batch size for postgresql: 500 rows." in rendered
    assert rendered.count('INSERT INTO "user"') == 2
    assert "TRUE" in rendered
    assert "FALSE" in rendered
