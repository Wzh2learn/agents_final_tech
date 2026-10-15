ACK FIRST LINE: ACK pe-l1-v4-audit-v4: Loop C independent auditor

ROLE: Loop C independent auditor on GB10. Read-only. Do not modify any v4 file.

GOAL:
Narrow final audit of v4 v3 artifacts. Verify only that the previous audit's D1-D5 defects are
closed and that the preflight lock prevents contract/fixtures/runner/receipt drift before the
held-out run. Do not re-design the science and do not compute any held-out label.

SINGLE OPERATIVE PIN BLOCK:
- contract: research/paper_e_layer1_20261015/v4/LAYER1_V4_COMPACT_CONTRACT_v3.json
  sha256 = 322c3b380d9f36d2603e89eef49f296d86c012497b442ec9c77b36c0adbdc8aa
- runner: research/paper_e_layer1_20261015/v4/run_v4.py
  sha256 = 55893b65f2d4aa201f1ecdb24438a33490cc350a0311ac58d6d0f69ba86d38d4
- manifest: research/paper_e_layer1_20261015/v4/V4_GOVERNING_MANIFEST_v3.json
  sha256 = b76ecd083269ab1005b7b3aa36e5bf5cd02905437bcf569cbee4454076211f7f
- fixtures: research/paper_e_layer1_20261015/v4/fixtures/SYNTHETIC_FIXTURES_v3.json
  sha256 = 0d3f023b04ced843355c58999af0c6d9af3e959a2a4852169da951b577555acd
- preflight receipt: research/paper_e_layer1_20261015/v4/PREFLIGHT_RECEIPT_v1.json
  sha256 = 142cf6adb5144e320d62eaf42b346cc1c8c54f15b979858f2e8107bfe049c7f1
- preflight lock: research/paper_e_layer1_20261015/v4/PREFLIGHT_LOCK_v1.json
  sha256 = fb84e72df29a11a2d1071f2d5c12f30b93c9a42dcb7aa30cf85706d337b1be29

CHECK ONLY:
1. D1: contract reason_codes match emitted runner codes; no phantom or unreachable closure claim.
2. D2: manifest pins the runner; run_heldout verifies the runner hash before any label.
3. D3: PREFLIGHT_LOCK_v1.json is required by run_heldout and preflight refuses overwrite unless explicitly overridden.
4. D4: misleading self-attested booleans are removed; no stale audit_state.
5. D5: exactly one operative pin set; stale v1/v2 pins are not presented as current.
6. Lock chain: current receipt and manifest hashes match the lock; heldout cannot start if they drift.
7. Scope: label rule remains the single frozen column-local rule; no heldout label exists.

OUTPUT:
Write only if permitted: research/paper_e_layer1_20261015/v4/V4_LOOP_C_AUDIT_v4.md
Otherwise give the full audit inline and state write blocked.

End with VERDICT: PASS / CONDITIONAL / FAIL.

FORBIDDEN:
No heldout label computation; no checker verdict read for labelling; no edits outside the audit
file; no git write; no model/network/training call beyond this audit.
