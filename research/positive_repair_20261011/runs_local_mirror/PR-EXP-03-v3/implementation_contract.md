# PR-EXP-03 v3 Implementation Contract (for Loop A)

> date: 2026-10-11 | author: Loop D | for: Loop A implementation + EXECUTION_PREFLIGHT | authority: PR-EXP-03_prereg_v3.md + PR-03_v3_design_decision_v1.md
> This is a specification. It does NOT authorize a formal run: Loop A implements, then runs EXECUTION_PREFLIGHT (toy/fixture only), then Loop C pre-result audit, then the owner/manager authorizes the formal run.

## 1. Environment and inputs
- Run on GB10 (the authoritative host): repo `wzh/projects/agents_final_tech` at the frozen revision.
- Inputs (paths frozen before outcomes):
  - Round-1 P1 manifest: `research/positive_repair_20261011/runs_local_mirror/PR-EXP-03/p1_generation_manifest.json`.
  - Frozen carriers: the drift-v0 tables and injection map (GB10: `data/research/drift_v0/...`).
  - Canonicalizer + field-hit matcher: `scripts/m1_statement_parser.py` (`map_headers`), pinned by host-raw sha256.
  - Checkpoint config: `config/eval_checkpoint_trees.json`.
- Deterministic; no network; no model/endpoint calls; zero writes to frozen artifacts.

## 2. Oracles (single changed factor = the oracle's measurement object)
- O_FH (BEFORE): field-hit response = 1 if injected hit-rate < baseline hit-rate else 0. Where the header is entirely empty, the semantic value is zero observable hits -> hit-rate 0 -> response 0 (defined by task semantics, not a per-case patch).
- O_TS (AFTER): structural signature = (column_count, ordered positional header-token sequence under the pinned canonicalizer with "" allowed as a token, row_count). Response = 1 iff the injected signature differs from the baseline signature, else 0. Total (defined on every P1 case).

## 3. Population and split
- P1 carriers per the round-1 manifest, incl. the 2 all-empty-header tables (RETIRED; retained under PATH A).
- Arms: A0 identity (expect 0), A1 value-only (expect 0), structural control set (expect 1).
- Split: frozen rule (sorted carrier UID index modulo k), group-disjoint, assigned before reading outcomes.

## 4. Non-degeneracy gate (before any P1 outcome)
(a) O_TS fires on the structural control set;
(b) O_TS returns 0 on A0 and A1;
(c) O_TS differs from O_FH on >=1 P1 case.
Fail any -> INVALID (gate), record provenance.

## 5. Execution preflight (10 checks; toy/fixture only; zero held-out reads)
Per `execution_preflight/EXECUTION_PREFLIGHT_SPEC_v1.md`. Emit `execution_preflight/PR-EXP-03_v3_preflight_receipt.json` with per-check PASS/FAIL. Target: `EXECUTION_PREFLIGHT_PASS`.

## 6. Formal run outputs (only after Loop C pre-result audit PASS)
- `result.json`: per-case O_FH/O_TS responses, coverage, stage/family components, unique catches, M1 regression, cost.
- `metrics.json`: primary (incremental coverage delta; stage/family diagnosability delta) and secondary.
- `receipt.json`: harmonized provenance (input hashes, split map, gate result, prereg hash).
- `undefined_cells.json`: must be empty under PATH A; if non-empty, that is the NOT_EVALUABLE trigger.

## 7. Classification
POSITIVE / NULL / NEGATIVE / INVALID / NOT_EVALUABLE (never merge NOT_EVALUABLE into NULL). POSITIVE requires the gate to pass AND a non-source-local held-out diagnostic gain AND no unacceptable M1 regression AND comparable cost.

## 8. Stop condition
If v3 stops at schema / gate / provenance / undefined-domain WITHOUT entering effect measurement -> `PR-03 = NOT_EVALUABLE_FINAL`, branch stopped, no fourth repair.

## 9. Provenance
Every output records: prereg sha256 (bbc9910c2d0b104897af6737393583c9b2efaa2e27ec328460b504d6072fa6b1, placeholder convention), input file sha256s, git revision, and the exact command line.