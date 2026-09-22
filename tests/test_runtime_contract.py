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
    serve_script = _read("serve.sh")
    compose = _read("docker-compose.yml")
    readme = _read("README.md")

    assert f"PGDATABASE_URL={CANONICAL_DATABASE_URL}" in env_example
    assert not re.search(r"^DATABASE_URL=", env_example, re.MULTILINE)
    assert f'PGDATABASE_URL:-{CANONICAL_DATABASE_URL}' in serve_script
    assert "dotenv_values" in serve_script
    assert "POSTGRES_DB=vector_db" in run_script
    assert "m1_statements" not in serve_script
    assert "POSTGRES_DB: vector_db" in compose
    assert "PGDATABASE_URL: postgresql://postgres:postgres@pgvector:5432/vector_db" in compose
    assert "唯一数据库连接变量" in readme


def test_http_port_defaults_to_5050_everywhere() -> None:
    app_config = json.loads(_read("config/app_config.json"))
    main_source = _read("src/main.py")
    serve_script = _read("serve.sh")

    assert app_config["web"]["port"] == 5050
    assert 'os.getenv("M1_PORT", "5050")' in main_source
    assert 'M1_PORT="${M1_PORT:-5050}"' in serve_script


def test_docker_image_contains_required_runtime_roots() -> None:
    dockerfile = _read("Dockerfile")

    for copy_instruction in (
        "COPY src/ ./src/",
        "COPY scripts/ ./scripts/",
        "COPY models/ ./models/",
        "COPY config/ ./config/",
        "COPY serve.sh ./serve.sh",
    ):
        assert copy_instruction in dockerfile


def test_active_launchers_delegate_to_one_serve_script() -> None:
    delegates = {
        "scripts/run.sh": "exec ./serve.sh",
        "scripts/m1_serve.sh": "exec ./serve.sh",
        "scripts/restart_m1_harness.sh": "nohup ./serve.sh",
        "Dockerfile": 'CMD ["bash", "serve.sh"]',
        "deploy/m1-harness.service": "ExecStart=/home/testuser/wzh/projects/agents_final_tech/serve.sh",
        "deploy/supervisord.conf": "command=/home/testuser/wzh/projects/agents_final_tech/serve.sh",
    }

    for path, expected in delegates.items():
        content = _read(path)
        assert expected in content, f"{path} does not delegate to serve.sh"
        assert " --workers " not in content, f"{path} still owns an Uvicorn command"

    assert "exec \"$PYTHON_BIN\" -m uvicorn main:app" in _read("serve.sh")
