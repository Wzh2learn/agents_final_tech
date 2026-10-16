# -*- coding: utf-8 -*-
'''TQ-3 developmental dry-run panel builder (12 inputs).

Builds, from the frozen packet (read-only):
- dev_panel/inputs_original/Qxx.json
- dev_panel/inputs_perturbed/Qxx.json
- dev_panel/reference/Qxx.json
- dev_panel/scoring/Qxx.json
- dev_panel/PANEL_MANIFEST.json
- dev_panel/README.md

All 12 inputs share one field structure. Reference answers and scoring
materials are stored separately and never inside input files.
Developmental panel - NOT heldout. No network. No model calls.
'''
import hashlib
import json
from pathlib import Path

PKG = Path(
    "D:/AIRcommend/JinRongAgents/agents_final_tech/research/"
    "paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1"
)
TQ3 = PKG / "tq3_execution_prep_v1"
PANEL = TQ3 / "dev_panel"
DEV = ["Q02", "Q03", "Q04", "Q05", "Q10", "Q12"]
STATUS_LABELS = {
    "panel": "DEVELOPMENTAL_DRY_RUN_NOT_HELDOUT",
    "reference_validity": "NOT_ESTABLISHED",
    "system_outcome": "NOT_RUN",
}


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(path, obj):
    Path(path).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8"
    )


def build_scoring(cid, ref):
    common = {
        "task_id": cid,
        "scoring_version": "v1",
        "status_labels": dict(STATUS_LABELS),
    }
    if cid == "Q02":
        return {
            **common,
            "compare_mode": "span_containment_normalized",
            "expected": "accounts receivable, inventories, and net property, plant, and equipment.",
            "expected_spans": ["accounts receivable, inventories, and net property, plant, and equipment."],
            "expected_precise": None,
            "abs_tolerance": None,
            "accepted_formats": None,
            "normalization_rules": ["lowercase", "strip terminal period", "collapse whitespace"],
            "unit_scale_status": "NOT_APPLICABLE",
            "notes": "Definition-span question; normalized containment counts as match for this dry run.",
        }
    if cid in ("Q03", "Q04", "Q12"):
        return {
            **common,
            "compare_mode": "numeric",
            "expected": ref["answer"],
            "expected_spans": None,
            "expected_precise": float(ref["answer"]),
            "abs_tolerance": 0.5,
            "accepted_formats": None,
            "normalization_rules": ["extract signed numbers", "strip thousands separators", "percent divides by 100 when value > 1.5"],
            "unit_scale_status": "RESOLVED_SCALE_MILLION",
            "notes": "0-digit integer tolerance as abs diff <= 0.5; scale resolved on reference side (specs_rev1).",
        }
    if cid == "Q05":
        return {
            **common,
            "compare_mode": "date",
            "expected": ref["answer"],
            "expected_spans": None,
            "expected_precise": None,
            "abs_tolerance": None,
            "accepted_formats": ["%d %B %Y", "%Y-%m-%d", "%B %d, %Y"],
            "normalization_rules": ["parse with one accepted format", "compare dates"],
            "unit_scale_status": "NOT_APPLICABLE",
            "notes": "Exact date match required.",
        }
    if cid == "Q10":
        return {
            **common,
            "compare_mode": "numeric",
            "expected": 0.47,
            "expected_spans": None,
            "expected_precise": 445000.0 / 945000.0,
            "abs_tolerance": 0.005,
            "accepted_formats": None,
            "normalization_rules": ["extract numbers; percent form (value/100) is the same ratio"],
            "unit_scale_status": "NOT_APPLICABLE",
            "notes": "Ratio 0.47, not a percentage operation; do not conflate 0.47 with 47 percent.",
        }
    raise ValueError(cid)


def main():
    packet = json.loads((PKG / "packets/stage2_cases.json").read_text(encoding="utf-8"))
    cases = {c["case_id"]: c for c in packet}
    specs = {
        cid: json.loads((TQ3 / "specs_rev1" / f"{cid}.json").read_text(encoding="utf-8"))
        for cid in DEV
    }
    input_pins = {}
    ref_pins = {}
    scoring_pins = {}
    for cid in DEV:
        c = cases[cid]
        for variant, table in (("original", c["source_table"]), ("perturbed", c["perturbed_table"])):
            obj = {
                "task_id": cid,
                "variant": variant,
                "question": c["question"],
                "table": table,
                "paragraphs": c["paragraphs"],
            }
            rel = f"inputs_{variant}/{cid}.json"
            write_json(PANEL / rel, obj)
            input_pins[rel] = sha256_file(PANEL / rel)
        ref = c["official_reference"]
        ref_obj = {
            "task_id": cid,
            "reference_version": "v1",
            "source": "packets/stage2_cases.json#official_reference (frozen packet copy)",
            "official_reference": ref,
            "applies_to_variants": ["original", "perturbed"],
            "provisional_evidence_effect": specs[cid]["evidence_effect_ai"],
            "caveats": [
                "reference_validity NOT_ESTABLISHED; provisional expected answer for the developmental dry run only",
                "perturbed-variant expectation relies on the provisional PRESERVED judgment (AI; not independent gold)",
            ],
        }
        rel = f"reference/{cid}.json"
        write_json(PANEL / rel, ref_obj)
        ref_pins[rel] = sha256_file(PANEL / rel)
        scoring = build_scoring(cid, ref)
        if scoring["compare_mode"] == "span_containment_normalized":
            assert ref["answer"][0] in scoring["expected_spans"]
        elif scoring["compare_mode"] == "date":
            assert scoring["expected"] == ref["answer"]
        else:
            assert abs(float(scoring["expected"]) - float(ref["answer"])) < 1e-9
        rel = f"scoring/{cid}.json"
        write_json(PANEL / rel, scoring)
        scoring_pins[rel] = sha256_file(PANEL / rel)
    allowed_keys = {"task_id", "variant", "question", "table", "paragraphs"}
    struct_fail = []
    for rel in input_pins:
        obj = json.loads((PANEL / rel).read_text(encoding="utf-8"))
        if set(obj.keys()) != allowed_keys:
            struct_fail.append({"input": rel, "keys": sorted(obj.keys())})
    assert not struct_fail, struct_fail
    manifest = {
        "schema": "tq3_dev_panel_manifest_v1",
        "date": "2026-10-16",
        "actor": "Loop D (AI)",
        "panel_name": "tq3_developmental_dry_run_panel_v1",
        "heldout": False,
        "confirmatory": False,
        "purpose": "Developmental dry run for TQ-3: real system outputs plus A/B/C verification under the prepared run card. NOT heldout, NOT confirmatory.",
        "primary_metrics_tasks": DEV,
        "excluded_exploratory_ambiguity": ["Q06", "Q08", "Q09"],
        "quarantined": ["Q01", "Q07", "Q11"],
        "input_structure": {"keys": sorted(allowed_keys), "variants": ["original", "perturbed"]},
        "counts": {"inputs": 12, "reference_files": 6, "scoring_files": 6},
        "source_packet": {"path": "packets/stage2_cases.json", "sha256": sha256_file(PKG / "packets/stage2_cases.json")},
        "input_pins": input_pins,
        "reference_pins": ref_pins,
        "scoring_pins": scoring_pins,
        "checks_performed": {
            "inputs_same_field_structure": True,
            "reference_scoring_consistency": True,
            "no_forbidden_keys_in_inputs": True,
            "reference_and_scoring_not_in_inputs": True,
        },
    }
    write_json(PANEL / "PANEL_MANIFEST.json", manifest)
    readme = [
        "# TQ-3 Developmental Dry-Run Panel",
        "",
        "> DEVELOPMENTAL_DRY_RUN_NOT_HELDOUT - not confirmatory; not human gold.",
        "> Built 2026-10-16 by Loop D (AI). No model calls.",
        "",
        "- inputs_original/ - 6 original-variant inputs",
        "- inputs_perturbed/ - 6 perturbed-variant inputs",
        "- reference/ - reference-side official answers (never given to the system under test)",
        "- scoring/ - reference-side scoring rules consumed by tools/tq3_scoring_entry.py",
        "- PANEL_MANIFEST.json - file pins, counts, exclusions",
        "",
        "All 12 inputs share one field structure: task_id, variant, question, table, paragraphs.",
        "The panel pairs original/perturbed variants of the same 6 tasks (paired design; not 12 independent samples).",
        "",
    ]
    (PANEL / "README.md").write_text(chr(10).join(readme), encoding="utf-8")
    print(json.dumps({"inputs": len(input_pins), "reference_files": len(ref_pins), "scoring_files": len(scoring_pins)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
