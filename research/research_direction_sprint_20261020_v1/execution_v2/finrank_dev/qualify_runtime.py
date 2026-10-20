#!/usr/bin/env python3
"""Non-generative GB10 runtime identity qualification through local forwarding."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from finrank_contract import (
    PACKAGE,
    load_object,
    sha256_bytes,
    sha256_file,
    utc_now,
    verify_bundle,
    write_json,
)


def get_json(base_url: str, path: str, timeout: int = 15) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(2_000_000)
            status = int(response.status)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"runtime_probe_failed:{path}:{type(exc).__name__}") from exc
    if status != 200:
        raise RuntimeError(f"runtime_probe_status_invalid:{path}:{status}")
    value = json.loads(body.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"runtime_probe_object_invalid:{path}")
    return value


def main() -> int:
    bundle = verify_bundle(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json")
    runtime = load_object(PACKAGE / "RUNTIME_IDENTITY_OVERRIDE_V1.json")
    identity = runtime["identity"]
    base_url = identity["base_url"]
    health = get_json(base_url, "/health")
    models = get_json(base_url, "/v1/models")
    props = get_json(base_url, "/props")
    model_data = models.get("data")
    model_ids = [
        item.get("id")
        for item in model_data
        if isinstance(item, dict)
    ] if isinstance(model_data, list) else []
    chat_template = props.get("chat_template")
    checks = {
        "health_ok": health.get("status") == "ok",
        "model_id_present": identity["model"]["model_id"] in model_ids,
        "model_path_matches": props.get("model_path") == identity["model"]["path"],
        "chat_template_matches": (
            isinstance(chat_template, str)
            and sha256_bytes(chat_template.encode("utf-8"))
            == identity["chat_template"]["sha256"]
        ),
        "thinking_disabled_boolean": identity["chat_template_kwargs"]
        == {"enable_thinking": False},
        "max_tokens_256": identity["generation"]["max_tokens"] == 256,
        "json_object_response": identity["generation"]["response_format"]
        == {"type": "json_object"},
        "endpoint_is_local_override": base_url == "http://127.0.0.1:18004",
    }
    output = {
        "schema": "finrank_runtime_qualification_v1",
        "checked_at_utc": utc_now(),
        "probe_type": "NON_GENERATIVE_HEALTH_MODELS_PROPS",
        "generation_requests": 0,
        "bundle_sha256": sha256_file(
            PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json"
        ),
        "bundle_schema": bundle["schema"],
        "endpoint_transport_override": runtime["transport_override"],
        "source_runtime_identity_sha256": runtime[
            "source_runtime_identity_sha256"
        ],
        "runtime_identity_override_sha256": sha256_file(
            PACKAGE / "RUNTIME_IDENTITY_OVERRIDE_V1.json"
        ),
        "observed": {
            "health": health,
            "model_ids": model_ids,
            "model_path": props.get("model_path"),
            "chat_template_sha256": (
                sha256_bytes(chat_template.encode("utf-8"))
                if isinstance(chat_template, str)
                else None
            ),
            "build_info": props.get("build_info"),
        },
        "checks": checks,
        "status": "QUALIFIED_NON_GENERATIVE" if all(checks.values()) else "FAILED",
    }
    write_json(PACKAGE / "RUNTIME_QUALIFICATION_C3.json", output)
    print(json.dumps({"status": output["status"], "checks": checks}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
