# Loop A Assignment - TAT-QA WP-1b (bounded fix + completion; NO MODEL CALLS)

CARD: research/tatqa_wp0_2026/wp1/loop_a_prompt_fix1.md | dispatched 2026-10-13 by Loop D after run-1 fail-closed.
ROLE: Loop A / GB10. Bounded completion of WP-1 after run 1 (`tatqa-wp1-20261013`) stopped with `SOFTWARE_NOT_QUALIFIED: hidden_gold_search`. Nothing else. Model calls = 0.

CONTEXT (read first; binding):
- Revision 1.1 in `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` Sec.4 SUPERSEDES Sec.3 obligation 2 only. Run-1 diagnosis: the check searched `late_value`/`early_value` (actor-visible table cells by design) inside the projection -> guaranteed false positive; the fail-closed stop was correct behaviour.
- Run-1 artifacts remain in `research/tatqa_wp0_2026/wp1/`; do not delete them (extend where the fix requires).
- Pinned inputs unchanged; re-verify the four hashes and the two counts before running (same as run 1).

TASK (bounded):
1. Update `_check_hidden_gold_search` in `run_fixtures.py` to revision 1.1:
   (a) forbidden-name search as before;
   (b) boundary-aware search for the `delta_source` and `delta_target` strings (as the checker renders them) across the FULL serialized projection for EVERY fixture - zero matches required; flanking characters outside {digits, `.`, `,`, `+`, `-`}; no length filter;
   (c) exclude `late_value`/`early_value` from the search set;
   (d) verify the fixture-design precondition per fixture (same boundary-aware search over raw table cells and period labels alone); if a collision exists, adjust ONLY the synthetic fixture numbers (keep the arithmetic correct).
2. Keep every other check and module unchanged. If the updated suite reveals any other genuine failure, stop and report it - do not weaken anything.
3. Re-run `python3 research/tatqa_wp0_2026/wp1/run_fixtures.py`. On PASS emit:
   - `research/tatqa_wp0_2026/wp1/PREFLIGHT_RECEIPT.json`
   - `data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json`
   - `research/tatqa_wp0_2026/wp1/WP1_RECEIPT.json`
   (schemas: per-obligation results, artifact hashes for checker/adapter/provenance/run_fixtures/fixtures/contract/preflight, cost model_calls=0, unverified items, deviations; run id `tatqa-wp1b-20261013`.)
4. Update `implementation_contract.md` with a revision addendum (corrected check + run-2 artifacts) and refresh `implementation_contract.sha256`; update the hash pins in `PREREG_DRAFT_SKELETON.md`.
5. Same write paths and forbidden list as run 1: no model/judge calls, no network, no services, no training, no commit/push, no edits to paper/, docs/, or pinned inputs, no candidate-item scoring (fixtures are synthetic).

STOP CONDITIONS: any genuine obligation failure -> `SOFTWARE_NOT_QUALIFIED` naming the failing item (never adjust a test to pass); hash mismatch -> `HASH_MISMATCH`; a forbidden action being required -> stop and report.

END: final message = status + receipt paths + one-line summary.
