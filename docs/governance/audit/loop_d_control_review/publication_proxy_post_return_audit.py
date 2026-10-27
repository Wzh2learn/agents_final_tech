"""Read-only audit of frozen P2 calls; never instantiate an actor or mutate raw."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.publication_proxy_calibration_20261026_v1.raw.semantic_matcher import (  # noqa: E402
    expected_refs, semantic_result,
)
from research.publication_proxy_calibration_20261026_v1.raw.strict_parser import (  # noqa: E402
    ParsedResponse, parse_response,
)
from research.publication_proxy_calibration_20261026_v1.raw.runner import (  # noqa: E402
    item_for, load_sources,
)

BASE = ROOT / "research/publication_proxy_calibration_20261026_v1"


def load_rows(relative: str) -> list[dict]:
    return [json.loads(line) for line in (BASE / relative).read_text("utf-8").splitlines() if line.strip()]


def fingerprint(relative: str) -> dict:
    data = (BASE / relative).read_bytes()
    return {
        "path": str((BASE / relative).relative_to(ROOT)).replace("\\", "/"),
        "git_lf_sha256": hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest(),
    }


def audit() -> dict:
    first_path = "raw/runs/failed_attempt_20261026/P2_GENERATIONS.partial_40.jsonl"
    second_path = "raw/runs/primary/P2_GENERATIONS.jsonl"
    first, second = load_rows(first_path), load_rows(second_path)
    annotated = load_rows("raw/runs/compliant_primary/P2_GENERATIONS.annotated.jsonl")
    references = json.loads((BASE / "p2_proxy_calibration/receipts/P2_REFERENCE_CHAIN.json").read_text("utf-8"))["rows"]
    ref_by_hash = {hashlib.sha256(x["question_uid"].encode()).hexdigest(): x for x in references}
    by_uid = {x["question_uid"]: x for x in references}
    loaded = load_sources()
    assert len(first) == len(second) == len(annotated) == 40
    assert [x["call_number"] for x in first] == list(range(1, 41))
    assert all(x["retry_attempt"] in (1, 2) for x in first)
    scientific_keys = set(first[0]) - {"wall_seconds"}
    assert all(all(a[k] == b[k] for k in scientific_keys) for a, b in zip(first, second))
    assert sum(a["wall_seconds"] != b["wall_seconds"] for a, b in zip(first, second)) == 40

    last = {(x["question_uid_sha256"], x["arm"]): x for x in first}
    old_last = {(x["question_uid_sha256"], x["arm"]): x for x in annotated}
    assert len(last) == 36
    replay = []
    for key, raw in last.items():
        annotation = old_last[key]
        ref = ref_by_hash[key[0]]
        try:
            response, strict = parse_response(raw["complete_response"]), True
        except ValueError:
            response, strict = ParsedResponse.unknown_response("strict_parser_failure"), False
        _, item, prompt = item_for(loaded, ref["question_uid"], key[1], raw["retry_attempt"])
        assert hashlib.sha256(prompt.encode()).hexdigest() == raw["prompt_sha256"]
        assert list(item.selected_raw_orders) == annotation["selected_paragraph_orders"]
        required = {str(x["order"]) for x in ref["paragraphs"]}
        visible = ref["source_requirement"] == "table" or bool(required) and required <= set(item.selected_raw_orders)
        score = semantic_result(response, ref, visible)
        assert score["outcome"] == annotation["semantic_outcome"]
        assert score["reason"] == annotation["semantic_reason"]
        assert strict == (raw["strict_parse_outcome"] == "PASS")
        replay.append({
            "uid": ref["question_uid"], "table_uid": ref["table_uid"], "arm": key[1],
            "strict_parse": strict, "outcome": score["outcome"], "reason": score["reason"],
            "input_tokens": raw["input_tokens"], "output_tokens": raw["output_tokens"],
            "answer": response.answer, "unit": response.unit,
        })

    gold_controls = []
    for ref in references:
        if ref["answer_type"] in {"arithmetic", "count"}:
            response = ParsedResponse(str(ref["answer"]), float(ref["answer"]), ref["unit"] or "UNKNOWN", ["TABLE:R1:C1"], False, "")
            result = semantic_result(response, ref, True)
            assert not expected_refs(ref["program"])
            assert result["lexical_match"] and result["outcome"] == "PENDING_ADJUDICATION"
            gold_controls.append({"uid": ref["question_uid"], "program_type": type(ref["program"]).__name__, "score": result})
    assert len(gold_controls) == 6

    span_ref = by_uid["7a1f65b6-25e2-48e2-a3cc-baddc688545e"]
    invalid_unit_ref = semantic_result(ParsedResponse("96,168", 96168, "million", ["P999"], False, ""), span_ref, True)
    assert invalid_unit_ref["outcome"] == "ACCEPT"
    multi_ref = by_uid["a75bb0b1-4fb1-405c-b2f1-1df4ee3cc9be"]
    extra_span = semantic_result(ParsedResponse(["At beginning of the period", "Additions", "At end of the period"], None, "UNKNOWN", ["P999"], False, ""), multi_ref, True)
    assert extra_span["outcome"] == "ACCEPT"
    currency_ref = by_uid["fcb5e3fa-fb0c-4cce-a86c-229ac3734bd2"]
    currency = [semantic_result(ParsedResponse(answer, 1289962, "thousands", ["TABLE:C4"], False, ""), currency_ref, True) for answer in (["$1,289,962"], "1,289,962")]
    assert [x["outcome"] for x in currency] == ["REJECT", "ACCEPT"]

    summaries = {}
    for arm in ("table_top3", "table_top5", "table_all"):
        rows = [x for x in replay if x["arm"] == arm]
        summaries[arm] = {
            "items": len(rows), "outcomes": dict(Counter(x["outcome"] for x in rows)),
            "strict_pass": sum(x["strict_parse"] for x in rows),
            "input_tokens": sum(x["input_tokens"] for x in rows),
            "output_tokens": sum(x["output_tokens"] for x in rows),
        }
    assert [summaries[a]["outcomes"]["ACCEPT"] for a in summaries] == [2, 3, 3]
    arm_delta = summaries["table_top5"]["input_tokens"] - summaries["table_top3"]["input_tokens"]
    assert arm_delta == 917

    return {
        "schema": "publication_proxy_post_return_audit_v1", "date": "2026-10-27",
        "identity": "research-lead fresh read-only re-verification; not a new C dispatch",
        "model_calls": 0, "training_runs": 0, "endpoint_probes": 0,
        "source_fingerprints": [fingerprint(first_path), fingerprint(second_path), fingerprint("raw/semantic_matcher.py"), fingerprint("raw/strict_parser.py"), fingerprint("raw/runner.py")],
        "raw_replay_matches_frozen_annotations": True, "replayed_primary_items": len(replay),
        "prompts_and_visible_selection_rebuilt_from_hash_bound_original_source": True,
        "uids": len(references), "table_families": len({x["table_uid"] for x in references}),
        "physical_accounting": {
            "calls": 80, "first_batch_calls": 40, "second_batch_calls": 40, "original_call_cap": 48, "over_cap": 32,
            "input_tokens": sum(x["input_tokens"] for x in first + second),
            "output_tokens": sum(x["output_tokens"] for x in first + second),
            "retries_per_batch": sum(x["retry_attempt"] > 1 for x in first),
            "remaining_phase_b_calls_conservative": 672 - 188 - 80,
            "remaining_generation_tokens_conservative_input_plus_output": 2_800_000 - 139_306 - 71_632,
            "remaining_training_runs": 2, "remaining_training_tokens": 4_000_000 - 319_948,
            "ac_dispatches_used": 24, "ac_dispatches_authorized": 24,
        },
        "historical_matcher_summaries": summaries,
        "top5_minus_top3_final_item_input_tokens": arm_delta,
        "historical_scores_are_not_corrected_semantic_accuracy": True,
        "synthetic_scorer_counterexamples_not_model_results": {
            "gold_number_controls_pending": gold_controls,
            "wrong_unit_and_nonexistent_citation_accepted": invalid_unit_ref,
            "extra_span_and_nonexistent_citation_accepted": extra_span,
            "equivalent_currency_display_changes_outcome": currency,
        },
        "strict_failures": [{"call_number": x["call_number"], "arm": x["arm"], "retry": x["retry_attempt"], "reason": x["parse_error"]} for x in first if x["strict_parse_outcome"] == "FAIL"],
        "tex_build": {"status": "UNAVAILABLE_COMPILER_SANDBOX", "actual_compile_attempted": True, "source_not_changed": True, "fallback_pdf_not_tex_compilation": True},
        "verdict": "REAL_EXECUTION_ACCEPTED_SCORE_VALIDITY_BLOCKS_METHOD_AND_RETRIEVAL_CLAIMS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": "PASS", "replayed_items": report["replayed_primary_items"], "model_calls": 0, "verdict": report["verdict"]}, ensure_ascii=False))
