# WP-0 TAT-QA Loop A Execution Package v1 (DRAFT - NOT DISPATCHED)

> date: 2026-10-13 | author: Loop D | status: `READY_TO_DISPATCH_AFTER_APPROVAL` | zero model calls; fixture-first; no training.
> parents: [adapter/checker contract](WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md), [evaluation protocol](WP0_TATQA_EVALUATION_PROTOCOL_v1.md), [task card](../archive/2026-10-20_entry_consolidation/thesis_experience_v1_task_card.md) Sec.3-4, [exec constraints](../../scripts/graph/loop_a_exec_constraints.md), [launcher](../governance/loop_ac_launcher_v1.md).

## 1. Preconditions (all required before dispatch)

1. Advisor: G-RQ accepted (QUALIFIED_CONDITIONAL -> formal allowance for WP-1).
2. Owner/advisor: write-path permission for `research/tatqa_wp0_2026/wp1/` and `data/research/tatqa_wp0_2026/wp1/` on GB10.
3. Actor freeze plan approved for the later stages (F1); WP-1 itself needs no model.
4. Dispatch via `scripts/graph/loop_ac_launcher.sh` (the designed channel), prompt file in-repo, receipt discipline per the launcher doc.

## 2. Work items (all reversible; fixture-first; stdlib-only where possible)

| # | Item | Deliverable | Acceptance |
|---|---|---|---|
| W1 | Checker implementation | `research/tatqa_wp0_2026/wp1/checker.py` (+ tests) | matches hand-computed values on 5 fixtures incl. parentheses-negative and thousands separator; taxonomy classes incl. `REFUSED`/`UNKNOWN` |
| W2 | Adapter implementation | `research/tatqa_wp0_2026/wp1/adapter.py` (+ tests) | byte-identical prompts for same item+arm; hidden-gold search clean; opaque ids; no arm-dependent truncation |
| W3 | Fixture suite (A5 Sec.3, six obligations) | `research/tatqa_wp0_2026/wp1/fixtures/` + receipt | all six obligations PASS, incl. E/C token-delta computation; fail-closed |
| W4 | Execution preflight | `research/tatqa_wp0_2026/wp1/PREFLIGHT_RECEIPT.json` | required files exist; schema fields match runtime payload; scorer defined on allowed inputs; provenance writer attributes to the task; metric pipeline runs on NON-SCIENTIFIC fixtures; no held-out reads |
| W5 | Freeze assembly (with Loop D) | prereg draft + hash pins | protocol/item/split/actor/checker hashes resolve |

## 3. Non-goals / prohibitions

- No model calls, no episode collection, no context-block construction, no training (Memory/SFT/DPO), no production services, no change to any frozen Paper E asset.
- No edits outside the two write paths above; receipts required for every claim; `SOFTWARE_NOT_QUALIFIED` stop on any fixture failure (do not "try it out" with a model).

## 4. Stop and escalation

- Any acceptance failure -> stop, report `SOFTWARE_NOT_QUALIFIED` with the failing fixture.
- After W1-W5 PASS + C pre-result audit PASS -> only then request pilot (WP-2) authorisation; budget/window must be bound first.

## 5. Dispatch template (when approved)

```
bash scripts/graph/loop_ac_launcher.sh start a tatqa-wp1-<date> research/tatqa_wp0_2026/wp1/loop_a_prompt.md 14400
```

Prompt file must state: scope = W1-W5 only; write paths; receipts; fail-closed; no model/services.

## 6. Dispatch log

| Run | Task id | Window (UTC) | Result |
|---|---|---|---|
| 1 | `tatqa-wp1-20261013` | 10:30:27 -> 10:53:38 | `SOFTWARE_NOT_QUALIFIED: hidden_gold_search` (fail-closed; no receipts generated; root cause: the check searched actor-visible late/early cells -> false-positive class; spec clarified as revision 1.1, `WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` Sec.4; no test weakened) |
| 2 | `tatqa-wp1b-20261013` | 10:59:26 -> 11:12:28 | **PASS** - all six obligations + preflight; receipts `WP1_RECEIPT.json` / `PREFLIGHT_RECEIPT.json` / `FIXTURE_RECEIPT.json`; model_calls=0; Loop D re-verification: hashes recompute + obligations re-executed PASS. |
| audit | `tatqa-wp1-audit-20261013` | 11:20:45 -> 11:37:54 | CONDITIONAL (items/spec-compliance/independence; scope PASS). Prescribed fixes: needle canonicalization + mandatory positive control + taxonomy/receipt precision -> spec rev 1.2 -> run 3 (`tatqa-wp1c-20261013`). |
| 3 | `tatqa-wp1c-20261013` | 11:45:10 -> 12:10:35 | **PASS** (spec rev 1.2): seven obligations incl. `hidden_gold_positive_control`; 28 fixture-arm determinism checks; `fixture_receipt` pinned; canonical/mirror byte-identical; Loop D re-verification: hashes recompute + obligations re-executed PASS on GB10 (local Python 3.9 re-run: 6/7, control blocked by `zip(strict=)` >=3.10 - environment note only). |
| re-audit v2 | `tatqa-wp1-reaudit-v2-20261013` | 12:17:47 -> 12:36:44 | ITEMS **PASS** / SCOPE **PASS** / SPEC CONDITIONAL / INDEPENDENT CONDITIONAL. All five prior prescriptions closed; one residual filed (`correct` unit-gate asymmetry) with resolution policy -> WP-2 freeze list. Closure: `WP1_COMPLETION_RECORD_v1.md`. |
