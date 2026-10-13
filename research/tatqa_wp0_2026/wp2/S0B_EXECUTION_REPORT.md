# TAT-QA WP-2 S0b Fix Execution Report

> task: `tatqa-wp2-s0b-20261013` | date: 2026-10-13 | loop: A | status: `PASS`
> boundary: closes Loop C round-1 F-2/F-3/F-4/F-8 only; F-5 remains owner/advisor-owned; no S4+ action.
> execution cost: zero model calls, zero endpoint calls, zero judge calls, zero training, zero external network.

## 1. Finding status

| Finding | Status | Closure evidence |
|---|---|---|
| F-2 | `CLOSED` | Direct and equivalent forms now share `wrong_unit` attribution for target-unit label errors. Existing equivalent-form cases remain PASS; no not-correct result can become correct. |
| F-3 | `CLOSED` | New dedicated direct-form fixture passed: before `actual=wrong`; after `actual=wrong_unit`. Periods, source delta, target delta, and scale conversion were correct; only the unit label was wrong. |
| F-4 | `CLOSED` | Every `preservation_check` boolean is now emitted through `_safety_claim` as `{basis, evidence, value}`. Preservation facts did not change. |
| F-8 | `CLOSED` | Protocol §5 now declares `wrong` and all eight implementation classes; the runner performs exact set-alignment verification. |

F-5 was not changed or inferred: `normalize_unit`, `UNIT_ALIASES`, source-unit null/currency behavior, candidate items, and target-unit rules remain untouched and pending owner/advisor decision.

## 2. Failing-before and passing-after evidence

Before the checker change, the dedicated fixture produced:

```text
direct_form_same_scale_wrong_unit: expected=wrong_unit actual=wrong pass=False
```

After the minimal checker change, the same fixture produced:

```text
direct_form_same_scale_wrong_unit: expected=wrong_unit actual=wrong_unit pass=True
```

This is a `not_correct -> not_correct` attribution correction only. It does not relax the correctness threshold.

## 3. Full rerun

Command:

```text
PYTHONPATH=src python3 research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py
```

Output:

```text
S0_FIXTURES_PASS obligations=7 unit_gate_cases=3 direct_form_cases=1 numeric_rendering_cases=5
receipt=research/tatqa_wp0_2026/wp1/S0B_FIX_RECEIPT.json
```

Additional verification:

```text
python3 -m py_compile research/tatqa_wp0_2026/wp1/checker_v2.py research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py
PY_COMPILE_PASS

python3 scripts/docs_lint.py --json /tmp/tatqa_s0b_docs_lint_20261013.json
docs_lint: PASS (0 fail / 14 warn)
```

The 14 documentation warnings are the pre-existing tracked debt; neither modified nor new S0b document generated a docs-lint warning.

## 4. Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `research/tatqa_wp0_2026/wp1/checker_v2.py` | `b3c7b36363386ab6a9d0be21775bd174d7a19db0e6b534347b0a2269d1194ca3` |
| `research/tatqa_wp0_2026/wp1/fixtures/s0b_direct_form_fixtures_v2.json` | `aecae15fcb3bd00523c458e41471b6815b70b4f158e37c6af8528046b601c95a` |
| `research/tatqa_wp0_2026/wp1/s0_run_fixtures_v2.py` | `eb05a7d9c0fa37466972c67602551599766859c62ef4c7432051a480760fb6dd` |
| `research/tatqa_wp0_2026/wp1/S0B_FIX_RECEIPT.json` | `b759a5e74b1d58c2500380f2301f5988c67bdb284e5453cdacab524236eb2c17` |
| `docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md` | `9d52a3395ad7e59b7c0b99eea9fda3981fc4e4a0e093d3fabf206e2a76c64203` |
| `docs/research/WP1_PREFREEZE_FIX_NOTE_S0B_ADDENDUM_v1.md` | `f44023bc3df603f254651cbe318e0e2c638e23240e336c3d5bad853dbb1c7e9e` |
| `research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json` | `1085cde79b3085eaa6963799c6c4018937c070149dbc5e619bb4cf0d39561c50` (unchanged) |
| `docs/research/WP1_PREFREEZE_FIX_NOTE_v1.md` | `998b82190ea618912ddab61a15684e4a53ccc6421c2be3960d3fc025b70c5fe5` (unchanged) |

Before/after pins for the directly changed implementation/document artifacts are in `S0B_FIX_RECEIPT.json`; the original S0 receipt is referenced and hash-guarded rather than overwritten.

## 5. Deliverables and preservation choice

The S0b explanation is a separate document, `WP1_PREFREEZE_FIX_NOTE_S0B_ADDENDUM_v1.md`, because the existing WP-1 fix note and S0 receipt are historical artifacts. A separate addendum preserves both byte-for-byte and provides a clean Loop C closure trail. The new S0b receipt references `S0_FIX_RECEIPT.json` and refuses to run if that historical receipt's pinned hash changes.

Historical WP-1 code, receipts, run logs, `S0_FIX_RECEIPT.json`, and `WP1_PREFREEZE_FIX_NOTE_v1.md` were not modified. `logs/` was not touched.

## 6. Left open

1. F-5 owner/advisor decision remains mandatory before item freeze.
2. Candidate v2 remains `DRAFT_NOT_FROZEN`; its later isolation receipt and all S4+ gates remain pending.
3. No actor revision, feedback-right approval, MODEL_GO, budget window, experience construction, pilot, training, model call, judge call, or scientific ruling occurred.

## 7. Workspace and skill-load discipline

No `git add`, `git commit`, `git push`, or other Git operation was performed. No production service, model endpoint, database, credential file, or external network was touched.

Loaded skills: `graph-loop-rules` (red lines; explicit “do not touch logs” overrides its generic log-append rule), `testing-practices` (fail-before/pass-after fixture discipline), `structured-output` (machine-checkable JSON receipt), and `verify-before-done` (fresh completion gate). All four were used; no unused skill was loaded.
