#!/usr/bin/env python3
"""Build a non-generative runtime identity snapshot from existing pinned artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from execution_core import sha256_file, write_json_lf


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"json object required: {path}")
    return payload


def sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-pin", required=True, type=Path)
    parser.add_argument("--service-props", required=True, type=Path)
    parser.add_argument("--model-file", required=True, type=Path)
    parser.add_argument("--server-binary", required=True, type=Path)
    parser.add_argument("--runtime-policy", required=True, type=Path)
    parser.add_argument("--plan-prompt", required=True, type=Path)
    parser.add_argument("--consume-prompt", required=True, type=Path)
    parser.add_argument("--output-schemas", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    model_pin = read_json(args.model_pin)
    service_props = read_json(args.service_props)
    if not isinstance(service_props.get("body_text"), str):
        raise ValueError("service_props.body_text must be string")
    service_body = json.loads(service_props["body_text"])
    policy = read_json(args.runtime_policy)
    plan_prompt = read_json(args.plan_prompt)
    consume_prompt = read_json(args.consume_prompt)
    schemas = read_json(args.output_schemas)

    model_sha = sha256_file(args.model_file)
    server_sha = sha256_file(args.server_binary)
    chat_template = service_body.get("chat_template")
    if not isinstance(chat_template, str):
        raise ValueError("chat_template missing")
    chat_sha = sha256_text(chat_template)
    checks = {
        "model_id_matches_policy":
            model_pin.get("model_id") == policy.get("model") == service_body.get("model_alias"),
        "model_path_matches_service":
            str(args.model_file) == service_body.get("model_path"),
        "model_sha_matches_pin":
            model_sha == model_pin.get("model_file_sha256") == model_pin.get("model_sha256_expected"),
        "server_sha_matches_pin":
            server_sha == model_pin.get("server_bin_sha256") == model_pin.get("server_sha256_expected"),
        "chat_template_sha_matches_pin":
            chat_sha == model_pin.get("chat_template_sha256"),
        "chat_template_len_matches_pin":
            len(chat_template) == model_pin.get("chat_template_len"),
        "generation_within_output_cap":
            policy["generation"]["max_tokens"] <= policy["limits"]["output_tokens_max"],
        "thinking_disabled_with_json_boolean":
            policy["chat_template_kwargs"].get("enable_thinking") is False,
        "worst_case_budget_fits":
            policy["limits"]["request_cap"] *
            policy["limits"]["per_request_reserve_tokens"] <=
            policy["limits"]["token_cap"],
    }
    blockers = [name for name, passed in checks.items() if not passed]
    snapshot = {
        "schema": "collection_runtime_identity_snapshot_v1",
        "status": "BOUND_NON_GENERATIVE_IDENTITY" if not blockers else "IDENTITY_BLOCKED",
        "generated_by": "file hashing and JSON parsing only; no service or model call",
        "identity": {
            "model": {
                "model_id": policy["model"],
                "path": str(args.model_file),
                "sha256": model_sha,
                "bytes": args.model_file.stat().st_size,
            },
            "tokenizer": policy["tokenizer"] | {
                "bound_by_model_sha256": model_sha,
            },
            "chat_template": {
                "sha256": chat_sha,
                "length": len(chat_template),
                "source": "service_props.body_text.chat_template",
            },
            "server_binary": {
                "path": str(args.server_binary),
                "sha256": server_sha,
                "bytes": args.server_binary.stat().st_size,
            },
            "generation": policy["generation"],
            "chat_template_kwargs": policy["chat_template_kwargs"],
            "limits": policy["limits"],
            "base_url": policy["base_url"],
            "api_path": policy["api_path"],
        },
        "artifact_hashes": {
            args.runtime_policy.name: sha256_file(args.runtime_policy),
            args.plan_prompt.name: sha256_file(args.plan_prompt),
            args.consume_prompt.name: sha256_file(args.consume_prompt),
            args.output_schemas.name: sha256_file(args.output_schemas),
        },
        "source_identity": {
            args.model_pin.name: sha256_file(args.model_pin),
            args.service_props.name: sha256_file(args.service_props),
        },
        "checks": checks,
        "blockers": blockers,
    }
    write_json_lf(args.output, snapshot)
    print(json.dumps({
        "output": str(args.output),
        "status": snapshot["status"],
        "checks": checks,
        "blockers": blockers,
    }, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
