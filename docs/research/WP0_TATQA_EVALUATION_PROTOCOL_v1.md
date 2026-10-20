# WP-0 TAT-QA Evaluation Protocol v1 (SPEC)

> date: 2026-10-13 | author: Loop D | status: `SPEC_ONLY - NOT EXECUTABLE` | no experiment, no model call, no training.
> parents: [task card](../archive/2026-10-20_entry_consolidation/thesis_experience_v1_task_card.md) Sec.2-4, [blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md) Sec.2, [package](WP0_TATQA_PACKAGE_v1.md) Sec.5, [adapter/checker contract](WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md). Numbers below are inherited, not new.

## 1. Question and scope

In a fixed actor / tool / budget setting, does providing related real execution experience from other origins improve answer correctness (including unit and period) and matched execution behaviour on new-origin two-period table-calculation tasks? This protocol covers the minimal validation (WP-2) only; it does not test feedback-construction algorithms, memory updating, parameter learning, or adaptation claims.

## 2. Population and units

- Item pool: the frozen candidate list (60 items / 60 distinct origins; `data/research/tatqa_wp0_2026/candidate_items_v1.json`; gold recomputed by the checker from cells).
- Independent unit of analysis: the **origin** (raw record). Not the item, not the repeat.
- Splits (sizes inherited from the card/blueprint): history = 8 episodes from >= 4 origins; development = 4 tasks from >= 2 origins; pilot = 16 tasks from **8 unseen origins** (2 tasks per origin), each run twice.
- Isolation: test origins share no origin with history/development; near-duplicate isolation across arms; test gold never enters any context.

## 3. Arms (frozen definitions)

| Arm | Context | What it isolates |
|---|---|---|
| B | none | base capability and headroom |
| E | 1-2 related real executed episodes (other origins) | effect of the experience package vs B |
| C | matched unrelated experience, same format; E/C context token delta <= 5% | whether the *relatedness* matters |
| S | static unit/period rules frozen at development | whether a cheap non-experience rule already explains gains |

All arms receive the same complete task evidence; no arm-dependent table truncation. One actor revision (see freeze plan), two model calls per episode (plan -> tool execution -> consume result), reset between items, no memory write-back.

## 4. Calls and budget (inherited; hard)

4 arms x 16 tasks x 2 repeats = 128 episodes; <= 256 evaluation requests; history+development <= 40; transport retries <= 4; **hard cap 300 actor request attempts, 0 judge calls**. Input/output caps and the 600-token experience block per the card Sec.3.4.

## 5. Endpoints and reporting

- Primary: per-item outcome class from the checker taxonomy (`correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong`, `regressed`, `refused`, `unknown`).
- Effects: per-origin paired differences `E-B`, `E-C`, `E-S`, `C-B`; list every origin-level difference explicitly; count corrections, regressions, refusals, UNKNOWN; report token/cost accounting per arm.
- Uncertainty: origin-level bootstrap CI (method declared in the prereg); no new significance thresholds; UNKNOWN stays a first-class state.
- Honesty rules: no pooled success showcase; behaviour change is reported but never asserted as causal by itself; window/scale of the pilot explicitly not extrapolated.

## 6. Gates and stop rules (inherited; unchanged)

| Outcome | Ruling |
|---|---|
| `E-B` and `E-C` each >= +12.5pp, >= 3 net-positive origins, no origin > 50% of its arm's corrections, both repeats non-reversing, behaviour consistent | `CONTINUE_EXPLORATORY` (apply for baseline/necessity comparison only) |
| B perfect on both repeats; leakage or bridge failure; B ceiling | `STOP_THIS_PANEL` / invalid per cause; do not add difficulty to hunt an effect |
| S solves everything | `NEW_METHOD_NOT_NECESSARY_ON_THIS_PANEL` |
| Anything else | `UNDETERMINED` (no negative/equivalence claim) |

## 7. Preregistration checklist (what must be frozen before the first model call)

1. This protocol (hash) + arm definitions.
2. Frozen item list + splits (origin-disjoint, opaque ids) + near-duplicate check receipt.
3. Actor freeze receipt (revision + settings + tool hash).
4. Checker/adapter versions + fixture PASS receipt.
5. Feedback-right contract (approved) + episode pool manifest (if E/C are populated).
6. Analysis script hash + bootstrap settings.
7. Budget/window binding (owner/advisor).

## 8. Non-goals

No training (Memory/SFT/DPO), no production integration, no long-horizon tasks, no new domains, no method-novelty claim. Executing anything here requires the WP-1 software gate and the owner/advisor window.
