# -*- coding: utf-8 -*-
'''TQ-3 entry checks: exercise the REAL scoring entry with positive and negative cases.

Supersedes two over-strong acceptance statements in
measurement_contract_v2/tools/tq2_offline_checks.py (old file untouched):
1) "modified copy hash differs from pinned original" was a bare hash comparison,
   not an entry rejection.
2) the "UNRESOLVED" string check was a bare string check, not entry-enforced blocking.
Now each anomaly is routed through the actual loading/scoring entry and must be
rejected (exception) or blocked (no valid score).

Writes only entry_checks/ENTRY_CHECKS.json. No network. No model calls.
'''
import json
import sys
import tempfile
from pathlib import Path

TQ3 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TQ3 / "tools"))
import tq3_scoring_entry as entry

PANEL = TQ3 / "dev_panel"
manifest = json.loads((PANEL / "PANEL_MANIFEST.json").read_text(encoding="utf-8"))
pins = manifest["input_pins"]

checks = []


def record(check_id, passed, detail):
    checks.append({"check": check_id, "passed": bool(passed), "detail": detail})


loaded = {}
fail = []
for rel, sha in pins.items():
    try:
        loaded[rel] = entry.load_input(PANEL / rel, expected_sha256=sha)
    except Exception as e:
        fail.append({"input": rel, "error": type(e).__name__ + ": " + str(e)})
record("positive_all_inputs_load_with_pins", (not fail) and len(loaded) == 12, {"loaded": len(loaded), "failures": fail})

q03 = json.loads((PANEL / "scoring/Q03.json").read_text(encoding="utf-8"))
r1 = entry.score("Q03", {"task_id": "Q03", "answer": "14054", "evidence": []}, q03)
record("positive_score_fixture_match", r1["status"] == "MATCH" and r1["score"] == 1.0, {"fixture": "entry-test fixture; not an actor result", "result": r1})
r2 = entry.score("Q03", {"task_id": "Q03", "answer": "9999", "evidence": []}, q03)
record("positive_score_fixture_no_match", r2["status"] == "NO_MATCH" and r2["score"] == 0.0, {"fixture": "entry-test fixture; not an actor result", "result": r2})

table = loaded["inputs_perturbed/Q02.json"]["table"]
try:
    entry.validate_reference_coords(table, ["r999c999"])
    n1 = {"rejected": False, "error": None}
except entry.InputRejected as e:
    n1 = {"rejected": True, "error": str(e)}
record("negative_invalid_reference_coordinate_via_entry", n1["rejected"] and "INVALID_REFERENCE_COORDINATES" in (n1["error"] or ""), n1)

orig = PANEL / "inputs_perturbed/Q03.json"
pin = pins["inputs_perturbed/Q03.json"]
with tempfile.TemporaryDirectory() as td:
    mod_path = Path(td) / "Q03_modified.json"
    mod = json.loads(orig.read_text(encoding="utf-8"))
    mod["question"] = mod["question"] + " [modified]"
    mod_path.write_text(json.dumps(mod, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        obj = entry.load_input(mod_path, expected_sha256=pin)
        n2 = {"rejected": False, "loaded": True}
    except entry.InputRejected as e:
        n2 = {"rejected": True, "error": str(e), "loaded": False}
record("negative_changed_input_hash_via_entry", n2["rejected"] and "INPUT_HASH_MISMATCH" in (n2["error"] or "") and not n2.get("loaded", False), n2)

fake_scoring = {"task_id": "NEG-TEST", "scoring_version": "negative-test", "compare_mode": "numeric", "expected_precise": 1.0, "abs_tolerance": 0.01, "unit_scale_status": "UNRESOLVED"}
r3 = entry.score("NEG-TEST", {"task_id": "NEG-TEST", "answer": "1.0"}, fake_scoring)
record("negative_unresolved_scale_no_valid_score", r3["status"] == "BLOCKED_SCALE_UNRESOLVED" and r3["score"] is None, {"fixture": "synthetic scoring material for the negative test", "result": r3})

with tempfile.TemporaryDirectory() as td:
    leak_path = Path(td) / "Q02_leak.json"
    leak = json.loads((PANEL / "inputs_perturbed/Q02.json").read_text(encoding="utf-8"))
    leak["official_reference"] = {"answer": 1}
    leak_path.write_text(json.dumps(leak, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        entry.load_input(leak_path)
        n4 = {"rejected": False}
    except entry.InputRejected as e:
        n4 = {"rejected": True, "error": str(e)}
record("negative_reference_leakage_via_entry", n4["rejected"] and "INPUT_LEAKAGE" in (n4["error"] or ""), n4)

report = {
    "schema": "tq3_entry_checks_v1",
    "date": "2026-10-16",
    "actor": "Loop D (AI)",
    "entry_module": "tq3_execution_prep_v1/tools/tq3_scoring_entry.py",
    "entry_kind": "LOCAL_DETERMINISTIC_ONLY (no model, no network)",
    "supersedes": {
        "file": "measurement_contract_v2/tools/tq2_offline_checks.py",
        "old_files_untouched": True,
        "corrected_statements": [
            "negative_changed_input_hash_rejected: old claim compared a modified copy hash to the pinned original; hash inequality alone is not an entry rejection. Now enforced by load_input raising INPUT_HASH_MISMATCH with no loaded object and no score.",
            "negative_unresolved_scale_blocks_compare: old claim checked for the string UNRESOLVED; string presence alone is not entry-enforced blocking. Now enforced by score() returning BLOCKED_SCALE_UNRESOLVED with score=None.",
        ],
    },
    "checks": checks,
    "all_passed": all(c["passed"] for c in checks),
    "scientific_gold_validity": "NOT_ESTABLISHED",
    "system_outcome": "NOT_RUN",
    "layer2_authorized": False,
}
out = TQ3 / "entry_checks" / "ENTRY_CHECKS.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
print(json.dumps({"all_passed": report["all_passed"], "n_checks": len(checks), "failed": [c["check"] for c in checks if not c["passed"]]}, ensure_ascii=True))
sys.exit(0 if report["all_passed"] else 1)
