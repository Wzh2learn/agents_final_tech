# Paper E — Layer-1 Independent-Gold Design v1

> status: `DESIGN_PROPOSAL_AWAITING_FREEZE` | date: 2026-10-15 | author: Loop D
> advisor brief (2026-10-15): first close the question "can the task target be judged
> independently of the audited evaluator?" before any larger study.
> scope: design + execution/audit contract only. Runs no experiment here; changes no manuscript.

## 1. Decision this layer informs

Can we define, for the existing controlled perturbations, a **task-level gold that does not come
from the audited evaluator** — and if so, does the audited checker co-miss (false-negative) or
co-alarm (false-positive) against that gold in a way that would change a research judgement?

If YES -> proceed to Layer 2 (three-arm comparison of evaluation methods).
If NO  -> keep Paper E as the present case study; do not build a larger platform for it.

## 2. The circularity risk and how this design avoids it

The user's concern (自产自销): if the "correctness" of a case is decided by the same matcher/judge
we are auditing, the study proves only that our instrument agrees with itself.

This design avoids that in three independent ways:

1. **Truth source = the injection map, not the matcher.** Each injection entry carries
   `{uid, col, original, injected, type, variant, seed_component}` — the ground-truth fact that a
   specific source column's header was rewritten from `original` to `injected`. This is dataset
   truth, generated independently of the audited greedy matcher.
2. **Contract = task-level, stated before scoring, not the audited drop rule.** Harmfulness is
   judged under an explicit equivalence contract (Section 3) that a human can read; it is not the
   protocol's threshold predicate and not the judge's score.
3. **Zero model calls.** No judge is queried, so repeated LLM sampling cannot masquerade as gold.
   Cases the contract cannot decide are labelled `INSUFFICIENT` and routed to human adjudication,
   never auto-filled by a model.

## 3. Independent equivalence contract (the gold rule)

For a header-drift injection on a table, define the task as *field-level correspondence*: which
column of the source table does a header denote. Column **values are unchanged** by construction
for these families (mechanically re-verified per case). Therefore the task answer is unchanged
iff the perturbed header still denotes its own column.

Given the table's header set H (from the frozen source tables) and the injection entry
(original `o`, injected `i`, column `c`):

- `LEGAL_VARIATION` (E) — canonical correspondence preserved. A fixed, non-audited normalization
  `norm(.)` satisfies: `norm(i)` uniquely matches `norm(o)` (i.e. `norm(i)==norm(o)`), or else
  `i` is a unique nearest neighbour of `o` in H under the fixed rule with no tie, and the target
  column's values are byte-identical to the clean column's values.
- `HARMFUL_ERROR` (H) — the perturbation breaks identity: under the same fixed rule, the injected
  header binds to a **different** column than `c`, or fails to bind at all, such that a downstream
  aggregation over the table would consume different values.
- `INSUFFICIENT_EVIDENCE` (U) — the fixed rule is ambiguous (a tie among candidate columns), the
  table has duplicate/colliding headers, the header is empty after normalization, or the
  value-invariance assumption does not hold for this case.

`norm(.)` is a single, fully specified canonicalization (case fold, whitespace collapse, and one
fixed punctuation/underscore policy) frozen in the analysis plan before any case is read. It is
**not** the audited greedy matcher and is **not** tuned on results.

## 4. Data inputs (read-only, frozen)

| Input | Path (GB10 production) | Notes |
|---|---|---|
| injection map | `data/research/drift_v0/output/injection_map.json` | 118 entries, 95 uids, sha256 `d7612405…` |
| source tables | `data/research/drift_v0/input/tatqa_tables.json` | sha256 `3e7e0568…` |
| injected tables | `data/research/drift_v0/output/injected_tables.json` | for value-invariance checks |
| audited checker verdict | `logs/graph/eval/t2_visibility_sensitivity.json` | the comparison target, NOT the gold |

These files are gitignored and present on GB10 production only; the run therefore executes on GB10.

## 5. Procedure

1. Freeze `norm(.)`, the tie policy, the U-rules and a dev split rule in an analysis plan *before*
   reading cases. Dev split = outcome-blind hash of injection id (e.g. first N by
   `sha256(id) mod k`), frozen.
2. For each dev case: read `{uid, o, i, c, type}`, recompute value-invariance (bytes of the
   column's values clean vs injected), apply the contract, emit one label in {E, H, U}.
3. Pull the audited checker's frozen verdict for the same injection id (visible / blind).
4. Build the 2×3 contingency (checker verdict x gold label) and report: P(gold=H | checker=blind)
   = checker co-miss, P(gold=E | checker=visible) = checker co-alarm, and the U rate.
5. Write a receipt with input hashes, the frozen rule text, and every per-case row.

## 6. Outputs

- `LAYER1_ANALYSIS_PLAN_v1.md` (frozen rule + dev split; written first)
- `LAYER1_RESULTS_v1.json` (per-case rows + contingency + rates)
- `LAYER1_RECEIPT_v1.json` (input hashes, rule hash, counts, calls=0)
- `LAYER1_SUMMARY_v1.md` (feasibility verdict: is the independent gold usable?)

## 7. Stop rules and budget

- Model calls: **0**. Judge calls: **0**. Network: **0**. Production endpoints: not touched.
- Read-only over frozen inputs; write only under the run directory.
- STOP and report (do not fix, do not expand) if: an input hash mismatches the expected value; a
  case cannot be decided by the contract and is not clearly `U`; the dev split rule is ambiguous;
  or the U rate exceeds a pre-set ceiling (proposed 30%) such that the contract is not usable.
- If >30% U, Layer 1 conclusion is "independent gold NOT established on this corpus" -> keep the
  present case study; do not start Layer 2.

## 8. What would falsify the layer

- If almost every blind case is `LEGAL_VARIATION` under an independent contract, then the checker's
  non-response is *correct*, and the "harmful blind spot" reading is unsupported — an important,
  publishable boundary result, not a failure.
- If a meaningful share of blind cases are `HARMFUL_ERROR`, that is the first independent evidence
  that the observation surface misses task-relevant change — the Layer-2 premise.
- Either way the result is reported as-is; the classification rule is never retuned to produce a
  preferred mix.

## 9. Loop A / Loop C contract summary

Loop A (execute, on GB10): implement the contract and dev split exactly as frozen; run
deterministic, zero-call; emit the four artifacts; self-check input hashes and counts.

Loop C (independent pre-result audit, read-only): challenge (a) whether `norm(.)` and the tie
policy are genuinely independent of the audited matcher; (b) whether the dev split is outcome-blind;
(c) whether the E/H/U rules are stated before results and not fitted; (d) whether any `U` case is
silently auto-labelled; (e) whether the contingency counts are arithmetically correct.
