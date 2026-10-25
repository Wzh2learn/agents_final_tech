# P0 Impact Return

Date: 2026-10-25

## Scope

P0 is a zero-model-call contract repair and post-hoc development replay. It
does not add a confirmation set, a third Paper E case, or a new trained
method. Hidden reference programs and answers are used only for retrospective
scoring, never as policy or repair-selection features.

## Corrected Contracts

1. `source_role_contract_v3.py` now applies average-count correction only to
   average/mean questions, treats 2018 through 2020 as three periods, and is
   idempotent for an existing structural constant.
2. `analyze_binding_residual_v3.py` now binds leading multi-row header labels,
   including periods and units, to the columns/cells they describe.
3. `semantic_repair_delivery_v3.py` now scores each policy against its own
   selected output. A repair is valid only when the repaired program is
   executable, reference-valid, and passes the complete visible semantic
   check.

## Unaffected Historical Results

- Numeric `program_correct` values in the frozen V4/V5 result files are not
  rewritten by P0. A numeric result remains a numeric result, not a complete
  semantic gold label.
- The historical V4/V5 training receipts and checkpoint identities remain
  unchanged. P0 did not retrain or reweight any checkpoint.
- The historical stale-table withdrawal and source-key isolation corrections
  remain in force.

## Changed Development Replay

The zero-call replay on the 72 ordinary frozen outputs changed the visible
semantic decisions as follows:

| State | Before P0 | After P0 |
|---|---:|---:|
| VALID | 31 | 48 |
| UNRESOLVED | 36 | 19 |
| INVALID | 5 | 5 |

The ordinary semantic policy consequently accepts 48 outputs rather than 31,
with 36 correct and 12 numerically wrong accepted outputs. This raises correct
coverage from 21/72 to 36/72, but the conditional accepted-wrong rate remains
25.0%. The repaired representation is therefore useful for reducing
information-loss false alarms; it is not yet a safe delivery policy.

`semantic_repair_rule` and `semantic_rule` remain numerically identical
because none of the 72 natural candidates triggers the bounded structural
denominator repair. This is no evidence that repair actions help.

## Evidence Identity and Remaining Uncertainty

- The P0 replay is `POST_HOC_DEVELOPMENT_REPLAY`.
- Multi-row header recovery is deterministic visible-evidence restoration.
- The `56/72` ordinary numeric outputs remain numeric identities. They have
  not been promoted to complete semantic or action gold.
- Algebraic equivalents, alternative valid evidence sets, unit semantics, and
  task-level usefulness still require the Experiment A and delivery analyses.
- The repaired checker must not be used as a hidden-reference feature. It can
  only inspect the question, visible table, recovered header information, the
  candidate, and deterministic execution traces.
