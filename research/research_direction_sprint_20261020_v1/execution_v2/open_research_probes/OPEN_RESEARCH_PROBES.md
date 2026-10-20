# Open Research Probes C2+C3

Status: `DEV_ONLY_COMPLETED`
Date: 2026-10-20, Asia/Shanghai

## Scope

Two deterministic mechanism probes were implemented and run on the 13
`KEEP_DEVELOPMENT` tasks. The inputs, lookup budgets (1/2/3), random seeds,
score rules and feedback thresholds were frozen before outcomes were computed.
No model, judge, training, service or network call was made.

This is a controlled finite-panel simulation, not a natural experiment, model
effect, validated learning method or independent-generalization result.

## C2: Active Evidence Acquisition

`direct`, `fixed`, `random`, `lexical`, `score_disagreement` and reference-only
`oracle` were compared. Useful-fact coverage uses only adjudication anchors
belonging to a minimal sufficient set. Contrast/distractor anchors are retained
in the fixture but do not count as useful facts. ESD_010 accepts `cand_003` as a
sufficient subset; optional `cand_007` is not required.

Task-macro results:

| Budget | Strategy | Sufficient-set discovery | Useful-fact coverage | Lookups |
|---:|---|---:|---:|---:|
| 1 | lexical | 46.2% | 46.2% | 1.0 |
| 1 | score-disagreement | 23.1% | 23.1% | 1.0 |
| 1 | oracle | 76.9% | 88.5% | 1.0 |
| 2 | lexical | 61.5% | 73.1% | 2.0 |
| 2 | score-disagreement | 38.5% | 42.3% | 2.0 |
| 2 | oracle | 100.0% | 100.0% | 2.0 |
| 3 | lexical | 76.9% | 84.6% | 3.0 |
| 3 | score-disagreement | 53.8% | 61.5% | 3.0 |
| 3 | oracle | 100.0% | 100.0% | 3.0 |

The lexical policy is the best realizable policy at every budget. The
score-disagreement policy is below lexical everywhere and below fixed order at
budget 3 (53.8% versus 61.5% discovery). Therefore the tested
lexical-versus-scope disagreement heuristic is **stopped as an acquisition
candidate**. Active acquisition itself remains open, but a future policy must
beat the frozen lexical baseline at equal lookup cost; generic score
disagreement is not evidence of useful uncertainty.

The oracle gap shows remaining acquisition headroom in this panel, but it is a
reference-informed upper bound. It does not show that an agent can realize the
gain.

## C3: Feedback Contract

Seven frozen selections were scored under `exact_match`,
`minimal_sufficient_set` and `fact_coverage`, then processed by one explicit
retain/revise/reject rule.

| Contract | False-negative rejections | Unsupported acceptances | Main effect |
|---|---:|---:|---|
| exact-match | 1/1 valid alternative | 0/2 unsupported extras | Rejects ESD_010's valid redundant sufficient set and unnecessarily revises it |
| minimal sufficient set | 0 | 2/2 unsupported extras | Retains selections that contain a sufficient subset but add out-of-scope evidence |
| fact coverage | 0 | 2/2 unsupported extras | Same precision failure when all useful facts are covered |

The two failures are complementary. Exact-match is too narrow when multiple
sufficient representations are legal. Set containment and fact coverage are
too permissive unless they also enforce scope precision. A defensible feedback
contract therefore needs **set-valued sufficiency plus scope precision**; neither
primitive is sufficient alone.

This result moves feedback-contract semantics above the tested disagreement
acquisition heuristic in the research ordering. It justifies a later mechanism
study of alternate sufficient sets, unsupported additions and experience
retention. It does not yet establish downstream learning benefit.

## Direction Decision

- Continue: set-valued feedback with explicit scope precision, evaluated later
  on naturally occurring alternate evidence sets.
- Deprioritize: active acquisition until a policy can beat lexical at equal cost.
- Stop: exact-match-only feedback; unqualified sufficient-set-only or
  fact-coverage-only retention; the tested score-disagreement policy.
- Controls to retain: fixed order and random acquisition, plus oracle only as a
  labeled upper bound.

## Reproducibility

- Inputs and protocol: `fixtures/probe_inputs_frozen.json`,
  `fixtures/feedback_cases_frozen.json`, `fixtures/FREEZE_RECEIPT.json`
- Machine-readable results:
  `results/active_evidence_probe_results.json`,
  `results/feedback_contract_probe_results.json`
- Scripts: `active_evidence_probe.py`, `feedback_contract_probe.py`,
  `probe_common.py`
- Regression tests: `test_probes.py` (`python -m unittest -v test_probes.py`)

All four regression tests pass. The freeze receipt records upstream and fixture
SHA-256 hashes. The scripts use only the Python standard library.
