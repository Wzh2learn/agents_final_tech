"""Deterministic controls for dependency-consumption verification."""

from __future__ import annotations

import ast
import copy
import json
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


UTF8_SAMPLE = b"\xc3\xa9"
LEGACY_SAMPLE = b"\xe9"
EXPECTED_TEXT = "\u00e9"


@dataclass
class ProbeResult:
    output: str | None
    error: str | None
    target_calls: int
    old_calls: int
    target_result_consumed: bool
    basic_behavior_pass: bool
    extended_behavior_pass: bool


def find_decode_function(code: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise ValueError(f"function_not_found:{name}")


def extract_function(code: str, name: str) -> str:
    node = copy.deepcopy(find_decode_function(code, name))
    node.decorator_list = []
    node.name = "decode_probe"
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    return ast.unparse(module)


def run_decode(
    code: str,
    function_name: str = "_decode_data",
    target_result_encoding: str = "latin-1",
) -> ProbeResult:
    target_calls = 0
    old_calls = 0

    def target_detect(data: bytes) -> dict[str, str]:
        nonlocal target_calls
        target_calls += 1
        return {
            "encoding": "utf-8" if data == UTF8_SAMPLE else target_result_encoding
        }

    def old_detect(_data: bytes) -> dict[str, str]:
        nonlocal old_calls
        old_calls += 1
        return {"encoding": "utf-8"}

    target = types.SimpleNamespace(detect=target_detect)
    old = types.SimpleNamespace(detect=old_detect)

    class FakeImportlib:
        @staticmethod
        def import_module(name: str) -> types.SimpleNamespace:
            if name == "cchardet":
                return target
            if name == "chardet":
                return old
            raise ImportError(name)

    namespace: dict[str, Any] = {
        "cchardet": target,
        "importlib": FakeImportlib,
    }
    parsed = ast.parse(code)
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "cchardet":
                    namespace[alias.asname or alias.name] = target
                elif alias.name == "importlib":
                    namespace[alias.asname or alias.name] = FakeImportlib
    exec(compile(extract_function(code, function_name), "<candidate>", "exec"), namespace)
    decode: Callable[[bytes], str] = namespace["decode_probe"]

    outputs: list[str | None] = []
    errors: list[str | None] = []
    before_target = target_calls
    for sample in (UTF8_SAMPLE, LEGACY_SAMPLE):
        try:
            value = decode(sample)
            outputs.append(value if isinstance(value, str) else None)
            errors.append(None if isinstance(value, str) else "non_string_output")
        except Exception as exc:
            outputs.append(None)
            errors.append(f"{type(exc).__name__}:{exc}")

    target_calls_in_probe = target_calls - before_target
    target_result_consumed = (
        target_calls_in_probe > 0
        and outputs[0] == EXPECTED_TEXT
        and outputs[1] == EXPECTED_TEXT
    )
    return ProbeResult(
        output=outputs[1],
        error=errors[1],
        target_calls=target_calls_in_probe,
        old_calls=old_calls,
        target_result_consumed=target_result_consumed,
        basic_behavior_pass=outputs[0] == EXPECTED_TEXT and errors[0] is None,
        extended_behavior_pass=all(
            value == EXPECTED_TEXT and error is None
            for value, error in zip(outputs, errors)
        ),
    )


def static_contract(code: str) -> dict[str, Any]:
    tree = ast.parse(code)
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "import_module":
                imported["importlib.import_module"] = "importlib.import_module"
    target_imported = any(
        value == "cchardet" or value.startswith("cchardet.") or value == "importlib.import_module"
        for value in imported.values()
    )
    source_imported = any(
        value == "chardet" or value.startswith("chardet.")
        for value in imported.values()
    )
    calls_target = False
    calls_old = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr == "detect":
                if isinstance(func.value, ast.Name):
                    if func.value.id in {"cchardet", "cc", "target"}:
                        calls_target = True
                    if func.value.id in {"chardet", "old"}:
                        calls_old = True
        elif isinstance(func, ast.Name) and func.id == "import_module":
            calls_target = True
    return {
        "syntax_valid": True,
        "target_imported": target_imported,
        "source_imported": source_imported,
        "target_call_present": calls_target,
        "old_call_present": calls_old,
        "static_pass": target_imported and calls_target and not source_imported and not calls_old,
    }


CONTROLS: list[dict[str, Any]] = [
    {
        "id": "valid_alias",
        "label": "VALID",
        "kind": "synthetic_control",
        "code": "import cchardet as cc\n\ndef _decode_data(data):\n    enc = cc.detect(data)['encoding']\n    return data.decode(enc or 'utf-8')",
    },
    {
        "id": "valid_wrapper",
        "label": "VALID",
        "kind": "synthetic_control",
        "code": "import cchardet\n\ndef _decode_data(data):\n    def detect_target(sample):\n        return cchardet.detect(sample)['encoding']\n    return data.decode(detect_target(data) or 'utf-8')",
    },
    {
        "id": "valid_dynamic_import",
        "label": "VALID",
        "kind": "synthetic_control",
        "code": "import importlib\n\ndef _decode_data(data):\n    target = importlib.import_module('cchardet')\n    return data.decode(target.detect(data)['encoding'] or 'utf-8')",
    },
    {
        "id": "invalid_dead_target_call",
        "label": "INVALID",
        "kind": "synthetic_control",
        "code": "import cchardet\n\ndef _decode_data(data):\n    if False:\n        cchardet.detect(data)\n    return data.decode('utf-8')",
    },
    {
        "id": "invalid_unused_target_result",
        "label": "INVALID",
        "kind": "synthetic_control",
        "code": "import cchardet\n\ndef _decode_data(data):\n    cchardet.detect(data)\n    return data.decode('utf-8')",
    },
    {
        "id": "invalid_swallowed_old_fallback",
        "label": "INVALID",
        "kind": "synthetic_control",
        "code": "def _decode_data(data):\n    try:\n        enc = chardet.detect(data)['encoding']\n    except Exception:\n        enc = None\n    return data.decode(enc or 'utf-8')",
    },
    {
        "id": "valid_equivalent_adapter",
        "label": "VALID",
        "kind": "synthetic_control",
        "code": "import cchardet\n\ndef _decode_data(data):\n    def adapter_detect(sample):\n        return cchardet.detect(sample)\n    return data.decode(adapter_detect(data)['encoding'] or 'utf-8')",
    },
]


def load_natural_candidates() -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parent
    result_path = (
        root.parent
        / "research_portfolio_v2"
        / "pymigbench_external_change_v1"
        / "ntripbrowser_qualification_v2"
        / "PROBE_RESULT.json"
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    rows = []
    for row in result["rows"]:
        rows.append(
            {
                "id": f"natural_{row['arm'].lower()}",
                "label": (
                    "VALID"
                    if row["arm"] in {"PROSE_CHANGE_FACTS", "STRUCTURED_CHANGE_FACTS"}
                    else "INVALID"
                ),
                "kind": "natural_model_candidate",
                "code": row["code"],
            }
        )
    return rows


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    static = static_contract(case["code"])
    runtime = run_decode(case["code"])
    reference = case["label"]
    hybrid_pass = bool(
        runtime.target_result_consumed
        and runtime.extended_behavior_pass
        and not static["source_imported"]
    )
    return {
        **case,
        "static": static,
        "runtime": {
            "target_calls": runtime.target_calls,
            "old_calls": runtime.old_calls,
            "target_result_consumed": runtime.target_result_consumed,
            "basic_behavior_pass": runtime.basic_behavior_pass,
            "extended_behavior_pass": runtime.extended_behavior_pass,
            "legacy_output": runtime.output,
            "legacy_error": runtime.error,
        },
        "judgments": {
            "basic_behavior": runtime.basic_behavior_pass,
            "static_contract": static["static_pass"],
            "runtime_consumption": runtime.target_result_consumed,
            "hybrid": hybrid_pass,
        },
        "reference": reference,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    methods = ["basic_behavior", "static_contract", "runtime_consumption", "hybrid"]
    summary = {}
    for method in methods:
        false_accept = 0
        false_reject = 0
        correct = 0
        for row in rows:
            predicted = row["judgments"][method]
            valid = row["reference"] == "VALID"
            if predicted and not valid:
                false_accept += 1
            elif not predicted and valid:
                false_reject += 1
            else:
                correct += 1
        summary[method] = {
            "correct": correct,
            "false_accept": false_accept,
            "false_reject": false_reject,
            "n": len(rows),
        }
    return summary


def main() -> int:
    rows = [evaluate_case(case) for case in load_natural_candidates() + CONTROLS]
    payload = {
        "schema": "g2_dependency_consumption_control_results_v1",
        "date": "2026-10-22",
        "evidence_identity": "NATURAL_CANDIDATES_PLUS_DEV_ONLY_SYNTHETIC_CONTROLS",
        "rows": rows,
        "summary": summarize(rows),
        "nonclaims": [
            "Synthetic controls are mechanism probes, not natural error rates.",
            "Runtime consumption evidence here is an isolated decode probe, not a full application trace.",
            "The verifier does not establish general semantic equivalence.",
        ],
    }
    out = Path(__file__).resolve().parent / "G2_CONTROL_RESULTS.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
