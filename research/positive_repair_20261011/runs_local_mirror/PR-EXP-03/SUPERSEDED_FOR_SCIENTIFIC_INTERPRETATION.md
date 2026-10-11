# SUPERSEDED_FOR_SCIENTIFIC_INTERPRETATION

> date: 2026-10-11 | applies to: metrics.json, receipt.json, and the descriptive numbers in this directory (round-1 PR-EXP-03, v2 lineage)

These round-1 artifacts are NOT reproducible by the delivered frozen implementation:

- The frozen implementation (research/positive_repair_20261011/runs/PR-EXP-03/experiment.py, sha256 d75afca6...) contains a variable-shadowing bug at line 480 (`a1_table = a1_table(...)`) that makes `evaluate` raise UnboundLocalError. It cannot have produced this metrics.json.
- The frozen `predict_loco` is O(groups^2); the frozen 10,000-replicate diagnostic bootstrap is computationally infeasible, so the recorded runtime (275 s) is likewise not attainable by this code.

Status: SUPERSEDED_FOR_SCIENTIFIC_INTERPRETATION.
- Retained for provenance and history. Do NOT delete.
- Barred from use as manuscript evidence or as a scientific result.
- The v3 outcome (NEGATIVE; see research/positive_repair_20261011/PR-03_v3_RESULT_v1.md) supersedes the scientific interpretation; the registered round-1 class remains INVALID gate provenance / NOT_EVALUABLE as recorded in the registry.