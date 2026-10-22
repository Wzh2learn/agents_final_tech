"""Task-scoped migration completion verifier with adversarial consumption probes."""

from __future__ import annotations

import argparse
import ast
import copy
import importlib
import io
import json
import os
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


UTF8_SAMPLE = b"\xc3\xa9"
LEGACY_SAMPLE = b"\xe9"
SENTINEL_SAMPLE = b"AB"


@dataclass
class ProbeResult:
    status: str
    outputs: list[str | None]
    errors: list[str | None]
    target_calls: int
    source_calls: int
    basic_behavior_pass: bool
    extended_behavior_pass: bool
    target_result_consumed: bool | None
    detail: str


def _extract_function(code: str, name: str) -> str:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            node = copy.deepcopy(node)
            node.decorator_list = []
            node.name = "probe_target"
            module = ast.Module(body=[node], type_ignores=[])
            ast.fix_missing_locations(module)
            return ast.unparse(module)
    raise ValueError(f"function_not_found:{name}")


def _execute_probe(
    code: str,
    function_name: str,
    namespace: dict[str, Any],
    samples: Iterable[tuple[bytes, str | None, str | None]],
) -> ProbeResult:
    exec(compile(_extract_function(code, function_name), "<candidate>", "exec"), namespace)
    target = namespace["probe_target"]
    outputs: list[str | None] = []
    errors: list[str | None] = []
    target_calls = int(namespace.get("__target_calls__", 0))
    source_calls = int(namespace.get("__source_calls__", 0))
    for sample, _expected, _sentinel in samples:
        try:
            value = target(io.BytesIO([sample]))
            outputs.append(value if isinstance(value, str) else None)
            errors.append(None if isinstance(value, str) else "non_string_output")
        except Exception as exc:
            outputs.append(None)
            errors.append(f"{type(exc).__name__}:{exc}")
    return ProbeResult(
        status="OK",
        outputs=outputs,
        errors=errors,
        target_calls=target_calls,
        source_calls=source_calls,
        basic_behavior_pass=False,
        extended_behavior_pass=False,
        target_result_consumed=None,
        detail="",
    )


def run_detect_dict(code: str, function_name: str = "_decode_data") -> ProbeResult:
    calls = {"target": 0, "source": 0}

    def target_detect(data: bytes) -> dict[str, str]:
        calls["target"] += 1
        if data == UTF8_SAMPLE:
            return {"encoding": "utf-8"}
        if data == LEGACY_SAMPLE:
            return {"encoding": "latin-1"}
        return {"encoding": "utf-16-le"}

    def source_detect(data: bytes) -> dict[str, str]:
        calls["source"] += 1
        return {"encoding": "utf-8"}

    target = types.SimpleNamespace(detect=target_detect)
    source = types.SimpleNamespace(detect=source_detect)

    class FakeImportlib:
        @staticmethod
        def import_module(name: str) -> types.SimpleNamespace:
            if name == "cchardet":
                return target
            if name == "chardet":
                return source
            raise ImportError(name)

    namespace: dict[str, Any] = {
        "cchardet": target,
        "chardet": source,
        "importlib": FakeImportlib,
    }
    parsed = ast.parse(code)
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "cchardet":
                    namespace[alias.asname or alias.name] = target
                elif alias.name == "chardet":
                    namespace[alias.asname or alias.name] = source
                elif alias.name == "importlib":
                    namespace[alias.asname or alias.name] = FakeImportlib

    exec(compile(_extract_function(code, function_name), "<candidate>", "exec"), namespace)
    decode = namespace["probe_target"]
    outputs: list[str | None] = []
    errors: list[str | None] = []
    for sample in (UTF8_SAMPLE, LEGACY_SAMPLE, SENTINEL_SAMPLE):
        try:
            value = decode(sample)
            outputs.append(value if isinstance(value, str) else None)
            errors.append(None if isinstance(value, str) else "non_string_output")
        except Exception as exc:
            outputs.append(None)
            errors.append(f"{type(exc).__name__}:{exc}")

    expected = [EXPECTED_UTF8, EXPECTED_UTF8, SENTINEL_SAMPLE.decode("utf-16-le")]
    basic = outputs[0] == expected[0] and errors[0] is None
    extended = all(value == want and error is None for value, want, error in zip(outputs, expected, errors))
    sentinel_tracks_target = outputs[2] == expected[2] and outputs[2] != SENTINEL_SAMPLE.decode("utf-8")
    consumed: bool | None = calls["target"] > 0 and sentinel_tracks_target
    if calls["target"] == 0 and calls["source"] == 0:
        consumed = None
    return ProbeResult(
        status="OK",
        outputs=outputs,
        errors=errors,
        target_calls=calls["target"],
        source_calls=calls["source"],
        basic_behavior_pass=basic,
        extended_behavior_pass=extended,
        target_result_consumed=consumed,
        detail="sentinel output must follow the injected target encoding",
    )


EXPECTED_UTF8 = "\u00e9"


class FakeTargetDetector:
    instances: list["FakeTargetDetector"] = []

    def __init__(self) -> None:
        self.data = b""
        self.result: dict[str, str | None] = {"encoding": "utf-8"}
        self.done = False
        self.__class__.instances.append(self)

    def feed(self, data: bytes) -> None:
        self.data += bytes(data)

    def close(self) -> None:
        if self.data == b"ascii\n":
            self.result = {"encoding": "ascii"}
        elif self.data == b"AB":
            self.result = {"encoding": "utf-16-le"}
        else:
            self.result = {"encoding": "latin-1"}
        self.done = True


class FakeSourceDetector(FakeTargetDetector):
    instances: list["FakeSourceDetector"] = []

    def close(self) -> None:
        if self.data == b"ascii\n":
            self.result = {"encoding": "ascii"}
        elif self.data == b"AB":
            self.result = {"encoding": "iso-8859-1"}
        else:
            self.result = {"encoding": "cp1252"}
        self.done = True


def run_universal_detector(code: str, function_name: str = "detect_encoding") -> ProbeResult:
    FakeTargetDetector.instances.clear()
    FakeSourceDetector.instances.clear()

    class FakeImportlib:
        @staticmethod
        def import_module(name: str) -> types.SimpleNamespace:
            if name == "cchardet":
                return types.SimpleNamespace(UniversalDetector=FakeTargetDetector)
            if name == "chardet":
                return types.SimpleNamespace(UniversalDetector=FakeSourceDetector)
            raise ImportError(name)

    namespace: dict[str, Any] = {
        "UniversalDetector": FakeTargetDetector,
        "SourceDetector": FakeSourceDetector,
        "importlib": FakeImportlib,
    }
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.ImportFrom) and node.module in {"cchardet", "chardet"}:
            for alias in node.names:
                if alias.name == "UniversalDetector":
                    namespace[alias.asname or alias.name] = (
                        FakeSourceDetector if node.module == "chardet" else FakeTargetDetector
                    )

    exec(compile(_extract_function(code, function_name), "<candidate>", "exec"), namespace)
    probe = namespace["probe_target"]
    inputs = ([b"latin\n"], [b"ascii\n"], [b"AB"])
    outputs: list[str | None] = []
    errors: list[str | None] = []
    for lines in inputs:
        try:
            value = probe(iter(lines))
            outputs.append(value if isinstance(value, str) else None)
            errors.append(None if isinstance(value, str) else "non_string_output")
        except Exception as exc:
            outputs.append(None)
            errors.append(f"{type(exc).__name__}:{exc}")
    expected = ["latin-1", "utf-8", "utf-16-le"]
    basic = outputs[0] == expected[0] and errors[0] is None
    extended = all(value == want and error is None for value, want, error in zip(outputs, expected, errors))
    consumed = (
        len(FakeTargetDetector.instances) > 0 and outputs[2] == expected[2]
        if FakeTargetDetector.instances
        else None
    )
    return ProbeResult(
        status="OK",
        outputs=outputs,
        errors=errors,
        target_calls=len(FakeTargetDetector.instances),
        source_calls=len(FakeSourceDetector.instances),
        basic_behavior_pass=basic,
        extended_behavior_pass=extended,
        target_result_consumed=consumed,
        detail="UniversalDetector.close result must control the returned encoding",
    )


def static_contract(code: str, setup_code: str = "") -> dict[str, Any]:
    combined = code + "\n" + setup_code
    tree = ast.parse(code)
    imported_target = False
    imported_source = False
    target_call = False
    source_call = False
    result_flow = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_target |= alias.name == "cchardet" or alias.name.startswith("cchardet.")
                imported_source |= alias.name == "chardet" or alias.name.startswith("chardet.")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imported_target |= module == "cchardet" or module.startswith("cchardet.")
            imported_source |= module == "chardet" or module.startswith("chardet.")
        elif isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            target_call |= "cchardet" in name or name.endswith("UniversalDetector")
            source_call |= "chardet" in name and "cchardet" not in name
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and node.value is not None:
            result_flow = True
    target_declared = bool(re_search_dependency(setup_code, "cchardet"))
    source_declared = bool(re_search_dependency(setup_code, "chardet"))
    return {
        "syntax_valid": True,
        "target_imported": imported_target,
        "source_imported": imported_source,
        "target_call_present": target_call,
        "source_call_present": source_call,
        "result_return_present": result_flow,
        "target_declared": target_declared,
        "source_declared": source_declared,
        "static_pass": bool(
            imported_target
            and target_call
            and not imported_source
            and not source_call
            and (not setup_code or (target_declared and not source_declared))
        ),
    }


def re_search_dependency(text: str, dependency: str) -> bool:
    return dependency in text.replace("cchardet", "CCHARDET_TARGET") if dependency == "chardet" else dependency in text


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    methods = ["basic_behavior", "enhanced_behavior", "static_contract", "runtime_consumption", "hybrid"]
    summary: dict[str, Any] = {}
    for method in methods:
        correct = false_accept = false_reject = unresolved = 0
        for row in rows:
            if row["reference"] == "UNRESOLVED":
                unresolved += 1
                continue
            predicted = bool(row["judgments"][method])
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
            "unresolved": unresolved,
            "n": len(rows),
        }
    return summary


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    runtime = (
        run_universal_detector(case["code"], case.get("function_name", "detect_encoding"))
        if case["probe_kind"] == "universal_detector"
        else run_detect_dict(case["code"], case.get("function_name", "_decode_data"))
    )
    static = static_contract(case["code"], case.get("setup_code", ""))
    hybrid = bool(
        runtime.extended_behavior_pass
        and runtime.target_result_consumed is True
        and not static["source_imported"]
        and not static["source_call_present"]
    )
    if runtime.target_result_consumed is None:
        hybrid = False
    return {
        **case,
        "static": static,
        "runtime": {
            "status": runtime.status,
            "outputs": runtime.outputs,
            "errors": runtime.errors,
            "target_calls": runtime.target_calls,
            "source_calls": runtime.source_calls,
            "target_result_consumed": runtime.target_result_consumed,
            "basic_behavior_pass": runtime.basic_behavior_pass,
            "extended_behavior_pass": runtime.extended_behavior_pass,
            "detail": runtime.detail,
        },
        "judgments": {
            "basic_behavior": runtime.basic_behavior_pass,
            "enhanced_behavior": runtime.extended_behavior_pass,
            "static_contract": static["static_pass"],
            "runtime_consumption": runtime.target_result_consumed is True,
            "hybrid": hybrid,
        },
        "reference": case["reference"],
    }


def load_ntrip_candidates() -> list[dict[str, Any]]:
    root = Path(__file__).resolve().parents[3]
    path = Path(
        os.environ.get(
            "G2_NTRIP_RESULT",
            root / "research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/PROBE_RESULT.json",
        )
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for row in data["rows"]:
        rows.append(
            {
                "id": f"ntrip_{row['arm'].lower()}",
                "task_id": "PYMIG_NTRIPBROWSER_CHARDET_TO_CCHARDET_9161C194",
                "probe_kind": "detect_dict",
                "kind": "natural_model_candidate",
                "code": row["code"],
                "reference": "VALID" if row["arm"] != "BASE" else "INVALID",
            }
        )
    return rows


def synthetic_controls() -> list[dict[str, Any]]:
    return [
        {
            "id": "partridge_real_parent",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "natural_commit_parent",
            "code": "from chardet import UniversalDetector\n\ndef detect_encoding(f, limit=100):\n    u = UniversalDetector()\n    for line in f:\n        line = bytearray(line)\n        u.feed(line)\n        limit -= 1\n        if u.done or limit < 1:\n            break\n    u.close()\n    if u.result['encoding'] == 'ascii':\n        return 'utf-8'\n    return u.result['encoding']",
            "setup_code": "requirements = ['chardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "INVALID",
        },
        {
            "id": "partridge_real_gold",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "natural_commit_gold",
            "code": "from cchardet import UniversalDetector\n\ndef detect_encoding(f, limit=100):\n    u = UniversalDetector()\n    for line in f:\n        u.feed(line)\n        limit -= 1\n        if u.done or limit < 1:\n            break\n    u.close()\n    if u.result['encoding'] == 'ascii':\n        return 'utf-8'\n    return u.result['encoding']",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "VALID",
        },
        {
            "id": "partridge_call_then_hardcoded_utf8",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "synthetic_control",
            "code": "from cchardet import UniversalDetector\n\ndef detect_encoding(f, limit=100):\n    u = UniversalDetector()\n    for line in f:\n        u.feed(line)\n    u.close()\n    return 'utf-8'",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "INVALID",
        },
        {
            "id": "partridge_call_then_hardcoded_latin1",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "synthetic_real_repository_control",
            "code": "from cchardet import UniversalDetector\n\ndef detect_encoding(f, limit=100):\n    u = UniversalDetector()\n    for line in f:\n        u.feed(line)\n    u.close()\n    return 'latin-1'",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "INVALID",
        },
        {
            "id": "partridge_target_call_then_source_fallback",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "synthetic_real_repository_control",
            "code": "from cchardet import UniversalDetector\nfrom chardet import UniversalDetector as SourceDetector\n\ndef detect_encoding(f, limit=100):\n    lines = list(f)\n    target = UniversalDetector()\n    source = SourceDetector()\n    for line in lines[:limit]:\n        target.feed(line)\n        source.feed(line)\n    target.close()\n    source.close()\n    return 'utf-8' if source.result['encoding'] == 'ascii' else source.result['encoding']",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "INVALID",
        },
        {
            "id": "partridge_alias_valid",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "synthetic_control",
            "code": "from cchardet import UniversalDetector as Detector\n\ndef detect_encoding(f, limit=100):\n    u = Detector()\n    for line in f:\n        u.feed(line)\n    u.close()\n    return 'utf-8' if u.result['encoding'] == 'ascii' else u.result['encoding']",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "VALID",
        },
        {
            "id": "partridge_dynamic_valid",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "synthetic_control",
            "code": "import importlib\n\ndef detect_encoding(f, limit=100):\n    Detector = importlib.import_module('cchardet').UniversalDetector\n    u = Detector()\n    for line in f:\n        u.feed(line)\n    u.close()\n    return 'utf-8' if u.result['encoding'] == 'ascii' else u.result['encoding']",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "VALID",
        },
        {
            "id": "partridge_cached_equivalent_unresolved",
            "task_id": "PARGRIDGE_CHARDET_TO_CCHARDET_09E89D9",
            "probe_kind": "universal_detector",
            "kind": "synthetic_control",
            "code": "from cchardet import UniversalDetector\n\n_cache = {b'AB': 'utf-8'}\n\ndef detect_encoding(f, limit=100):\n    data = b''.join(f)\n    if data in _cache:\n        return _cache[data]\n    u = UniversalDetector()\n    u.feed(data)\n    u.close()\n    return u.result['encoding']",
            "setup_code": "requirements = ['cchardet', 'networkx>=2.0', 'pandas', 'isoweek']",
            "reference": "UNRESOLVED",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case")
    parser.add_argument("--action", choices=("static_contract", "runtime_consumption"))
    args = parser.parse_args()
    if args.case or args.action:
        if not args.case or not args.action:
            parser.error("--case and --action must be provided together")
        cases = {case["id"]: case for case in synthetic_controls()}
        if args.case not in cases:
            cases.update({case["id"]: case for case in load_ntrip_candidates()})
        case = cases[args.case]
        if args.action == "static_contract":
            result = static_contract(case["code"], case.get("setup_code", ""))
        else:
            probe = (
                run_universal_detector(case["code"], case.get("function_name", "detect_encoding"))
                if case["probe_kind"] == "universal_detector"
                else run_detect_dict(case["code"], case.get("function_name", "_decode_data"))
            )
            result = {
                "target_calls": probe.target_calls,
                "source_calls": probe.source_calls,
                "target_result_consumed": probe.target_result_consumed,
                "extended_behavior_pass": probe.extended_behavior_pass,
                "outputs": probe.outputs,
                "errors": probe.errors,
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    root = Path(__file__).resolve().parents[3]
    out = Path(__file__).with_name("G2_CONTROL_RESULTS_V2.json")
    cases = load_ntrip_candidates() + synthetic_controls()
    rows = [evaluate_case(case) for case in cases]
    payload = {
        "schema": "g2_contract_verification_v2",
        "date": "2026-10-22",
        "evidence_identity": "REAL_PARTRIDGE_COMMIT_PLUS_NTRIP_MODEL_OUTPUTS_PLUS_SYNTHETIC_CONTROLS",
        "real_task": {
            "repository": "https://github.com/remix/partridge",
            "parent_commit": "daefcbe6a03e92a0bfc0c2433279b9fd3d179f6c",
            "gold_commit": "09e89d98b5a00db44394204d2f3e70c220b51764",
            "license": "MIT",
            "gold_tests": "42 passed in GB10 Python 3.11.16 environment",
            "parent_tests": "42 passed in the same environment",
        },
        "rows": rows,
        "summary": summarize(rows),
        "nonclaims": [
            "The two real commit rows are a bounded migration case, not a natural error-rate estimate.",
            "Runtime consumption is task-scoped and does not establish general semantic equivalence.",
            "UNRESOLVED cache rows are excluded from false-accept and false-reject rates.",
            "The real repository test suite passing on the parent shows behavior-only verification has no headroom for this dependency contract.",
        ],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
