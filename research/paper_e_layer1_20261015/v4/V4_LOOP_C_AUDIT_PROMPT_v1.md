ACK FIRST LINE: ACK pe-l1-v4-audit: Loop C independent auditor

ROLE: Loop C independent auditor on GB10. Read-only. Do not modify runner, contract, fixtures, or preflight receipt.

GOAL:
Audit the v4 compact pipeline before any held-out label is computed. Verify that v4 is a single
governing contract with a machine-checkable implementation, that the synthetic preflight passed,
and that no held-out label or checker verdict has been read as a label source.

SOURCES:
- research/paper_e_layer1_20261015/v4/LAYER1_V4_COMPACT_CONTRACT_v1.json
- research/paper_e_layer1_20261015/v4/V4_GOVERNING_MANIFEST_v1.json
- research/paper_e_layer1_20261015/v4/run_v4.py
- research/paper_e_layer1_20261015/v4/fixtures/SYNTHETIC_FIXTURES_v1.json
- research/paper_e_layer1_20261015/v4/PREFLIGHT_RECEIPT_v1.json

CHALLENGE AND VERDICT PER ITEM (PASS / CONDITIONAL / FAIL):
1. Single authority: the manifest pins the contract and fixtures; no competing v4 contract exists.
2. Contract completeness: inputs pinned, held-out-only sample, closed reason codes, decision gate,
   stop conditions, zero-call budget, and checker-read-after-label-freeze policy are all present.
3. Preflight honesty: preflight PASS is reproduced from fixtures only; it does not read the real
   injection map, heldout labels, or checker verdicts.
4. Runner order: compute labels -> write labels_frozen hash -> only then read checker target.
   The heldout mode must not read dev labels for any decision.
5. Fixture coverage: direct E, non-target-empty E, harmful other-column H, target-empty U,
   target-collision U, tie U, injected-empty U, non-target-empty H are all covered.
6. Claim boundary: no population rate, OCR result, harmful blind spot, or Layer-2 activation is
   claimed before the heldout run and its post-result audit.

ALSO CHECK:
- Any scope change beyond the single frozen column-local rule = STOP.
- Any hidden use of checker verdicts before labels_frozen hash = STOP.
- Any path where changing fixtures or contract after preflight would not invalidate the run = FAIL.
- Recompute the preflight fixture results from the runner logic; report mismatches.

OUTPUT:
If write is permitted, write only:
`research/paper_e_layer1_20261015/v4/V4_LOOP_C_AUDIT_v1.md`
Otherwise include the full audit in your final reply and state write blocked.

End with `VERDICT: PASS / CONDITIONAL / FAIL`.

FORBIDDEN:
No heldout label computation; no checker read for labelling; no edits outside the audit file;
no git write; no model/network/training call beyond this audit.
