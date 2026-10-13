# Loop A Assignment - TAT-QA WP-1 (thin runner: checker + adapter + fixtures + preflight; NO MODEL CALLS)

CARD: research/tatqa_wp0_2026/wp1/loop_a_prompt.md | dispatched 2026-10-13 by Loop D under owner approval.
ROLE: Loop A / GB10 implementation. You implement ONE bounded software package (WP-1) plus its non-scientific fixture checks. Nothing else. Model calls = 0. This card authorises NO pilot run and NO episode collection.

CONTRACT (read first; binding):
- docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md  (THE specification for checker/adapter/fixtures)
- docs/research/WP0_TATQA_LOOP_A_EXECUTION_PACKAGE_v1.md  (W1-W5 + acceptance criteria)
- docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md  (context only; do not execute anything)
- data/research/tatqa_wp0_2026/origin_manifest.json, candidate_items_v1.json, GENERATION_RECEIPT.json  (READ-ONLY)
- data/research/tatqa_raw_2026/tatqa_dataset_train.json, tatqa_dataset_dev.json  (READ-ONLY)

Project dir (your cwd): /home/testuser/wzh/projects/agents_final_tech
Work dir (create; NEW): research/tatqa_wp0_2026/wp1/
Data out (create; NEW): data/research/tatqa_wp0_2026/wp1/

PINNED INPUTS (verify BEFORE anything else; mismatch -> STOP, report HASH_MISMATCH):
- candidate_items_v1.json sha256 bc55fe7a53381f32e5d84ff6c17ced18ec72fd322f98a9f80c4eccb714caac12
- origin_manifest.json sha256 3718e6fef4d52bec0c1c29b47ba9ab60e298754b9e8527835d09c9d223d70cea
- tatqa_dataset_train.json sha256 2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69
- tatqa_dataset_dev.json sha256 8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5
- expected counts: 60 candidate items; 182 origins.

PRE-RUN (mandatory order):
1) Verify the four hashes (sha256sum) and the two counts from GENERATION_RECEIPT.json.
2) Write research/tatqa_wp0_2026/wp1/implementation_contract.md first: module list, function signatures, fixture plan, receipt schema, exact commands you will run; hash the contract before running anything.
3) Implement W1-W5, then run ONLY the synthetic fixture suite.

WORK ITEMS (spec = adapter/checker contract; acceptance = execution package Sec.2):
W1 checker.py - gold recomputed from table cells (strip thousands separators; parentheses = negative), scale conversion (thousand->unit, million->thousand, billion->million, percent->percent), outcome taxonomy including correct_other_form / REFUSED / UNKNOWN; gold exists before any answer is read.
W2 adapter.py - deterministic actor-visible projection (verbatim, no truncation), fixed answer format, hidden fields (gold etc.) never leaked, opaque item/origin ids, byte-identical prompt for the same item+arm; arm context hooks for B/E/C/S as typed placeholders only (real experience blocks are NOT built here).
W3 fixtures/ + run_fixtures.py - the six obligations: (1) byte-equal prompts; (2) hidden-gold string search clean; (3) >=5 hand-built recompute fixtures incl. one parentheses-negative and one thousands-separator case; (4) the four scale conversions; (5) UNKNOWN + REFUSED classification; (6) E/C context token-delta accounting. SYNTHETIC fixtures only; never read held-out outcomes.
W4 PREFLIGHT_RECEIPT.json - required files exist; schema field names match the runtime payload; checker defined on all allowed inputs; group/split ids resolve; provenance writer attributes to this task; the metric pipeline runs end-to-end on NON-SCIENTIFIC fixtures; no held-out result read.
W5 PREREG_DRAFT_SKELETON.md + hash pins (checker/adapter/fixtures/preflight hashes); actor fields marked PENDING (advisor selection; do NOT touch model files or weights).

STYLE: python3 stdlib only; LF outputs; tests runnable via `python3 research/tatqa_wp0_2026/wp1/run_fixtures.py`; no pytest dependency.

FORBIDDEN: model/judge calls; network; services/databases; training; commit/push; editing paper/, docs/, pinned inputs, or anything outside the two write dirs; scoring candidate items (READ allowed, SCORE not allowed; fixtures are synthetic); running loop_b_verify.sh; fabricating or weakening any test.
STOP CONDITIONS: hash mismatch -> HASH_MISMATCH; any fixture obligation fails -> STOP and report SOFTWARE_NOT_QUALIFIED naming the failing item (never adjust the test to pass); a forbidden action being required -> stop and report.

OUTPUTS: the files above + research/tatqa_wp0_2026/wp1/WP1_RECEIPT.json (valid JSON, no fences): task, start/end UTC, re-verified input hashes, artifact hashes (checker/adapter/fixtures/preflight/contract), per-obligation fixture results, preflight results, cost (model_calls=0, endpoint_calls=0), unverified items, deviations (expect none).

END: final message = status + receipt path + one-line summary.
