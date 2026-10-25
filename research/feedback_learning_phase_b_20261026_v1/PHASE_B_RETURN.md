# Phase B Research Return

Goal ID: `FEEDBACK_LEARNING_PHASE_B_20261026`
Date: 2026-10-26, Asia/Shanghai
Status: `PHASE_B_EVIDENCE_EXIT_COMPLETED_CURRENT_R_E_STOPPED`

## Executive Decision

- B1 supervision qualification: passed only for
  `REFERENCE_DERIVED_VISIBLE_SET_BINDING_REVISION_SUPERVISION` on exposed
  development data. It is not feedback-derived learning.
- B2/B2B same-start development: real R/E training completed, but the current
  full-program R and restricted-patch E candidates are stopped.
- Exposure-clean confirmation and second seed: not run because the frozen
  development gate failed. This is a required stop, not missing work.
- Paper E: remains `NARROW_AND_CONTINUE`; the 12-page package and owner action
  packet are ready. No external submission action was performed.
- Thesis: C1-C3 method/results/limitations text and evidence table were updated
  with the real Phase B training and negative results.

## A/C Execution Evidence

| Task | Role | Result |
|---|---|---|
| `phaseb-b1-supervision-a-20261026` plus remediations | A | 72 trajectories; one visible set-binding mechanism, 5 eligible rows / 3 families |
| `phaseb-b1-preaudit-c-20261026`, reaudits | C | C-1 through C-6 and H1/H2 closed; R-1 report count discrepancy explicitly disposed by D |
| `phaseb-paper-thesis-a-20261026` | A-PAPER | Paper E owner packet, first review check and Chinese thesis draft completed |
| `phaseb-b2-same-start-a-20261026` | A | Two real R/E LoRA runs plus 192-token development generation |
| `phaseb-b2b-output-repair-a-20261026` | A | Same checkpoint, no retraining, 72-call 384-token repair generation and corrected paired analysis |
| `phaseb-b2b-combined-audit-c-20261026` | C | Independent 288-row recompute, zero numerical discrepancies; stop accepted with four scope disclosures |

All A/C tasks ran on GB10 worktree
`/home/testuser/wzh/phase_b_worktree_20261026`. The first remediation3 C attempt
is preserved as `AUDIT_NOT_EXECUTABLE_INPUTS_INACCESSIBLE` interface evidence;
the corrected-worktree rerun supplied the scientific judgment.

## Scientific Results

### Supervision

B1 produced 5 eligible set-binding correction rows across 3 source families:
3 `ROW_ROLE_MISBINDING` rows / 2 families and 2
`ROW_AND_PERIOD_ROLE_MISBINDING` rows / 1 family. Unit and direction are not
training targets. Three of five materialized targets are sign-reversed relative
to the frozen audit reference, so the sole estimand is
`SET_BINDING_SET_ACCURACY`, not answer correctness.

### Training

R and E continued from the same frozen ordinary parent and each trained 128
steps on 256 rows. Total processed training text was 319,948 tokens and 287.98
GPU seconds. The R receipt is recovered from the saved multi-adapter artifact
after a post-training layout assertion failed; `training_rerun=false`. E then
trained once. No third training run occurred.

### Development Comparison

Primary metric: row-level `SET_BINDING_SET_ACCURACY`, averaged within source
family and then across 12 families.

| Arm | Correct | Wrong | Reasonable UNKNOWN | Accuracy |
|---|---:|---:|---:|---:|
| Frozen O | 27 | 5 | 4 | 75.0% |
| Neutral retry N | 26 | 6 | 4 | 72.2% |
| Full revision R | 25 | 7 | 4 | 69.4% |
| Restricted patch E | 0 | 32 | 4 | 0.0% |

- E-R: -69.4 percentage points, source-family interval [-91.7, -44.4].
- E-N: -72.2 points, interval [-94.4, -47.2].
- R-N: -2.8 points, interval [-19.4, +13.9].
- E added 5 originally-correct family damages relative to R; ceiling was zero.
- E had 0 legal patches across both generation runs. B2B failures were 20
  patch-key mismatches and 16 patch-schema mismatches, including hallucinated
  hash fields and JSON Schema objects.
- All 72 B2B R/E generations reached the 384-token cap. The 192-token first run
  was therefore retained as interface-truncation evidence, not a method score.
- The reference-derived deterministic patch control reached 88.9%, but it uses
  audit-reference construction and is not deployable.

The C audit confirmed the numerical results and accepted
`INTERFACE_REPRESENTATION_FAILURE_STOP_R_E_CANDIDATE` for this implementation
only. D additionally records:

1. E is interface-UNKNOWN 36/36 but target-availability `CORRECT 0 / UNKNOWN 4 /
   WRONG 32`.
2. The old 24-family semantic gate was substituted by a 12-family
   set-binding gate with zero-damage ceiling.
3. R is also a method-level negative; N comparator configuration is not
   perfectly matched to B2B R/E.
4. The direction gate is structurally unsatisfiable on this panel because 2/3
   eligible families are sign-reversed by construction.

## Judgment Changes

1. The original plan to test whether E beats R is no longer the live question.
   The tested E representation fails at the deployment contract before a
   meaningful method comparison can survive.
2. R is not rescued by the interface repair: it remains below N and O. The
   current full-revision training is also a negative result.
3. The strongest simple baselines are frozen O and neutral retry. More output
   budget repaired parseability partially but did not create a useful E method.
4. The next research point should not be another prompt tweak or patch schema
   variant on this panel. A new point needs a distinct decision residual and
   independently verifiable evidence.

## Paper E

- Canonical scope remains exactly two measurement-audit cases.
- 12-page PDF SHA-256:
  `30aa05af73e05c5e64f324014f982547b46f7166448f256425b5de0ca990b013`.
- Package audit: PASS, citations 24/24.
- Conditional primary route: ICAART 2027 Regular.
- Sequential backup: SN Computer Science subscription route.
- Owner action packet is ready. No submission, payment, signature, public
  artifact release or external contact occurred.

## Thesis Output

- `thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md` now contains the B1
  supervision boundary, real same-start training, first-run truncation, B2B
  repair results, failure taxonomy, strong baselines, limitations and stop rule.
- `thesis_draft/EVIDENCE_TABLE.md` now distinguishes real training, repaired
  development results and interface failure mechanisms.
- The 2027 October review timeline was updated to close the current C2 candidate
  and seek a distinct third research point instead of duplicating C2/C3.

## Resource Accounting

- Generation: 188 physical calls; 180 retained logical calls.
- Generation tokens: lower bound 137,770; conservative upper bound 139,306.
- Training: 2 runs, 319,948 processed-text tokens.
- Collaboration dispatches: 13 of 16.
- Known Codex harness usage: 93,686,809 input, 363,799 output and 111,000
  reasoning-output tokens. Claude usage and subscription fees remain UNKNOWN.
- Paid research API: 0. Judge: 0. Production probes: 0. Production Memory
  writes: 0.
- Confirmation and second-seed scientific budgets remain unused.

## Owner Items

Only the existing Paper E external decisions remain: route, author/affiliation
and contact identity, patent status, AI disclosure, artifact release timing and
license, school recognition, registration/travel funding, formal submission and
payment. The exact October 2027 thesis review date is still unknown.

No new scientific resource request is required for the current stop decision.
