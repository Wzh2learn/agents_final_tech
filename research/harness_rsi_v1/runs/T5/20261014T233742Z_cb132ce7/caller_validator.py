#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
SHELL_METACHARACTERS = re.compile(r"[;&|`$><\n\r*?()[\]{}#]")
PROTOCOL_FREEZE = "282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b"
INTERFACES_SHA256 = "52d5ec1e3f6a54629ddd83ed1787f257f560dfbb8723e8325d7c390b7680d6ef"
OPERATIONS_SHA256 = "2cc368b69c8ae1687f3e85b8eab1181625f8f6816b82e5872d78c818113c9a03"
RUN_ID = "20261014T233742Z_cb132ce7"
REPOSITORY_ROOT = "/home/testuser/wzh/projects/agents_final_tech"


class ContractError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("FC_INPUT_NOT_JSON_OBJECT", f"duplicate JSON field: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ContractError("FC_INPUT_NOT_JSON_OBJECT", f"illegal JSON constant: {value}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)
    except ContractError:
        raise
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError("FC_INPUT_NOT_JSON_OBJECT", f"cannot parse {path.name}: {exc}") from exc


def require_fields(value: dict[str, Any], required: set[str], code: str = "FC_MISSING_REQUIRED_FIELD") -> None:
    missing = sorted(required - set(value))
    if missing:
        raise ContractError(code, f"missing required fields: {missing}")


def safe_relative_path(root: Path, value: Any, allowed_enum: list[str]) -> Path:
    if not isinstance(value, str):
        raise ContractError("FC_PARAMETER_TYPE_MISMATCH", f"path parameter must be string: {value!r}")
    if value not in allowed_enum:
        if SHELL_METACHARACTERS.search(value):
            raise ContractError("FC_SHELL_OR_COMMAND_INJECTION", f"shell or command text rejected: {value!r}")
        if Path(value).is_absolute() or ".." in Path(value).parts:
            raise ContractError("FC_ARBITRARY_PATH", f"absolute/traversal path rejected: {value!r}")
        raise ContractError("FC_ARBITRARY_PATH", f"unregistered path rejected: {value!r}")
    candidate = (root / value).resolve()
    root_resolved = root.resolve()
    if root_resolved not in candidate.parents and candidate != root_resolved:
        raise ContractError("FC_ARBITRARY_PATH", f"path escapes run root: {value!r}")
    if not candidate.is_file():
        raise ContractError("FC_ARBITRARY_PATH", f"fixture path is not a regular file: {value!r}")
    return candidate


def runtime_relative_path(runtime_root: Path, value: Any, allowed_enum: list[str]) -> Path:
    if not isinstance(value, str) or value not in allowed_enum or not value.startswith("runtime/"):
        raise ContractError("FC_ARBITRARY_PATH", f"unregistered runtime path rejected: {value!r}")
    candidate = (runtime_root / value.removeprefix("runtime/")).resolve()
    runtime_resolved = runtime_root.resolve()
    if runtime_resolved not in candidate.parents:
        raise ContractError("FC_ARBITRARY_PATH", f"runtime path escapes runtime root: {value!r}")
    if not candidate.is_file():
        raise ContractError("FC_ARBITRARY_PATH", f"runtime fixture is not a regular file: {value!r}")
    return candidate


def validate_parameters(op_id: str, parameters: Any, registry_entry: dict[str, Any], root: Path, runtime_root: Path) -> dict[str, Any]:
    if not isinstance(parameters, dict):
        raise ContractError("FC_PARAMETER_TYPE_MISMATCH", "parameters must be an object")
    specs = registry_entry["allowed_parameters"]
    if set(parameters) != set(specs):
        raise ContractError("FC_MISSING_REQUIRED_FIELD" if set(parameters) < set(specs) else "FC_PARAMETER_TYPE_MISMATCH", f"{op_id} parameter keys mismatch")
    resolved: dict[str, Any] = {}
    for name, spec in specs.items():
        value = parameters[name]
        parameter_type = spec["type"]
        if parameter_type == "relative_path_enum":
            if isinstance(value, str) and value.startswith("runtime/"):
                resolved[name] = runtime_relative_path(runtime_root, value, spec["enum"])
            else:
                resolved[name] = safe_relative_path(root, value, spec["enum"])
        elif parameter_type == "integer_range":
            if type(value) is not int:
                raise ContractError("FC_PARAMETER_TYPE_MISMATCH", f"{op_id}.{name} must be integer")
            if value < spec["minimum"] or value > spec["maximum"]:
                raise ContractError("FC_PARAMETER_OUT_OF_RANGE", f"{op_id}.{name}={value} outside bounds")
            resolved[name] = value
        elif parameter_type == "enum":
            if value not in spec["enum"]:
                raise ContractError("FC_PARAMETER_TYPE_MISMATCH", f"{op_id}.{name} not in enum")
            resolved[name] = value
        else:
            raise ContractError("FC_PARAMETER_TYPE_MISMATCH", f"unsupported registry parameter type: {parameter_type}")
    return resolved


def validate_delivery_fields(recipe: dict[str, Any], delivery_fields: Any) -> None:
    if not isinstance(delivery_fields, dict):
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "delivery_fields must be an object")
    categories = {"qualification", "audit", "execution", "scientific"}
    if set(delivery_fields) != categories:
        if "overall_pass" in delivery_fields:
            raise ContractError("FC_SINGLE_OVERALL_PASS_FORBIDDEN", "single overall PASS is forbidden")
        missing = sorted(categories - set(delivery_fields))
        if missing:
            raise ContractError("FC_MISSING_REQUIRED_FIELD", f"missing delivery categories: {missing}")
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "delivery categories must be exactly separated")
    contract = recipe["delivery_fields"]
    qualification = delivery_fields["qualification"]
    audit = delivery_fields["audit"]
    execution = delivery_fields["execution"]
    scientific = delivery_fields["scientific"]
    for value, name in [(qualification, "qualification"), (audit, "audit"), (execution, "execution"), (scientific, "scientific")]:
        if not isinstance(value, dict):
            raise ContractError("FC_MISSING_REQUIRED_FIELD", f"{name} must be an object")
    status_field = contract["qualification"]["status_field"]
    if qualification.get(status_field) not in contract["qualification"]["allowed_values"]:
        raise ContractError("FC_MISSING_REQUIRED_FIELD", f"qualification.{status_field} invalid")
    if set(qualification) != {status_field}:
        raise ContractError("FC_SINGLE_OVERALL_PASS_FORBIDDEN", "qualification class contains mixed fields")
    if not isinstance(audit.get("verification_level"), str) or audit["verification_level"] not in contract["audit"]["allowed_values"]:
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "audit.verification_level invalid")
    if not isinstance(audit.get("scope"), str) or not audit["scope"].strip():
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "audit.scope missing")
    if set(audit) != {"verification_level", "scope"}:
        raise ContractError("FC_SINGLE_OVERALL_PASS_FORBIDDEN", "audit class contains mixed fields")
    if execution.get("execution_status") not in contract["execution"]["allowed_values"]:
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "execution.execution_status invalid")
    if type(execution.get("operation_count")) is not int:
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "execution.operation_count invalid")
    if set(execution) != {"execution_status", "operation_count"}:
        raise ContractError("FC_SINGLE_OVERALL_PASS_FORBIDDEN", "execution class contains mixed fields")
    if scientific.get("scientific_status") not in contract["scientific"]["allowed_values"]:
        raise ContractError("FC_MISSING_REQUIRED_FIELD", "scientific.scientific_status invalid")
    if scientific.get("claim") is not None:
        raise ContractError("FC_SINGLE_OVERALL_PASS_FORBIDDEN", "scientific claim is forbidden for these recipes")
    if set(scientific) != {"scientific_status", "claim"}:
        raise ContractError("FC_SINGLE_OVERALL_PASS_FORBIDDEN", "scientific class contains mixed fields")


def execute_operation(op_id: str, parameters: dict[str, Any], registry_entry: dict[str, Any]) -> dict[str, Any]:
    target = Path(registry_entry["target"]["path"])
    declared_git_blob_id = registry_entry["target"].get("git_blob_id")
    if not isinstance(declared_git_blob_id, str) or not re.fullmatch(r"[0-9a-f]{40}", declared_git_blob_id):
        raise ContractError("FC_OPERATION_TARGET_IDENTITY_MISMATCH", "registered target lacks a canonical git_blob_id")
    target_raw = target.read_bytes()
    actual_git_blob_id = hashlib.sha1(b"blob " + str(len(target_raw)).encode("ascii") + b"\0" + target_raw).hexdigest()
    if actual_git_blob_id != declared_git_blob_id:
        raise ContractError("FC_OPERATION_TARGET_IDENTITY_MISMATCH", f"{op_id} target bytes do not match registered git_blob_id")
    if registry_entry["target"].get("required_cwd") != REPOSITORY_ROOT:
        raise ContractError("FC_RECIPE_OBJECT_MISMATCH", "registered operation does not pin the required repository cwd")
    if op_id == "OP-T4-R-DISPATCH-PRECHECK":
        command = [
            "/usr/bin/bash",
            str(target),
            "--watcher",
            str(parameters["watcher_path"]),
            "--tick-marker",
            str(parameters["tick_path"]),
            "--max-tick-age-min",
            str(parameters["max_tick_age_minutes"]),
        ]
    elif op_id == "OP-T4-R-SUMMARY-GUARD-CHECK":
        command = ["/usr/bin/bash", str(target), "check", str(parameters["markdown_path"])]
    elif op_id == "OP-T4-R-SUMMARY-GUARD-DERIVE":
        command = ["/usr/bin/bash", str(target), str(parameters["base_markdown_path"])]
    else:
        raise ContractError("FC_UNREGISTERED_OPERATION", f"no execution mapping for {op_id}")
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    guard_match = re.search(r"^guard_rc=([0-9]+)$", completed.stdout, re.MULTILINE)
    target_exit_code = int(guard_match.group(1)) if op_id == "OP-T4-R-SUMMARY-GUARD-DERIVE" and guard_match else completed.returncode
    result = {
        "op_id": op_id,
        "wrapper_exit_code": completed.returncode,
        "target_exit_code": target_exit_code,
        "duration_ms": duration_ms,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "semantic": "target tool exit code; for derive this is guard_rc, not wrapper exit" if op_id == "OP-T4-R-SUMMARY-GUARD-DERIVE" else "wrapper and target exit code coincide",
    }
    expected = registry_entry.get("expected_wrapper_exit_code", 0)
    expected_target = registry_entry.get("expected_target_exit_code", 0)
    if completed.returncode != expected or target_exit_code != expected_target:
        raise ContractError("FC_OPERATION_TARGET_FAILURE", f"{op_id} wrapper={completed.returncode} target={target_exit_code}; expected {expected}/{expected_target}")
    return result


def validate_call(call: dict[str, Any], interfaces: dict[str, Any], registry: dict[str, Any], run_root: Path, runtime_root: Path) -> dict[str, Any]:
    base_required = {"schema", "recipe_id", "caller_context", "run_id", "protocol_freeze_sha256", "operations", "delivery_fields"}
    require_fields(call, base_required)
    if call["schema"] != "jinrong_t5_recipe_call_v1":
        raise ContractError("FC_INPUT_NOT_JSON_OBJECT", "unexpected call schema")
    if call["run_id"] != RUN_ID:
        raise ContractError("FC_HASH_BINDING_MISMATCH", "run_id mismatch")
    if call["protocol_freeze_sha256"] != PROTOCOL_FREEZE:
        raise ContractError("FC_HASH_BINDING_MISMATCH", "protocol freeze mismatch")
    recipes = {recipe["recipe_id"]: recipe for recipe in interfaces["recipes"]}
    recipe = recipes.get(call["recipe_id"])
    if recipe is None:
        raise ContractError("FC_RECIPE_OBJECT_MISMATCH", "unknown recipe id")
    is_delivery = recipe["single_object_declaration"]["object_id"] == "evidence_delivery_recipe"
    expected_context = "EVIDENCE_DELIVERY_RECEIPT_MANIFEST_VALIDATION" if is_delivery else "LOOP_D_RUN_PACKAGE_PRECHECK"
    if is_delivery:
        caller_context = call["caller_context"]
        if not isinstance(caller_context, dict) or "expected_artifact_sha256" not in caller_context:
            raise ContractError("FC_ARTIFACT_NOT_PINNED", "delivery caller_context must provide an external expected_artifact_sha256 pin")
        if set(caller_context) != {"context", "expected_artifact_sha256"} or caller_context.get("context") != expected_context:
            raise ContractError("FC_RECIPE_OBJECT_MISMATCH", "delivery caller context does not match recipe object")
        expected_pin = caller_context["expected_artifact_sha256"]
        if not isinstance(expected_pin, str) or not HEX64.match(expected_pin):
            raise ContractError("FC_ARTIFACT_NOT_PINNED", "external summary pin is absent or malformed")
    elif call["caller_context"] != expected_context:
        raise ContractError("FC_RECIPE_OBJECT_MISMATCH", "caller context does not match recipe object")
    if not isinstance(call["operations"], list):
        raise ContractError("FC_PARAMETER_TYPE_MISMATCH", "operations must be an array")
    expected_op_ids = [entry["op_id"] for entry in recipe["operations"]]
    actual_op_ids = [entry.get("op_id") if isinstance(entry, dict) else None for entry in call["operations"]]
    if actual_op_ids != expected_op_ids:
        for op_id in actual_op_ids:
            if op_id not in {item["op_id"] for item in registry["operations"]}:
                raise ContractError("FC_UNREGISTERED_OPERATION", f"unregistered operation: {op_id!r}")
        raise ContractError("FC_RECIPE_OBJECT_MISMATCH", "operation ids/order do not match recipe")
    registry_map = {entry["op_id"]: entry for entry in registry["operations"]}
    resolved_operations = []
    for index, operation in enumerate(call["operations"]):
        if set(operation) != {"op_id", "parameters"}:
            raise ContractError("FC_MISSING_REQUIRED_FIELD", f"operation {index} keys mismatch")
        op_id = operation["op_id"]
        if op_id not in registry_map:
            raise ContractError("FC_UNREGISTERED_OPERATION", f"unregistered operation: {op_id}")
        resolved = validate_parameters(op_id, operation["parameters"], registry_map[op_id], run_root, runtime_root)
        resolved_operations.append({"op_id": op_id, "parameters": resolved, "registry_entry": registry_map[op_id]})
    validate_delivery_fields(recipe, call["delivery_fields"])
    if is_delivery:
        package_required = {"package_ref", "package_sha256", "summary_text", "summary_sha256"}
        require_fields(call, package_required)
        package_path = safe_relative_path(run_root, call["package_ref"], ["recipe_fixtures/delivery_payload.json"])
        if not isinstance(call["package_sha256"], str) or not HEX64.match(call["package_sha256"]):
            raise ContractError("FC_HASH_BINDING_MISMATCH", "package_sha256 must be 64 lowercase hex")
        actual_package_sha256 = hashlib.sha256(package_path.read_bytes()).hexdigest()
        if call["package_sha256"] != actual_package_sha256:
            raise ContractError("FC_HASH_BINDING_MISMATCH", "package bytes do not match declared SHA-256")
        if not isinstance(call["summary_text"], str) or not isinstance(call["summary_sha256"], str) or not HEX64.match(call["summary_sha256"]):
            raise ContractError("FC_FORGED_SUMMARY_MISMATCH", "summary text/hash shape invalid")
        actual_summary_sha256 = hashlib.sha256(call["summary_text"].encode("utf-8")).hexdigest()
        if call["summary_sha256"] != actual_summary_sha256:
            raise ContractError("FC_FORGED_SUMMARY_MISMATCH", "runtime-derived summary does not match declared SHA-256")
        if actual_summary_sha256 != expected_pin:
            raise ContractError("FC_PIN_MISMATCH", "declared/measured summary SHA-256 does not match the caller's trusted external pin")
    operation_results = []
    for operation in resolved_operations:
        operation_results.append(execute_operation(operation["op_id"], operation["parameters"], operation["registry_entry"]))
    return {
        "validation_status": "ACCEPTED_WITHIN_SCOPE",
        "recipe_id": recipe["recipe_id"],
        "single_object_id": recipe["single_object_declaration"]["object_id"],
        "fail_closed_code": None,
        "operation_results": operation_results,
        "target_execution_performed": True,
        "scientific_status": call["delivery_fields"]["scientific"]["scientific_status"],
        "scientific_claim": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--interfaces", required=True)
    parser.add_argument("--operations", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--call-stdin", action="store_true")
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    runtime_root = Path(args.runtime_root).resolve()
    if runtime_root == run_root or run_root in runtime_root.parents:
        raise SystemExit("runtime root must be outside the delivered run tree")
    base_result = {
        "validation_status": "REJECTED",
        "recipe_id": None,
        "single_object_id": None,
        "fail_closed_code": None,
        "error_detail": None,
        "operation_results": [],
        "target_execution_performed": False,
        "scientific_status": None,
        "scientific_claim": None,
    }
    try:
        interfaces_path = Path(args.interfaces).resolve()
        registry_path = Path(args.operations).resolve()
        if hashlib.sha256(interfaces_path.read_bytes()).hexdigest() != INTERFACES_SHA256:
            raise ContractError("FC_INPUT_IDENTITY_MISMATCH", "interfaces bytes do not match the embedded SHA-256 pin")
        if hashlib.sha256(registry_path.read_bytes()).hexdigest() != OPERATIONS_SHA256:
            raise ContractError("FC_INPUT_IDENTITY_MISMATCH", "operations bytes do not match the embedded SHA-256 pin")
        interfaces = load_json(interfaces_path)
        registry = load_json(registry_path)
        raw = sys.stdin.read()
        try:
            call = json.loads(raw, object_pairs_hook=strict_object, parse_constant=reject_constant)
        except ContractError:
            raise
        except json.JSONDecodeError as exc:
            raise ContractError("FC_INPUT_NOT_JSON_OBJECT", f"call is not JSON: {exc}") from exc
        if not isinstance(call, dict):
            raise ContractError("FC_INPUT_NOT_JSON_OBJECT", "call must be a JSON object")
        result = validate_call(call, interfaces, registry, run_root, runtime_root)
        exit_code = 0
    except ContractError as exc:
        result = {**base_result, "fail_closed_code": exc.code, "error_detail": exc.detail}
        exit_code = 1
    except (OSError, subprocess.SubprocessError, KeyError, TypeError, ValueError) as exc:
        result = {**base_result, "fail_closed_code": "FC_INPUT_NOT_JSON_OBJECT", "error_detail": f"caller validation internal fail-closed: {type(exc).__name__}: {exc}"}
        exit_code = 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
