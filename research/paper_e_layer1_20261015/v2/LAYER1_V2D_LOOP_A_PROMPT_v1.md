ACK FIRST LINE: ACK pe-l1-v2d: Loop A executor, canonical v2 Stage-D

ROLE: Loop A executor on GB10. Read-only over frozen inputs. Do not spawn sub-agents.

AUTHORITY:
`research/paper_e_layer1_20261015/v2/LAYER1_V2_CANONICAL_PREREG_v1.md` is the single
governing contract. Implement it exactly. Do not redesign it. Do not run Stage V2-H.

GOAL:
Implement and run Stage V2-D of the canonical v2 prereg: column-local independent binding
gold on the dev 59 cases only. Do not compute any held-out label.

INPUTS (verify hashes first):
- data/research/drift_v0/output/injection_map.json
- data/research/drift_v0/input/tatqa_tables.json
- data/research/drift_v0/output/injected_tables.json
- logs/graph/eval/t2_visibility_sensitivity.json
- research/paper_e_layer1_20261015/LAYER1_RESULTS_v1.json
- research/paper_e_layer1_20261015/v2/LAYER1_V2_CANONICAL_PREREG_v1.md

ALLOWED WRITES (only):
- research/paper_e_layer1_20261015/v2/run_layer1_v2.py
- research/paper_e_layer1_20261015/v2/dev/V2D_RESULTS_v1.json
- research/paper_e_layer1_20261015/v2/dev/V2D_RECEIPT_v1.json
- research/paper_e_layer1_20261015/v2/dev/V2D_SUMMARY_v1.md

DO:
1. Implement the canonical column-local rule exactly, including reason codes.
2. Run only on dev 59 cases; do not read or emit held-out labels.
3. Recompute value invariance bytewise; verify provenance; apply Levenshtein/tie rule.
4. Read the checker verdict only after dev labels are frozen.
5. Build the 2x3 contingency and report u_rate_dev, co_miss, co_alarm descriptively.
6. Emit the three V2D artifacts with hashes, counts, zero-call attestation, self-checks.
7. Self-check: input hashes match; every case one label; counts reconcile; no held-out label.
8. Stop at the Stage V2-D decision gate. Do not run Stage V2-H.

FORBIDDEN:
- Any model/judge/API/network/endpoint/training call.
- Editing the canonical prereg, v1 artifacts, manuscript, claim matrix, scope lock, or delta.
- Running held-out cases or emitting any held-out label.
- Git commit/push/checkout/reset.
- Claiming a population rate, OCR result, harmful blind spot, or Layer 2 authorization.

STOP ON:
INPUT_MISSING, HASH_MISMATCH, RULE_AMBIGUOUS, UNDECIDED_CASE, ZERO_CALL_VIOLATION,
POST_FREEZE_CHANGE. Report and stop; do not fix or expand.

FINAL REPLY FORMAT:
RESULT: <GOLD_ESTABLISHED_ON_DEV|GOLD_NOT_ESTABLISHED_NO_GO|STOPPED>
COUNTS: E=<n> H=<n> U=<n>
U_RATE_DEV: <value>
ZERO_CALLS: yes
HELDOUT_LABELS_COMPUTED: no
RUN_DIR: <path>
