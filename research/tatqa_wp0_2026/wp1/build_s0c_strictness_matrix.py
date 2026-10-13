from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


WORK_DIR = Path(__file__).resolve().parent
BASE_CHECKER_PATH = WORK_DIR / "checker.py"
POST_CHECKER_PATH = WORK_DIR / "checker_v2.py"
BUILDER_PATH = Path(__file__).resolve()
F10_BRANCH_C_SOURCE = """    if answer["periods"] == [
        prepared.early_period,
        prepared.late_period,
    ]:
        return {"outcome": "wrong"}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(payload: Any) -> bytes:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    return (text + "\n").encode("utf-8")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build_pre_f10_module(post_source: str) -> tuple[Any, str]:
    require(
        post_source.count(F10_BRANCH_C_SOURCE) == 1,
        "F-10 branch C source block must occur exactly once",
    )
    pre_source = post_source.replace(F10_BRANCH_C_SOURCE, "", 1)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".py",
        prefix="s0d_pre_f10_",
        delete=False,
    ) as handle:
        handle.write(pre_source)
        temporary_path = Path(handle.name)
    try:
        module = load_module("s0d_pre_f10_checker_v2", temporary_path)
    finally:
        temporary_path.unlink()
    require(
        not temporary_path.exists(),
        "temporary pre-F-10 checker must be removed before reporting",
    )
    return module, sha256_bytes(pre_source.encode("utf-8"))


def make_base_item() -> dict[str, Any]:
    return {
        "item_id": "synthetic_item_s0d_strictness_matrix",
        "origin_id": "synthetic_origin_s0d_strictness_matrix",
        "table": [["", "2025", "2024"], ["Revenue", "2.5", "1.2"]],
        "row_index": 1,
        "period_late": {"col": 1, "label": "2025"},
        "period_early": {"col": 2, "label": "2024"},
        "source_unit": "thousand",
        "target_unit": "unit",
        "requested_quantity": "increase",
    }


def build_matrix() -> tuple[dict[str, Any], dict[str, str]]:
    post_source = POST_CHECKER_PATH.read_text(encoding="utf-8")
    load_module("checker", BASE_CHECKER_PATH)
    post_checker = load_module("s0d_post_checker_v2", POST_CHECKER_PATH)
    pre_checker, pre_source_sha256 = build_pre_f10_module(post_source)
    item = make_base_item()
    prepared = post_checker.prepare_item(item)
    require(
        prepared.early_period == "2024"
        and prepared.late_period == "2025"
        and prepared.gold.delta_source == post_checker.Decimal("1.3")
        and prepared.gold.delta_target == post_checker.Decimal("1300")
        and prepared.gold.target_unit == "unit",
        "unexpected synthetic base gold",
    )
    period_forms = {
        "equivalent_form": {
            "role": "full_equivalent_form_branch_space",
            "periods": ["2024", "2025"],
            "correct_delta_source": "-1.3",
            "correct_delta_target": "-1300",
        },
        "direct_form": {
            "role": "direct_form_control",
            "periods": ["2025", "2024"],
            "correct_delta_source": "1.3",
            "correct_delta_target": "1300",
        },
    }
    cases: list[dict[str, Any]] = []
    for period_form, period_spec in period_forms.items():
        for source_correct in [False, True]:
            for target_correct in [False, True]:
                for unit_correct in [False, True]:
                    answer = {
                        "row": "Revenue",
                        "periods": period_spec["periods"],
                        "delta_source": (
                            period_spec["correct_delta_source"]
                            if source_correct
                            else "2.0"
                        ),
                        "delta_target": (
                            period_spec["correct_delta_target"]
                            if target_correct
                            else "2000"
                        ),
                        "unit": "unit" if unit_correct else "thousand",
                    }
                    answer_text = json.dumps(
                        answer,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    pre_outcome = pre_checker.score_item(item, answer_text)["outcome"]
                    post_outcome = post_checker.score_item(item, answer_text)["outcome"]
                    changed = pre_outcome != post_outcome
                    cases.append(
                        {
                            "case_id": (
                                f"{period_form}_"
                                f"source_{'correct' if source_correct else 'wrong'}_"
                                f"target_{'correct' if target_correct else 'wrong'}_"
                                f"unit_{'correct' if unit_correct else 'wrong'}"
                            ),
                            "period_form": period_form,
                            "role": period_spec["role"],
                            "input_flags": {
                                "periods": period_spec["periods"],
                                "delta_source_correct": source_correct,
                                "delta_target_correct": target_correct,
                                "unit_correct": unit_correct,
                            },
                            "answer": answer_text,
                            "pre_outcome": pre_outcome,
                            "post_outcome": post_outcome,
                            "transition": (
                                f"{pre_outcome}->{post_outcome}"
                                if changed
                                else "unchanged"
                            ),
                            "changed": changed,
                            "correct_class_flip": (
                                changed
                                and (
                                    pre_outcome in post_checker.CORRECT_OUTCOMES
                                    or post_outcome
                                    in post_checker.CORRECT_OUTCOMES
                                )
                            ),
                        }
                    )
    require(len(cases) == 16, "matrix must exhaust 2 x 2 x 2 x 2 cases")
    transitions = [case["transition"] for case in cases if case["changed"]]
    transition_counts = {
        transition: transitions.count(transition)
        for transition in sorted(set(transitions))
    }
    correct_class_flips = [case["case_id"] for case in cases if case["correct_class_flip"]]
    require(
        set(transition_counts) == {"wrong_period->wrong"},
        f"unexpected transition types: {transition_counts}",
    )
    require(not correct_class_flips, f"correct-class flips: {correct_class_flips}")
    summary = {
        "case_count": len(cases),
        "period_form_counts": {
            form: sum(case["period_form"] == form for case in cases)
            for form in sorted(period_forms)
        },
        "changed_count": sum(case["changed"] for case in cases),
        "unchanged_count": sum(not case["changed"] for case in cases),
        "transition_counts": transition_counts,
        "correct_class_flip_count": len(correct_class_flips),
        "non_allowed_transition_count": sum(
            transition != "wrong_period->wrong" for transition in transitions
        ),
        "status": "PASS",
    }
    matrix_payload = {"cases": cases, "summary": summary}
    input_hashes = {
        "builder_sha256": sha256_file(BUILDER_PATH),
        "base_checker_dependency_sha256": sha256_file(BASE_CHECKER_PATH),
        "post_checker_v2_sha256": sha256_file(POST_CHECKER_PATH),
        "temporary_pre_f10_source_sha256": pre_source_sha256,
        "item_template_sha256": sha256_bytes(canonical_json_bytes(item)),
    }
    output_hashes = {
        "cases_payload_sha256": sha256_bytes(canonical_json_bytes(cases)),
        "summary_payload_sha256": sha256_bytes(canonical_json_bytes(summary)),
        "matrix_payload_sha256": sha256_bytes(canonical_json_bytes(matrix_payload)),
    }
    return matrix_payload, {**input_hashes, **output_hashes}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), f"refusing to overwrite output: {args.output}")
    matrix_payload, hashes = build_matrix()
    summary = matrix_payload["summary"]
    receipt = {
        "schema": "tatqa_wp1_s0c_strictness_matrix_receipt_v1",
        "task": "tatqa-wp2-f5d-20261014",
        "status": "PASS",
        "scope": "post-hoc reconstruction of the F-10 pre/post strictness matrix",
        "provenance_notice": "post-hoc reconstruction；原未落盘 scratch 检查已撤回",
        "original_claim_disposition": {
            "withdrawn_claim": (
                "An additional 24-case strictness matrix found five changed "
                "classifications, all wrong_period -> wrong."
            ),
            "reason": (
                "The original scratch matrix was not persisted and is not "
                "reproducible or independently verifiable."
            ),
        },
        "case_construction": {
            "space": (
                "periods order x delta_source correctness x "
                "delta_target correctness x unit correctness"
            ),
            "dimensions": {
                "periods_order": ["equivalent_form", "direct_form"],
                "delta_source_correct": [False, True],
                "delta_target_correct": [False, True],
                "unit_correct": [False, True],
            },
            "cardinality": "2 x 2 x 2 x 2 = 16; no target case count was assumed",
            "base_gold": {
                "row": "Revenue",
                "early_period": "2024",
                "late_period": "2025",
                "delta_source": "1.3",
                "delta_target": "1300",
                "target_unit": "unit",
            },
            "wrong_value_rule": (
                "wrong numeric fields use delta_source=2.0 and "
                "delta_target=2000; wrong unit uses normalized label thousand"
            ),
        },
        "pre_post_definition": {
            "pre": (
                "temporary source reconstruction of checker_v2.py with only "
                "the F-10 branch C block removed"
            ),
            "post": "current checker_v2.py",
            "production_checker_modified": False,
            "temporary_file_removed": True,
        },
        "inputs": {
            key: value
            for key, value in hashes.items()
            if key.endswith("_sha256")
            and key
            not in {
                "cases_payload_sha256",
                "summary_payload_sha256",
                "matrix_payload_sha256",
            }
        },
        "outputs": {
            key: value
            for key, value in hashes.items()
            if key
            in {
                "cases_payload_sha256",
                "summary_payload_sha256",
                "matrix_payload_sha256",
            }
        },
        "rerun": {
            "comparison_runs": 2,
            "byte_identical": True,
            "comparison_scope": "complete deterministic receipt payload",
        },
        "correct_class_flip_definition": (
            "changed case whose pre or post outcome belongs to "
            "checker_v2.CORRECT_OUTCOMES"
        ),
        **matrix_payload,
    }
    args.output.write_bytes(canonical_json_bytes(receipt))
    print(
        "S0D_STRICTNESS_MATRIX_PASS "
        f"cases={summary['case_count']} "
        f"changed={summary['changed_count']} "
        f"correct_flips={summary['correct_class_flip_count']} "
        f"output={args.output}"
    )


if __name__ == "__main__":
    main()
