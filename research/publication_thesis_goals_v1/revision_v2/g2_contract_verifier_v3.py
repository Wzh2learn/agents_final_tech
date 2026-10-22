"""Actual-module migration verifier with paired causal result interventions."""

from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import importlib
import json
import re
import types
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


VALID = "VALID"
INVALID = "INVALID"
UNRESOLVED = "UNRESOLVED"


@dataclass
class EvidenceResult:
    prediction: str
    reason: str
    execution_status: str
    module_path: str
    module_sha256: str
    function_name: str
    target_calls: int
    source_calls: int
    outputs: list[str | None]
    expected_outputs: list[str | None]
    errors: list[str | None]
    intervention_results: list[str]
    injection_boundary: dict[str, Any]


@dataclass
class CandidateResult:
    candidate_id: str
    reference: str
    prediction: str
    prediction_reason: str
    execution_status: str
    behavior_status: str
    static_contract: dict[str, Any]
    consumption: dict[str, Any]
    binding: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _DetectorState:
    def __init__(self, role: str, result_encoding: str, calls: dict[str, int]) -> None:
        self.role = role
        self.result_encoding = result_encoding
        self.calls = calls
        self.data = b""
        self.result: dict[str, str | None] = {"encoding": None}
        self.done = False

    def feed(self, data: bytes) -> None:
        self.data += bytes(data)

    def close(self) -> None:
        self.calls[self.role] += 1
        self.result = {"encoding": self.result_encoding}
        self.done = True


def _detector_class(role: str, result_encoding: str, calls: dict[str, int]) -> type[_DetectorState]:
    return type(
        f"{role.title()}Detector",
        (_DetectorState,),
        {
            "__init__": lambda self: _DetectorState.__init__(
                self, role, result_encoding, calls
            )
        },
    )


def _flatten(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        output: list[Any] = []
        for item in value:
            output.extend(_flatten(item))
        return output
    return [value]


def execute_actual_module(
    module_path: Path,
    target_result: str,
    source_result: str,
) -> tuple[dict[str, Any], dict[str, int], dict[str, Any]]:
    source_bytes = module_path.read_bytes()
    source = source_bytes.decode("utf-8")
    ast.parse(source)
    calls = {"target": 0, "source": 0}
    target_class = _detector_class("target", target_result, calls)
    source_class = _detector_class("source", source_result, calls)
    target_module = types.SimpleNamespace(
        UniversalDetector=target_class,
        detect=lambda _data: {"encoding": target_result},
    )
    source_module = types.SimpleNamespace(
        UniversalDetector=source_class,
        detect=lambda _data: {"encoding": source_result},
    )
    pandas_common = types.SimpleNamespace(flatten=_flatten)
    pandas_core = types.SimpleNamespace(common=pandas_common)
    pandas = types.SimpleNamespace(core=pandas_core, DataFrame=lambda *args, **kwargs: None)
    numpy = types.SimpleNamespace(unicode=str)
    fake_importlib = types.SimpleNamespace(
        import_module=lambda name: {
            "cchardet": target_module,
            "chardet": source_module,
        }.get(name, importlib.import_module(name))
    )
    stubs = {
        "cchardet": target_module,
        "chardet": source_module,
        "pandas": pandas,
        "pandas.core": pandas_core,
        "pandas.core.common": pandas_common,
        "numpy": numpy,
        "importlib": fake_importlib,
    }
    real_import = builtins.__import__

    def controlled_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        if level == 0 and name in stubs:
            return stubs[name]
        return real_import(name, globals, locals, fromlist, level)

    namespace: dict[str, Any] = {
        "__builtins__": {**vars(builtins), "__import__": controlled_import},
        "__name__": "candidate_actual_module",
        "__file__": str(module_path),
    }
    exec(compile(source, str(module_path), "exec"), namespace)
    boundary = {
        "module_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_bytes": len(source_bytes),
        "stubbed_imports": sorted(stubs),
        "controlled_detector_results": {
            "target": target_result,
            "source": source_result,
        },
    }
    return namespace, calls, boundary


def consume_universal_detector(
    module_path: Path,
    function_name: str,
) -> EvidenceResult:
    interventions = (("latin-1", "cp1252"), ("utf-16-le", "cp1252"))
    outputs: list[str | None] = []
    expected: list[str | None] = []
    errors: list[str | None] = []
    total_target = 0
    total_source = 0
    boundary: dict[str, Any] = {}
    for target_result, source_result in interventions:
        namespace, calls, boundary = execute_actual_module(
            module_path, target_result, source_result
        )
        function = namespace.get(function_name)
        if not callable(function):
            return EvidenceResult(
                UNRESOLVED,
                f"function_not_found:{function_name}",
                "PROBE_ERROR",
                str(module_path),
                boundary["module_sha256"],
                function_name,
                calls["target"],
                calls["source"],
                [],
                [],
                [f"function_not_found:{function_name}"],
                [target_result for target_result, _ in interventions],
                boundary,
            )
        try:
            value = function(iter([b"AB"]))
            outputs.append(value if isinstance(value, str) else None)
            errors.append(None if isinstance(value, str) else "non_string_output")
        except Exception as exc:
            outputs.append(None)
            errors.append(f"{type(exc).__name__}:{exc}")
        expected.append("utf-8" if target_result == "ascii" else target_result)
        total_target += calls["target"]
        total_source += calls["source"]

    intervention_values = [item[0] for item in interventions]
    if any(error is not None for error in errors):
        prediction = UNRESOLVED
        reason = "candidate_execution_error"
        execution_status = "PROBE_ERROR"
    elif total_target == 0 and total_source > 0:
        prediction = INVALID
        reason = "source_dependency_used_without_target_calls"
        execution_status = "OK"
    elif total_target == 0:
        prediction = UNRESOLVED
        reason = "no_target_or_source_call_possible_cache_or_external_helper"
        execution_status = "OK"
    elif outputs == expected and outputs[0] != outputs[1]:
        prediction = VALID
        reason = "downstream_output_tracks_paired_target_result_intervention"
        execution_status = "OK"
    else:
        prediction = INVALID
        reason = "target_called_but_downstream_output_does_not_track_target_result"
        execution_status = "OK"
    return EvidenceResult(
        prediction,
        reason,
        execution_status,
        str(module_path),
        boundary["module_sha256"],
        function_name,
        total_target,
        total_source,
        outputs,
        expected,
        errors,
        intervention_values,
        boundary,
    )


def _manifest_declares(text: str, dependency: str) -> bool | None:
    if not text:
        return None
    pattern = rf"[\"']{re.escape(dependency)}(?:[<>=!~][^\"']*)?[\"']"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def analyze_static(module_path: Path, manifest_path: Path | None) -> dict[str, Any]:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    target_aliases: set[str] = set()
    source_aliases: set[str] = set()
    target_module_aliases: set[str] = set()
    source_module_aliases: set[str] = set()
    dynamic_target = False
    dynamic_source = False
    dynamic_unknown = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if alias.name == "cchardet" or alias.name.startswith("cchardet."):
                    target_module_aliases.add(bound)
                if alias.name == "chardet" or alias.name.startswith("chardet."):
                    source_module_aliases.add(bound)
        elif isinstance(node, ast.ImportFrom):
            bound_names = {
                alias.asname or alias.name for alias in node.names
            }
            if node.module == "cchardet" or (node.module or "").startswith("cchardet."):
                target_aliases.update(bound_names)
            if node.module == "chardet" or (node.module or "").startswith("chardet."):
                source_aliases.update(bound_names)
        elif isinstance(node, ast.Call):
            text = ast.unparse(node.func).lower()
            if text.endswith("import_module") and node.args:
                value = node.args[0]
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    dynamic_target |= value.value == "cchardet"
                    dynamic_source |= value.value == "chardet"
                else:
                    dynamic_unknown = True
            elif "__import__" in text:
                if node.args and isinstance(node.args[0], ast.Constant):
                    value = str(node.args[0].value)
                    dynamic_target |= value == "cchardet"
                    dynamic_source |= value == "chardet"
                else:
                    dynamic_unknown = True

    target_call = False
    source_call = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        called = ast.unparse(func)
        root = called.split(".", 1)[0]
        target_call |= root in target_aliases or root in target_module_aliases
        source_call |= root in source_aliases or root in source_module_aliases
        target_call |= "universaldetector" in called.lower() and bool(target_aliases)
        source_call |= "universaldetector" in called.lower() and bool(source_aliases)

    manifest_text = manifest_path.read_text(encoding="utf-8") if manifest_path else ""
    target_declared = _manifest_declares(manifest_text, "cchardet")
    source_declared = _manifest_declares(manifest_text, "chardet")
    target_imported = bool(target_aliases or target_module_aliases or dynamic_target)
    source_imported = bool(source_aliases or source_module_aliases or dynamic_source)
    if dynamic_unknown:
        prediction = UNRESOLVED
        reason = "nonliteral_dynamic_import_not_resolved"
    elif source_imported or source_call or source_declared:
        prediction = INVALID
        reason = "source_dependency_present"
    elif target_imported and target_call and target_declared:
        prediction = VALID
        reason = "alias_aware_target_import_call_and_manifest_agree"
    else:
        prediction = UNRESOLVED
        reason = "target_dependency_contract_not_fully_observed"
    return {
        "prediction": prediction,
        "reason": reason,
        "target_imported": target_imported,
        "target_call": target_call,
        "source_imported": source_imported,
        "source_call": source_call,
        "target_declared": target_declared,
        "source_declared": source_declared,
        "dynamic_target": dynamic_target,
        "dynamic_source": dynamic_source,
        "dynamic_unknown": dynamic_unknown,
        "target_aliases": sorted(target_aliases | target_module_aliases),
        "source_aliases": sorted(source_aliases | source_module_aliases),
    }


def combine_prediction(
    static_result: dict[str, Any],
    consumption_result: dict[str, Any],
    behavior_status: str,
) -> tuple[str, str, str]:
    execution_status = consumption_result["execution_status"]
    if execution_status != "OK":
        return UNRESOLVED, consumption_result["reason"], execution_status
    if behavior_status not in {"PASS", "FAIL", "NOT_RUN"}:
        return UNRESOLVED, "behavior_status_invalid", "CONTRACT_ERROR"
    if static_result["prediction"] == INVALID or consumption_result["prediction"] == INVALID:
        return INVALID, "independent_evidence_contains_invalid_result", "OK"
    if behavior_status == "FAIL":
        return INVALID, "independent_behavior_tests_fail", "OK"
    if (
        static_result["prediction"] == VALID
        and consumption_result["prediction"] == VALID
        and behavior_status == "PASS"
    ):
        return VALID, "static_consumption_and_independent_behavior_agree", "OK"
    return UNRESOLVED, "one_or_more_required_evidence_channels_unresolved", "OK"


def evaluate_candidate(
    candidate_id: str,
    module_path: Path,
    manifest_path: Path | None,
    function_name: str,
    reference: str,
    behavior_status: str,
) -> CandidateResult:
    if reference not in {VALID, INVALID, UNRESOLVED}:
        raise ValueError("reference_must_be_VALID_INVALID_or_UNRESOLVED")
    static_result = analyze_static(module_path, manifest_path)
    consumption_result = asdict(consume_universal_detector(module_path, function_name))
    prediction, reason, execution_status = combine_prediction(
        static_result, consumption_result, behavior_status
    )
    return CandidateResult(
        candidate_id=candidate_id,
        reference=reference,
        prediction=prediction,
        prediction_reason=reason,
        execution_status=execution_status,
        behavior_status=behavior_status,
        static_contract=static_result,
        consumption=consumption_result,
        binding={
            "module_path": str(module_path),
            "module_sha256": sha256_file(module_path),
            "manifest_path": str(manifest_path) if manifest_path else None,
            "manifest_sha256": sha256_file(manifest_path) if manifest_path else None,
            "function_name": function_name,
            "probe": "paired_target_result_intervention_on_actual_module",
        },
    )


def summarize(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    resolved_reference = [row for row in rows if row["reference"] in {VALID, INVALID}]
    reference_unresolved = [row for row in rows if row["reference"] == UNRESOLVED]
    summary: dict[str, Any] = {
        "n": len(rows),
        "resolved_reference_n": len(resolved_reference),
        "reference_unresolved_n": len(reference_unresolved),
        "execution_unresolved_n": sum(
            row["execution_status"] != "OK" for row in rows
        ),
    }
    for name, getter in (
        ("static_contract", lambda row: row["static_contract"]["prediction"]),
        ("consumption", lambda row: row["consumption"]["prediction"]),
        ("combined", lambda row: row["prediction"]),
    ):
        false_accept = false_reject = correct = abstain = 0
        for row in resolved_reference:
            prediction = getter(row)
            if prediction == UNRESOLVED:
                abstain += 1
                continue
            expected_valid = row["reference"] == VALID
            predicted_valid = prediction == VALID
            if predicted_valid and not expected_valid:
                false_accept += 1
            elif not predicted_valid and expected_valid:
                false_reject += 1
            else:
                correct += 1
        summary[name] = {
            "correct": correct,
            "false_accept": false_accept,
            "false_reject": false_reject,
            "abstain": abstain,
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--function", default="detect_encoding")
    parser.add_argument("--reference", choices=(VALID, INVALID, UNRESOLVED), required=True)
    parser.add_argument("--behavior-status", choices=("PASS", "FAIL", "NOT_RUN"), default="NOT_RUN")
    parser.add_argument(
        "--evidence-channel",
        choices=("all", "static_contract", "consumption"),
        default="all",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.evidence_channel != "all":
        if args.evidence_channel == "static_contract":
            result: Any = analyze_static(
                args.module.resolve(),
                args.manifest.resolve() if args.manifest else None,
            )
        else:
            result = asdict(consume_universal_detector(
                args.module.resolve(), args.function
            ))
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    result = evaluate_candidate(
        args.candidate_id,
        args.module.resolve(),
        args.manifest.resolve() if args.manifest else None,
        args.function,
        args.reference,
        args.behavior_status,
    )
    rendered = json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
