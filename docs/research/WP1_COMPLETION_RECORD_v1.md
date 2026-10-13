# WP-1 Completion Record v1 (TAT-QA thin runner)

> date: 2026-10-13 | author: Loop D | status: `WP-1 DELIVERED / SOFTWARE PASS (contract-scoped) / WP-2 NOT AUTHORISED`
> owner approval: "wp-1 approved" (2026-10-13). This record certifies software only; it does not authorise any pilot, episode collection, actor freeze, or training.

## 1. Execution chain

| Step | Task id | Window (UTC) | Result |
|---|---|---|---|
| run 1 | `tatqa-wp1-20261013` | 10:30:27 -> 10:53:38 | FAIL-CLOSED `SOFTWARE_NOT_QUALIFIED: hidden_gold_search` (over-broad check searched actor-visible cells; correct stop; no receipts generated, no test weakened) |
| spec rev 1.1 | - | - | hidden-gold search clarified (Sec.4) |
| run 2 | `tatqa-wp1b-20261013` | 10:59:26 -> 11:12:28 | PASS - six obligations + preflight; receipts |
| audit v1 | `tatqa-wp1-audit-20261013` | 11:20:45 -> 11:37:54 | CONDITIONAL (scope PASS). Prescribed: needle canonicalization + positive control + taxonomy/receipt precision |
| spec rev 1.2 | - | - | needle canonicalized; positive control mandatory; taxonomy extended to eight classes; receipt precision (Sec.5) |
| run 3 | `tatqa-wp1c-20261013` | 11:45:10 -> 12:10:35 | PASS - seven obligations (incl. `hidden_gold_positive_control`); 28 fixture-arm determinism checks; `fixture_receipt` pinned; canonical/mirror byte-identical |
| re-audit v2 | `tatqa-wp1-reaudit-v2-20261013` | 12:17:47 -> 12:36:44 | ITEMS PASS / SCOPE PASS; SPEC CONDITIONAL on one filed residual; INDEPENDENT CONDITIONAL |

## 2. Deliverables (tracked; hashes = run-3 `WP1_RECEIPT.json`)

- Code: `research/tatqa_wp0_2026/wp1/{checker,adapter,provenance,run_fixtures}.py`, `fixtures/synthetic_fixtures.json`
- Receipts: `WP1_RECEIPT.json`, `PREFLIGHT_RECEIPT.json`, `FIXTURE_RECEIPT.json` (repo mirror; canonical copy = `data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json` on GB10)
- Contracts: `implementation_contract.md` (+sha256), `PREREG_DRAFT_SKELETON.md` (`DRAFT - NOT READY`; protocol/item/split/actor PENDING)
- Run logs: `run_logs/` (runs 1-3 + audit v1 + re-audit v2; force-added evidence under the `*.log` ignore rule)
- Spec: `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` rev 1.2

## 3. Verification chain

- Loop A receipts: 8 artifact hashes + 4 pinned input hashes + counts 60/182; `cost = {model_calls: 0, endpoint_calls: 0}`; no commit/push by Loop A.
- Loop D: committed-blob bytes recompute against receipts; obligations re-executed PASS on GB10 (Python 3.12); local (Python 3.9) re-run passed 6/7 - the positive control is blocked below 3.10 by `zip(..., strict=False)` (declared runtime 3.12; environment note only, consistent with the contract).
- Loop C: audit v1 (CONDITIONAL, all prescriptions closed in run 3) and focused re-audit v2 (items/scope PASS; residual below).

## 4. Filed residuals (resolution policy set; implement at the WP-2 prereg freeze)

1. `correct-path-unit-gate-unequal-between-equivalent-outcome-classes` (re-audit v2): the frozen checker gates `correct` on an answer-unit match while `correct_other_form` ignores unit; the spec text and implementation-contract rule 7 do not state the unit conjunct; no fixture exercises the case. **Resolution policy (proposed for ratification at the freeze): align upward - the evaluation protocol defines correctness as including unit and period, so the unit conjunct is added to every correct-class outcome with a dedicated fixture case and a recorded change note. The frozen WP-1 runner is not modified further.**
2. `leak-guard-needle-blind-to-alternate-numeric-renderings` (secondary, spec-level): needles do not enumerate `1,300` / `1.3e3` / `001300` renderings - hardening listed for the same freeze.
3. `gold_delta_source_unit` naming trap and `target_unit` absent from all 60 candidates (identity conversions) - both PENDING at item freeze (spec rev 1.2 Sec.5(f)).

## 5. What this certifies / does not certify

- Certifies: the thin runner (checker + adapter + fixtures + preflight) satisfies the contract on synthetic fixtures; receipts and hashes resolve; scope discipline held (no model calls, no candidate scoring, no network).
- Does NOT certify: any scientific effect; any authorisation for the pilot (WP-2), episode collection, actor freeze, or training. The prereg skeleton remains `DRAFT - NOT READY`.

## 6. Next gate (owner/advisor)

A WP-2 pilot request requires: feedback-right contract blanks decided; actor revision chosen + MODEL_GO; budget/window bound; the freeze checklist above resolved; the prereg frozen with hash pins; a C pre-result audit. Until then, nothing runs.
