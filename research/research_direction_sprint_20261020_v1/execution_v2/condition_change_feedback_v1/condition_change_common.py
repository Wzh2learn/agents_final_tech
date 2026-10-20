#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
PACKAGE_NAME = "condition_change_feedback_v1"
TASK_ID = "condition_change_feedback_v1"
SUPPORTED_PYTHON_VERSIONS = {"3.11", "3.12"}
EVIDENCE_IDENTITY = "DEV_ONLY_CONTROLLED_MECHANISM"

SOURCE_POLICY_PATH = PACKAGE_DIR / "policy_spec_v1.source.json"
SOURCE_CASES_PATH = PACKAGE_DIR / "case_inputs_v1.source.json"
V1_SOURCE_POLICY_PATH = SOURCE_POLICY_PATH
V1_SOURCE_CASES_PATH = SOURCE_CASES_PATH
REVISION_SOURCE_PATH = PACKAGE_DIR / "condition_change_feedback_v2_revision.source.json"
SOURCE_POLICY_V2_PATH = PACKAGE_DIR / "policy_spec_v2.source.json"
SOURCE_CASES_V2_PATH = PACKAGE_DIR / "case_inputs_v2.source.json"
SCHEMA_V1_PATH = PACKAGE_DIR / "TASK_TOOL_SCHEMA.json"
SCHEMA_PATH = PACKAGE_DIR / "TASK_TOOL_SCHEMA_V2.json"
POLICY_V1_PATH = PACKAGE_DIR / "POLICY_SPEC_V1.json"
FACTS_V1_PATH = PACKAGE_DIR / "EVIDENCE_FACTS_V1.json"
ACTOR_TASKS_V1_PATH = PACKAGE_DIR / "ACTOR_TASKS_V1.json"
REFERENCE_TASKS_V1_PATH = PACKAGE_DIR / "REFERENCE_TASKS_V1.json"
INPUT_MANIFEST_V1_PATH = PACKAGE_DIR / "FROZEN_INPUT_MANIFEST.json"
PROBE_FIXTURES_V1_PATH = PACKAGE_DIR / "FEEDBACK_PROBE_FIXTURES_V1.json"
PROBE_FREEZE_MANIFEST_V1_PATH = PACKAGE_DIR / "PROBE_FREEZE_MANIFEST.json"
PROBE_RUN_MANIFEST_V1_PATH = PACKAGE_DIR / "PROBE_RUN_MANIFEST.json"
PROBE_RESULTS_V1_PATH = PACKAGE_DIR / "FEEDBACK_PROBE_RESULTS_V1.json"
PROBE_SUMMARY_V1_PATH = PACKAGE_DIR / "FEEDBACK_PROBE_SUMMARY_V1.json"
MACHINE_VERIFICATION_V1_PATH = PACKAGE_DIR / "MACHINE_VERIFICATION.json"
POLICY_PATH = PACKAGE_DIR / "POLICY_SPEC_V2.json"
FACTS_PATH = PACKAGE_DIR / "EVIDENCE_FACTS_V2.json"
ACTOR_TASKS_PATH = PACKAGE_DIR / "ACTOR_TASKS_V2.json"
REFERENCE_TASKS_PATH = PACKAGE_DIR / "REFERENCE_TASKS_V2.json"
INPUT_MANIFEST_PATH = PACKAGE_DIR / "FROZEN_INPUT_MANIFEST_V2.json"
PROBE_FIXTURES_PATH = PACKAGE_DIR / "FEEDBACK_PROBE_FIXTURES_V2.json"
PROBE_FREEZE_MANIFEST_PATH = PACKAGE_DIR / "PROBE_FREEZE_MANIFEST_V2.json"
PROBE_RUN_MANIFEST_PATH = PACKAGE_DIR / "PROBE_RUN_MANIFEST_V2.json"
PROBE_RESULTS_PATH = PACKAGE_DIR / "FEEDBACK_PROBE_RESULTS_V2.json"
PROBE_SUMMARY_PATH = PACKAGE_DIR / "FEEDBACK_PROBE_SUMMARY_V2.json"
MACHINE_VERIFICATION_PATH = PACKAGE_DIR / "MACHINE_VERIFICATION_V2.json"
RETURN_PATH = PACKAGE_DIR / "RETURN.md"

V1_FROZEN_FILES = (
    V1_SOURCE_POLICY_PATH,
    V1_SOURCE_CASES_PATH,
    SCHEMA_V1_PATH,
    POLICY_V1_PATH,
    FACTS_V1_PATH,
    ACTOR_TASKS_V1_PATH,
    REFERENCE_TASKS_V1_PATH,
    INPUT_MANIFEST_V1_PATH,
    PROBE_FIXTURES_V1_PATH,
    PROBE_FREEZE_MANIFEST_V1_PATH,
    PROBE_RUN_MANIFEST_V1_PATH,
    PROBE_RESULTS_V1_PATH,
    PROBE_SUMMARY_V1_PATH,
    MACHINE_VERIFICATION_V1_PATH,
)

REQUEST_ACCOUNTING = {
    "model_requests": 0,
    "judge_calls": 0,
    "training_calls": 0,
    "network_requests": 0,
    "service_requests": 0,
    "production_memory_writes": 0,
}


def canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            separators=(",", ": "),
        )
        + "\n"
    ).encode("utf-8")


def canonical_json_text(payload: Any) -> str:
    return canonical_json(payload).decode("utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_bytes(canonical_json(payload))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def strict_validate(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    root = schema.get("root")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise ValueError(f"unsupported schema reference at {path}: {ref}")
        definition_name = ref.removeprefix("#/$defs/")
        definitions = (root or {}).get("$defs", {})
        if definition_name not in definitions:
            raise ValueError(f"missing schema definition at {path}: {ref}")
        strict_validate(
            instance,
            {**definitions[definition_name], "root": {"$defs": definitions}},
            path,
        )
        return

    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(instance, dict):
            raise TypeError(f"{path} must be an object")
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            raise ValueError(f"{path} missing required keys: {missing}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(instance) - set(properties))
            if unknown:
                raise ValueError(f"{path} has unknown keys: {unknown}")
        for key, value in instance.items():
            if key in properties:
                strict_validate(
                    value,
                    {**properties[key], "root": root},
                    f"{path}.{key}",
                )
    elif schema_type == "array":
        if not isinstance(instance, list):
            raise TypeError(f"{path} must be an array")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, value in enumerate(instance):
                strict_validate(
                    value,
                    {**item_schema, "root": root},
                    f"{path}[{index}]",
                )
    elif schema_type == "string":
        if not isinstance(instance, str):
            raise TypeError(f"{path} must be a string")
        if "enum" in schema and instance not in schema["enum"]:
            raise ValueError(f"{path} must be one of {schema['enum']}")
        if "pattern" in schema:
            import re

            if not re.fullmatch(schema["pattern"], instance):
                raise ValueError(f"{path} does not match {schema['pattern']}")
    elif schema_type == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            raise TypeError(f"{path} must be an integer")
    elif schema_type == "number":
        if not isinstance(instance, (int, float)) or isinstance(instance, bool):
            raise TypeError(f"{path} must be a number")
    elif schema_type == "boolean":
        if not isinstance(instance, bool):
            raise TypeError(f"{path} must be a boolean")
    elif schema_type is not None:
        raise ValueError(f"unsupported schema type at {path}: {schema_type}")


def load_strict_schema() -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    strict_validate(schema, {"type": "object"})
    return schema


def validate_against_definition(instance: Any, definition_name: str) -> None:
    schema = load_strict_schema()
    root = {"$defs": schema["$defs"]}
    strict_validate(
        instance,
        {"$ref": f"#/$defs/{definition_name}", "root": root},
        f"$/{definition_name}",
    )
