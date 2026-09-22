"""Static contract checks for runtime configuration shared by all launch paths."""

from __future__ import annotations

import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:15432/vector_db"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_local_runtime_uses_one_database_contract() -> None:
    env_example = _read(".env.example")
    run_script = _read("scripts/run.sh")
    compose = _read("docker-compose.yml")
    readme = _read("README.md")

    assert f"PGDATABASE_URL={CANONICAL_DATABASE_URL}" in env_example
    assert not re.search(r"^DATABASE_URL=", env_example, re.MULTILINE)
    assert f'PGDATABASE_URL:-{CANONICAL_DATABASE_URL}' in run_script
    assert "dotenv_values" in run_script
    assert "POSTGRES_DB=vector_db" in run_script
    assert "m1_statements" not in run_script
    assert "POSTGRES_DB: vector_db" in compose
    assert "PGDATABASE_URL: postgresql://postgres:postgres@pgvector:5432/vector_db" in compose
    assert "唯一数据库连接变量" in readme


def test_http_port_defaults_to_5050_everywhere() -> None:
    app_config = json.loads(_read("config/app_config.json"))
    main_source = _read("src/main.py")
    run_script = _read("scripts/run.sh")

    assert app_config["web"]["port"] == 5050
    assert 'os.getenv("M1_PORT", "5050")' in main_source
    assert 'M1_PORT="${M1_PORT:-5050}"' in run_script
