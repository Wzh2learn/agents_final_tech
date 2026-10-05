# SUMMARY: Q3 labels and B0-B4 exploratory baselines

> Status: current summary | Updated: 2026-10-05 | Evidence level: exploratory only

## Current answer

The 146-column Valentine Q3 review is sealed with visibility exceptions. The corrected label distribution is `map_to=51 / skip=58 / hold=37`. The pre-correction `52/58/36` distribution is provenance only.

R1/R2 exact agreement is 119/146, action Cohen's kappa is approximately 0.727, and all 27 disagreements are action-boundary decisions. Target identity was 41/41 when both reviewers selected `map_to`. The only final-ledger correction changes line 61 from `map_to | pap_curb_sec` to `hold | null`.

B0-B4 v2 is the valid exploratory baseline run. The first run is invalidated by the salted B4 alignment bug. B4 is the strongest risk-admissible simple baseline to beat, but dedicated-student necessity is not established.

## Canonical evidence

| Topic | Canonical file |
|---|---|
| Corrected Q3 ledger and visibility exceptions | `docs/experiments/2026-10-04_q3_full_delivery_seal_validation.md` |
| Machine seal receipt | `docs/datasets/phase1a_q3_seal_receipt_v1.json` |
| B0-B4 v2 result | `docs/experiments/2026-10-04_b0_b4_exploratory_probe_results_v2.md` |
| Valid frozen configuration | `docs/datasets/2026-10-04_b0_b4_exploratory_config_v1.json` and `freeze_v2.json` |
| Stage D necessity interpretation | `docs/experiments/2026-10-05_stage_d_necessity_residual_memo.md` |
| Q3 pre-correction and B5 candidate | `docs/experiments/2026-10-04_q3_adjudicated_labels_and_b5_candidate.md` |

## Historical chain

- `docs/archive/experiments/2026-10-04_q3_partial_delivery_validation.md` records the incomplete delivery state before the full raw package arrived.
- `docs/archive/experiments/2026-10-04_q3_boundary_blocker_audit.md` records the earlier raw-missing and invalid-reference blockers before Option A/B were implemented.
- `docs/datasets/2026-10-04_b0_b4_exploratory_freeze_v1.json` is superseded by `freeze_v2.json`.

## Boundary

This chain is exploratory learnability evidence. It does not lift `DATA_NO_GO`, does not identify RQ2, and does not establish Stage D, Stage R, RQ4, or training results. B5 remains `PROPOSED_EXPLORATORY / NOT_RUN`.
