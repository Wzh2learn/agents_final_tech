# Loop C independent audit (read-only) - TAT-QA WP-1 (checker + adapter + fixtures + preflight)

You are **Loop C**: an independent reviewer. READ-ONLY: do not modify files, commit, push, create runners, or call services. Do not trust the prompt or any summary; verify from the artifacts.

Repo root: `wzh/projects/agents_final_tech`

## Context
Loop A implemented the WP-1 thin runner under owner approval: run 1 (`tatqa-wp1-20261013`) stopped fail-closed on the hidden-gold check (over-broad search set; correct stop); spec revision 1.1 clarified the check; run 2 (`tatqa-wp1b-20261013`) completed the bounded fix. Your job: audit the FINAL artifacts against the binding specification (including revision 1.1) and report verdicts.

## Authorised scope (read-only)
- `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` (THE specification)
- `docs/research/WP0_TATQA_LOOP_A_EXECUTION_PACKAGE_v1.md` (W1-W5, acceptance)
- `research/tatqa_wp0_2026/wp1/` (implementation_contract.md + .sha256, checker, adapter, fixtures, run_fixtures.py, PREFLIGHT_RECEIPT.json, WP1_RECEIPT.json, PREREG_DRAFT_SKELETON.md)
- Pinned inputs (read-only): `data/research/tatqa_wp0_2026/` receipts; raw archives headers only if needed.

## Checks
1. Receipts: `WP1_RECEIPT.json` is valid JSON; declared artifact hashes recompute (`sha256sum`); the four pinned input hashes match; counts 60 items / 182 origins.
2. The six fixture obligations (contract Sec.3) are each present and not weakened: byte-equal prompts; hidden-gold search; >=5 hand-built recompute fixtures incl. parentheses-negative + thousands separator; the four scale conversions; UNKNOWN/REFUSED classification; E/C token-delta accounting. Quote the code/evidence for each.
3. Checker: gold is computed before any answer is read; taxonomy classes per contract; spot-check 2-3 fixture recomputations by hand.
4. Adapter: hidden fields never leak; opaque ids; no arm-dependent truncation; fixed answer format; determinism claim credible.
5. Preflight: each claim in `PREFLIGHT_RECEIPT.json` is supported by an artifact or a runnable check.
6. Scope discipline: no model/judge calls, no network, no services; writes confined to wp1 dirs; candidate items were not scored (fixtures are synthetic). Note anything suspicious.
7. If `python3` execution is denied by your permission gate, replicate statically and say so; Loop D runs the suite natively.

## Output (stdout only)
Per check: verdict + file:line or hash evidence. Then exactly:
`LOOP_C_WP1_ITEMS_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_WP1_SPEC_COMPLIANCE_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_WP1_SCOPE_VERDICT = PASS | CONDITIONAL | FAIL`
`LOOP_C_WP1_INDEPENDENT_VERDICT = PASS | CONDITIONAL | FAIL`
and one closing line naming the single weakest point.
