# Loop A Return — Adaptive Mechanism 2026-10-27

Task: `adaptive-mechanism-a-20261027`
Date: 2026-10-27, Asia/Shanghai
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `17f6895e3f2734f5e597f1a1d7853af22ae2adf4`
Authority LF SHA256: `73da0c8a44512c4b47d677efa3a7c71b45fb7d15e582a77737c27c284f800d12`

## Decision

`STOP_BEFORE_GENERATION`.

The visible-only typed reduction baseline reaches `ACCEPT` on 31/36 immutable
first-batch final attempts and contract-valid `REASONABLE_UNKNOWN` on the other
5; it leaves 0 unexplained natural residuals. The 8-UID diagnostic panel is
frozen but was not run. No training, model load, generation, confirmation,
judge, production probe, payment, public release, external contact, or formal
submission occurred.

## 1. Paper E formal build

- Status: `BUILD_BLOCKED`.
- Local search found no installed TeX engine: `pdflatex`, `latex`, `lualatex`,
  `xelatex`, `tectonic`, `latexmk`, `bibtex`, `biber`, `tex`, and
  `luaotfload` were missing.
- Exact attempted command:
  `bash research/adaptive_mechanism_20261027_v1/paper_e_formal_build/build_paper_e.sh`
- Exact observed failure: exit `127`,
  `BUILD_BLOCKED: required TeX tool not found: pdflatex`.
- No fallback PDF is claimed as a formal build; no engine version, TeX log,
  `.bbl`, formal PDF hash, or formal page count exists.
- Directly buildable bundle contains canonical `paper_e_sncs.tex`,
  `references.bib`, three PNG and three SVG figures, `build_paper_e.sh`, and
  the explicit `elsarticle-harv.bst` style dependency.
- Non-TeX source check passed: 24 bibliography entries, 24 cited keys, exact
  citation/bibliography identity, 3 figures, structured abstract, declarations,
  author placeholders, complete body, manual figure references, and no P1/P2
  result insertion.
- Receipt: `paper_e_formal_build/SOURCE_CHECK_RECEIPT.json`.
- First-reviewer check: `paper_e_formal_build/FIRST_REVIEWER_PASS_V2.md`.
  Contribution/nearest-work separation, two-case interpretation,
  clustered/post-hoc identity, claim boundaries and reference readability were
  substantively checked. Owner identity, patent, artifact, funding, fee and
  submission fields remain pending.

## 2. Scoring V2 and first-batch zero-model rescore

Contract layers are reported separately:

1. strict JSON/schema/format;
2. answer content and exact set completeness;
3. numeric equivalence, unit/scale and direction;
4. evidence existence and semantic support;
5. final delivery.

Statuses remain distinct: `ACCEPT`, `REJECT`, `PENDING_ADJUDICATION`,
`STRICT_FAIL`, and `REASONABLE_UNKNOWN`. PENDING is not WRONG, and a correct
number alone is not complete delivery.

### Controls and rescore

- Command:
  `PYTHONPATH=research/adaptive_mechanism_20261027_v1/scoring_v2 python3 -m unittest -v research/adaptive_mechanism_20261027_v1/scoring_v2/test_scoring_v2.py`
- Result: 17 tests, 0 failures, 0 errors, `OK`.
- Rescore command:
  `PYTHONPATH=. python3 research/adaptive_mechanism_20261027_v1/scoring_v2/rescore_first_batch.py --output research/adaptive_mechanism_20261027_v1/scoring_v2/results`
- Input: immutable first 40-call raw batch only.
- Selection: maximum `call_number` for each of 12 UIDs × 3 arms = 36 final
  attempts.
- Model calls in rescore: 0. Generation records created: 0.
- Receipt: `scoring_v2/SCORING_TEST_RECEIPT.json`.

### Per-layer counts

| Layer | top-3 | top-5 | all |
|---|---|---|---|
| Strict | PASS 8 / SF 4 | PASS 8 / SF 4 | PASS 7 / SF 5 |
| Answer | PASS 3 / FAIL 9 | PASS 3 / FAIL 9 | PASS 3 / FAIL 9 |
| Numeric/unit | PASS 5 / FAIL 6 / PENDING 1 | PASS 5 / FAIL 7 | PASS 5 / FAIL 7 |
| Evidence | PASS 1 / FAIL 5 / PENDING 6 | PASS 1 / FAIL 5 / PENDING 6 | PASS 1 / FAIL 7 / PENDING 4 |
| Final delivery | REJECT 7 / SF 4 / PENDING 1 | REJECT 8 / SF 4 | REJECT 7 / SF 5 |

Historical `2/3/3` ACCEPT remains visible beside V2. Corrected final-attempt
input deltas are top-5 − top-3 = `917` and all − top-5 = `1604`.

### Per-UID outcomes

Historical and V2 triples are ordered top-3 / top-5 / all; `R`, `SF`, and `P`
mean `REJECT`, `STRICT_FAIL`, and `PENDING_ADJUDICATION`.

| UID | Historical | Scoring V2 |
|---|---|---|
| `01de2123` | R / R / R | R / R / R |
| `5e67e832` | R / R / R | SF / SF / SF |
| `7a1f65b6` | A / A / A | P / R / R |
| `7e942684` | R / R / R | R / R / SF |
| `8a3fb2be` | R / R / R | R / R / R |
| `9e3493de` | R / R / R | SF / SF / SF |
| `a75bb0b1` | A / A / A | R / R / R |
| `ad42fe3e` | R / R / R | SF / SF / SF |
| `cb4abf04` | R / R / R | R / R / R |
| `e14c60c4` | R / R / R | SF / SF / SF |
| `f37d1be3` | R / R / R | R / R / R |
| `fcb5e3fa` | R / A / A | R / R / R |

Full machine-readable per-layer and per-UID results:
`scoring_v2/results/FIRST_BATCH_RESCORE_V2.json` and
`scoring_v2/results/FIRST_BATCH_ROWS_V2.jsonl`.

## 3. Persistent physical budget

- External ledger:
  `/home/testuser/wzh/research_runs/persistent_budget/adaptive_mechanism_20261027/ledger.jsonl`
- Ledger SHA256:
  `ad0535aeb3fb324c60631ca38b0bbb5a82cb509c834aefb624e025db2350fdef`
- Schema SHA256:
  `ac1090a9974d08350cbd4a699572a95c3440b92a039a22e910bb8619ca89910b`
- Current ledger: 1 `ledger_initialized` event, 0 reservations, 0 raw rows,
  0 physical attempts, 0 input/output tokens, 0 model loads.
- Separate CLI modes: `generate`, `resume`, `rescore`.
- Physical attempt IDs are separate from logical call IDs.
- Reservation precedes loader invocation; raw response and actual usage are
  appended and fsynced before scoring; uncertain reservations stay consumed.
- Attempt 37 and any conservative projection beyond 240,000 input+output
  tokens are rejected before model loading.
- `rescore` loads no model and writes no generation records.
- Shared normalization/calculator:
  `persistent_budget/shared_tools.py`.
- Receipt: `persistent_budget/BUDGET_RECEIPT.json`.

Exact fault command:

```text
PYTHONPATH=. python3 -m unittest -v research/adaptive_mechanism_20261027_v1/persistent_budget/test_persistent_budget.py
```

Result: 7 tests, 0 failures, 0 errors, `OK`.

| Fault | Observed invariant |
|---|---|
| Scoring throws after raw | raw preserved; restart/rescore adds 0 calls |
| Crash after reservation before raw | uncertain reservation remains consumed |
| Crash between calls | every earlier raw row remains present |
| Output directory changes | cumulative ledger is not reset |
| Attempt 37 | rejected before loader; loader count stays 36 |
| Token-cap successor | rejected before loader; loader count stays 1 |
| Shared calculator | safe arithmetic passes; import payload raises |

## 4. Error cards and mechanism decision

- Exactly 12 evidence-grounded cards: nine old shared REJECT UIDs and three
  non-shared controls.
- Cards use the real question, immutable final-attempt raw and visible
  context; labels are derived from scoring observations, not model self-labels.
- Files:
  `diagnostics/results/ERROR_CARDS.json` and `ERROR_CARDS.md`.
- Visible baseline command:
  `PYTHONPATH=. python3 research/adaptive_mechanism_20261027_v1/diagnostics/visible_typed_baseline.py`
- Baseline actor receives only question, answer type, selected visible
  paragraphs and visible table. Gold, expected refs, hidden units, expected
  programs and UID branches are forbidden and used only after output for
  scoring.
- Baseline controls: 5 tests, all `OK`.
- Baseline result: 36 attempts = `ACCEPT 31 / REASONABLE_UNKNOWN 5`;
  `REJECT 0`, `STRICT_FAIL 0`, unexplained natural residual `0`.
- Prioritized signals are resolved or bounded:
  - mean operands without mean reduction: baseline `ACCEPT` in all 3 arms;
  - correct quarter set without count: baseline `ACCEPT` in all 3 arms;
  - seven services without count: `ACCEPT` for all context and
    `REASONABLE_UNKNOWN` where the required paragraph is absent.
- Diagnostic summary:
  `diagnostics/results/DIAGNOSTIC_SUMMARY.json`.
- Frozen 8-UID panel:
  `diagnostic_panel/DIAGNOSTIC_PANEL_PREREGISTRATION.json`.
- Frozen prompts:
  `diagnostic_panel/prompts.json`.
- Model identity is frozen as local Qwen3-4B revision
  `1cfa9a7208912126459214e8b04321603b3df60c`, file-manifest SHA256
  `0f967e91a45dfb1ff799e1c131cd744ad80f627ced9d55e73f3a598bc25cdf2c`;
  it was not loaded.

## 5. Exact accounting

### Immutable historical first batch

- Calls: 40 = 36 primary final attempts + 4 bounded retries.
- Input tokens: 33,207.
- Output tokens: 2,609.
- Cached tokens: unavailable/null in all 36 selected final attempts.
- Wall time: 268.9788107126951 seconds.
- By arm:
  - top-3: 13 calls, 9,342 input, 842 output, 86.55732808634639 seconds;
  - top-5: 13 calls, 10,259 input, 842 output, 86.93324388191104 seconds;
  - all: 14 calls, 13,606 input, 925 output, 95.4882387444377 seconds.
- Selected 36 final attempts: 30,027 input, 2,342 output,
  247.12595063261688 seconds, 4 selected retries.

### This A task

- New model calls: 0.
- New input tokens: 0.
- New output tokens: 0.
- New retries: 0.
- New generation wall time: 0 seconds.
- New generation records: 0.
- Training runs: 0.
- Judge calls: 0.
- Production probes: 0.
- New raw model outputs: 0; immutable historical raw remains at
  `research/publication_proxy_calibration_20261026_v1/raw/runs/compliant_primary/P2_GENERATIONS.raw.jsonl`.

## 6. Thesis additions

Substantive Chinese results, methods and limitations were added only to:

- `research/feedback_learning_phase_b_20261026_v1/thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md`
- `research/feedback_learning_phase_b_20261026_v1/thesis_draft/EVIDENCE_TABLE.md`

They record Paper E `BUILD_BLOCKED`, the five-layer rescore and historical
2/3/3 comparison, corrected deltas, mean/count information-loss signal,
baseline stop decision, persistent-ledger/fault evidence, AI/automatic review
identity and claim boundaries. No C acceptance is claimed.

## 7. Verification

Fresh local verification on 2026-10-27:

```text
python3 research/adaptive_mechanism_20261027_v1/paper_e_formal_build/check_sources.py --json research/adaptive_mechanism_20261027_v1/paper_e_formal_build/SOURCE_CHECK_RECEIPT.json
bash research/adaptive_mechanism_20261027_v1/paper_e_formal_build/build_paper_e.sh   # expected exit 127 / BUILD_BLOCKED
PYTHONPATH=research/adaptive_mechanism_20261027_v1/scoring_v2 python3 -m unittest -v research/adaptive_mechanism_20261027_v1/scoring_v2/test_scoring_v2.py
PYTHONPATH=. python3 research/adaptive_mechanism_20261027_v1/scoring_v2/rescore_first_batch.py --output research/adaptive_mechanism_20261027_v1/scoring_v2/results
PYTHONPATH=. python3 -m unittest -v research/adaptive_mechanism_20261027_v1/diagnostics/test_visible_typed_baseline.py
PYTHONPATH=. python3 research/adaptive_mechanism_20261027_v1/diagnostics/visible_typed_baseline.py
PYTHONPATH=. python3 research/adaptive_mechanism_20261027_v1/diagnostics/build_error_cards.py
PYTHONPATH=. python3 research/adaptive_mechanism_20261027_v1/diagnostics/summarize_diagnostics.py
PYTHONPATH=. python3 -m unittest -v research/adaptive_mechanism_20261027_v1/persistent_budget/test_persistent_budget.py
PYTHONPATH=. python3 -m compileall -q research/adaptive_mechanism_20261027_v1
python3 scripts/docs_lint.py --json /tmp/adaptive_docs_lint_report.json
```

Results: source check PASS; expected build blocked at 127; scoring 17/17;
baseline 5/5; persistent budget 7/7; compile PASS; all owned JSON parses;
docs lint PASS with 0 fail / 0 warn. Full repository test suite was not run.

## 8. Harness usage and skill loading

A-harness usage is reported separately and was not exposed by the harness:

| Field | Value |
|---|---|
| Input tokens | `null` — not exposed |
| Cached tokens | `null` — not exposed |
| Output tokens | `null` — not exposed |
| Reasoning tokens | `null` — not exposed |

No numbers are inferred or fabricated. Skill loading execution status:

- `graph-loop-rules`: loaded and applied; SHA256
  `492fef50e386d9526385676968b649880eb0e409a70e8b345658342abd157a3e`.
- `paper-review-check`: loaded and applied; SHA256
  `2439cfaf06af5c5d8ddd9f4637fb126261e215a3c48c249e03ee3a4189862a83`.
- `verify-before-done`: loaded and applied for the final completion gate;
  SHA256 `3f62872c3e6f7bf3341a52f5dd577bc3fef4f517b8a4498b040da13617d5ddfa`.
- Total task skills loaded: 3 of the 5-skill maximum.

## 9. Claim boundaries

- No C acceptance before an independent fixed-snapshot C task exists.
- No panel method gain, confirmation, new-source validation, production
  result, formal TeX build, school recognition, or submission claim.
- All diagnostics are AI/automatic development review, not human gold.
- The historical raw, scores, manifests and reports were preserved.
