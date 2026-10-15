# Paper E Layer-1 v2/v3 Branch Stop Record v1

> Status: `STOPPED_BY_GOVERNANCE` | Date: 2026-10-15
> Branch: independent task-level binding gold for frozen drift-v0 header-drift injections
> Decision rule applied: if an independent re-audit still finds a scientific scope change,
> STOP; do not keep repairing the preregistration.

## 1. What happened

- v1 (frozen plan + deterministic zero-call run) produced `GOLD_NOT_ESTABLISHED`:
  59 dev cases, E=12 / H=12 / U=35, U rate 0.593220 > 0.30.
- Independent audits then showed that 32/35 U labels came from empty headers elsewhere in the
  table, not from the target column. A dev sensitivity ("variant C") gave E=29 / H=23 / U=7,
  U rate 0.118644, but that dev result is public and cannot serve as confirmatory evidence.
- Three successive v2/v3 preregistration revisions were written to fix this. Each pre-result
  Loop C audit found a new specification/scope issue:
  1. v2 draft revision 1 -> CONDITIONAL (gate arity, non-exhaustive decision function,
     no-tuning list, missing stop, hashes, reason codes, arbitrary floors).
  2. v2 canonical revision 1 -> CONDITIONAL (K1-K6 clarifications).
  3. v2 canonical revision 2 -> CONDITIONAL (collision scope beyond design, dev stage
     non-confirmatory, manifest/banners).
  4. v3 held-out-only revision -> CONDITIONAL again (checker-read contamination channel,
     analysis scope shrink, compressed norm description, reason-code gaps).
- No v2/v3 label was ever computed, including for the held-out 59. No held-out outcome was read.

## 2. Why the branch stops

The branch hit the pre-declared stop rule. Continuing would mean a further prereg repair cycle
after an audit found scope changes. That is exactly the failure mode the rule was written to
prevent. The branch is therefore closed as a governance stop, not as a scientific negative
result. It must not be reported as "gold established" or "gold impossible".

## 3. What stands

- v1 result: `GOLD_NOT_ESTABLISHED` on the dev split under its frozen contract.
- v1 remains the only executed Layer-1 artifact.
- Dev sensitivity: `DEV_SENSITIVITY_NOT_CONFIRMATORY`; must not be used as v2/v3 evidence.
- Held-out 59: no labels, no verdict, no claim.
- Paper E manuscript, claim matrix, scope lock, and frozen numbers: unchanged.
- Layer 2: NOT authorized, NOT designed, NOT started.

## 4. Provenance artifacts

- v1 run: `research/paper_e_layer1_20261015/` (plan, generator, results, receipt, summary).
- v2 drafts and audit transcripts: `research/paper_e_layer1_20261015/v2/`.
- v3 drafts and final audit transcript: `research/paper_e_layer1_20261015/v3/`.
- Final v3 audit transcript:
  `research/paper_e_layer1_20261015/v3/LAYER1_V3_FINAL_AUDIT_v1.md`
  (raw launcher-log copy; sha256 recorded on disk).
- Prior independent dev audit with variant C:
  `docs/research/PAPER_E_LAYER1_LOOP_C_AUDIT_v1.md`.
- Governing manifest (now historical for this stopped branch):
  `research/paper_e_layer1_20261015/v3/GOVERNING_MANIFEST_v1.json`.

## 5. What a future attempt would need

A future attempt must not be a fourth patch of these drafts. It needs a new, single design pass
with:
- one authoritative contract from the start, no competing deltas;
- the checker read discipline, contingency/rates, and reason codes fully specified before any
  label;
- dev-only development and a genuinely untouched held-out confirmation split;
- an independent pre-result audit before any label, and a named stop code for scope changes.

Until then, Paper E stays as the current case study and no Layer-2 work starts.
