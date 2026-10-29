#!/usr/bin/env python3
"""Check frozen original operating points and the separate sensitivity grid."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
output = Path(sys.argv[2])
original = root / "logs/graph/eval/t1_eval_baseline_comparison.json"
grid = root / "research/stage_e_method_revision_20261009/matched_fpr_reanalysis.json"
runner = root / "research/paper_t1_eval_baselines.py"
grid_runner = root / "research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py"
data = json.loads(original.read_text(encoding="utf-8"))
arm = data["arm_b"]
if data["meta"]["tau"] != 2.0 or data["meta"]["flat_tau_H"] != 0.2:
    raise ValueError("original thresholds differ")
computed = {}
for unit in ("tables", "injections"):
    rows = arm[unit]
    vals = {
        "n": len(rows),
        "flat_ge_2": sum(row["drop10"] >= 2.0 for row in rows),
        "hier_ge_2": sum(row["E1.3_root_drop"] >= 2.0 for row in rows),
        "flat_equal_2": sum(row["drop10"] == 2.0 for row in rows),
        "hier_equal_2": sum(row["E1.3_root_drop"] == 2.0 for row in rows),
        "flat_recorded_flags": sum(row["E1.2_detected"] for row in rows),
        "hier_recorded_flags": sum(row["E1.3_detected"] for row in rows),
    }
    if vals["flat_ge_2"] != vals["flat_recorded_flags"] or vals["hier_ge_2"] != vals["hier_recorded_flags"]:
        raise ValueError("stored rounded values do not reproduce recorded decisions")
    computed[unit] = vals
reanalysis = json.loads(grid.read_text(encoding="utf-8"))
cell = next(x for x in reanalysis["cross_fit"][0]["fixed_affine_grid_sensitivity"] if x["theta_flat_drop10"] == 1.0)
if cell["theta_layered_root_drop"] != 0.375 or cell["flat_detected"] != cell["layered_detected"]:
    raise ValueError("matched grid cell differs")
result = {
    "scope": "post-hoc frozen-artifact recheck; not a new experimental panel",
    "original": computed,
    "original_predicate": "flat drop10 >= 2.0; hierarchical root drop >= 2.0, on their respective scales",
    "matched_grid_predicate": "strictly greater than the corresponding thresholds; distinct from the original >= predicate",
    "matched_grid_fold_0": cell,
    "frozen_sha256": {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (original, grid, runner, grid_runner)
    },
    "caveat": "Counts are from saved rounded values and stored decisions; this check does not rerun the original pipeline or establish general calibration.",
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
