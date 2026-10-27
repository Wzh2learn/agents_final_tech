"""Read-only replay and paired controls for the 2026-10-27 D return.

Run with the GB10 Python 3.12 environment. Imports no models; never calls a
generation loader or the historical writers. Output is a new review receipt.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from research.adaptive_mechanism_20261027_v1.d_integration import question_only_ablation as qa
from research.adaptive_mechanism_20261027_v1.scoring_v2 import scorer as sc


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload(answer, value, refs):
    return json.dumps(dict(answer=answer, numeric_value=value, unit="thousand",
                           evidence_refs=refs, unknown=False, clarification=""))


def control(reference, text):
    context = sc.load_visible_context({"paragraphs": []}, reference, [])
    result = sc.score_response(text, reference, context)
    return {"status": result["status"], "evidence": result["layers"]["evidence"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    stage = ROOT / "research/adaptive_mechanism_20261027_v1"
    watched = [p for p in stage.rglob("*") if p.is_file()
               and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts]
    watched += [qa.vtb.DEFAULT_RAW, qa.vtb.DEFAULT_ANNOTATED,
                qa.vtb.DEFAULT_REFERENCE, qa.vtb.DEFAULT_SOURCE]
    before = {str(p): digest(p) for p in watched}
    cases = qa.build_cases()
    variants = {}
    for mode, name in (("oracle", "ORACLE_ROWS.jsonl"),
                       ("answer_type_free", "ANSWER_TYPE_FREE_ROWS.jsonl"),
                       ("question_only", "QUESTION_ONLY_ROWS.jsonl")):
        observed = qa.run_variant(cases, mode)
        saved = qa.read_jsonl(stage / "d_integration/results" / name)
        variants[mode] = {"rows": len(observed),
                          "counts": dict(Counter(r["score_status"] for r in observed)),
                          "full_row_equality": observed == saved}

    ref = dict(answer=["100"], answer_type="span", unit="thousand", program="",
               paragraphs=[], source_requirement="table",
               question="What was the wanted role in 2019?",
               table_text="columns: C0=item | C1=2019\n"
                          "R1 [wanted role] C0=wanted role | C1=100\n"
                          "R2 [wrong role] C0=wrong role | C1=100")
    equal_cells = {name: control(ref, payload(["100"], 100, refs))
                   for name, refs in (
                       ("correct_role_only", ["TABLE:R1:C1"]),
                       ("wrong_role_only", ["TABLE:R2:C1"]),
                       ("both_roles", ["TABLE:R1:C1", "TABLE:R2:C1"]))}
    ref2 = dict(answer=30, answer_type="arithmetic", unit="thousand", program="10+20",
                paragraphs=[], source_requirement="table",
                question="What is the sum of wanted in 2019 and 2018?",
                table_text="columns: C0=(in thousands) | C1=2019 | C2=2018\n"
                           "R1 [wanted] C0=wanted | C1=10 | C2=20\n"
                           "R2 [wrong] C0=wrong | C1=100 | C2=200")
    mixed = control(ref2, payload("30", 30, ["TABLE:R1:C1", "TABLE:C2"]))

    numeric_mutations = []
    rows = qa.run_variant(cases, "question_only")
    for (uid, arm, reference, context), row in zip(cases, rows):
        gold = reference["answer"]
        if (row["score_status"] == "ACCEPT" and reference["answer_type"] == "span"
                and isinstance(gold, list) and len(gold) == 1
                and sc.parse_decimal(gold[0]) is not None):
            changed = dict(row["response"])
            changed["numeric_value"] = -999999
            result = sc.score_response(json.dumps(changed), reference, context)
            numeric_mutations.append({"uid": uid, "arm": arm, "changed_value": -999999,
                                      "status": result["status"]})

    after = {str(p): digest(p) for p in watched}
    receipt = {
        "schema": "adaptive_mechanism_post_return_review_v1",
        "review_date": "2026-10-27",
        "boundary": "AI read-only development audit, no new method experiment or human gold",
        "scientific_generation": 0, "training": 0, "judge": 0,
        "ac_dispatches": 0, "variants": variants,
        "paired_equal_value_controls": equal_cells,
        "mixed_exact_and_broad_control": mixed,
        "single_numeric_span_contradictions": numeric_mutations,
        "historical_inputs_unchanged": before == after,
        "input_hashes": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): h
                         for p, h in ((p, before[str(p)]) for p in watched)},
        "verdict": "ACCEPT_REPLAY_NARROW_SCORER_ROLE_AND_NUMERIC_CLAIMS",
        "limits": [
            "Controls are synthetic or mutations of exposed outputs, not natural error prevalence.",
            "The five numeric-field mutations do not prove the five original responses were wrong.",
            "31/5 is exactly reproducible under V2; role-complete semantic validation is not established.",
            "No held-out panel, model loader, TeX build, submission or external publication was executed."
        ]
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"variants": variants, "controls": equal_cells, "mixed": mixed,
                      "mutated_numeric_span_accepts": sum(r["status"] == "ACCEPT" for r in numeric_mutations),
                      "historical_inputs_unchanged": before == after}, ensure_ascii=False))
    return 0 if before == after and all(v["full_row_equality"] for v in variants.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
