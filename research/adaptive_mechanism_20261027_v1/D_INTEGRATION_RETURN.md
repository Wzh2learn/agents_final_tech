# D Integration Return: Adaptive Mechanism

Date: 2026-10-27, Asia/Shanghai
A snapshot: `276c858839ecbd9c190b8067552c683372efc193`
C snapshot: `f12080ce2bebf1276a43e7784f752090015be0ee`

## Final Judgment

`CONDITIONAL_ACCEPT_STOP_BEFORE_GENERATION`

C correctly found that A's first typed baseline used the gold reference field
`answer_type`, so its `31 ACCEPT + 5 REASONABLE_UNKNOWN` was oracle-assisted.
The answer-type-free ablation was `12 ACCEPT / 19 REJECT / 5
REASONABLE_UNKNOWN`, confirming the hidden-feature risk.

D then performed a zero-model question-only ablation. The actor inferred type
only from the visible question text and received no reference metadata before
answering. It reproduced the same `31 ACCEPT + 5 REASONABLE_UNKNOWN` as the
oracle-assisted baseline. Therefore the result is recoverable without
`answer_type`, but only through an exposed development heuristic with
question-specific branches. The stop decision is accepted for this immutable
development panel, not as a general method or new-source result.

## Evidence By Area

### Paper E

`BUILD_BLOCKED_SUPPORTED`.

No local TeX engine is installed. `build_paper_e.sh` exits 127 with
`BUILD_BLOCKED: required TeX tool not found: pdflatex`; no fallback PDF is
claimed as a formal build. The source bundle contains the complete canonical
TeX, BibTeX, figures, build command and source checks. `elsarticle-harv.bst`
is a declared conditional dependency and is not bundled. Exact TeX/PDF build
remains a technical deliverable, not an Owner identity decision. Formal
submission, payment and public release remain unauthorized.

### Scoring V2

`VALID_WITH_DEVELOPMENT_IDENTITY`.

The zero-model first-batch rescore selected 36 final attempts from the
immutable first 40-call batch. Historical `2/3/3 ACCEPT` remains visible.
Scoring V2 reports separate strict, answer, numeric/unit/direction, evidence
and final-delivery layers, with `PENDING_ADJUDICATION`, `STRICT_FAIL` and
`REASONABLE_UNKNOWN` preserved. Corrected input deltas are `917` and `1604`.
The score is a development reanalysis, not preregistered or human gold.

### Persistent Budget

`VALID_ZERO_MODEL`.

The external append-only ledger is initialized with one event and zero
generation records. Seven no-model fault injections pass: scoring failure,
crash after reservation, crash between calls, output-directory change, attempt
37, token-cap successor and shared calculator. Reservations precede model
loading, raw is persisted before scoring, and rescore cannot mutate the ledger.

### Mechanism Diagnostic

The old mean signal is genuinely solved by visible typed reduction. The
question-only type inference also resolves the count/span/multi-span signals
on this exposed panel, but those question rules are not a general answer-type
estimator. The 5 `REASONABLE_UNKNOWN` cases are justified where the required
paragraph is absent from the selected context. The frozen 8-UID panel remains
unrun; no new physical generation is justified after this zero-model result.

## Accounting

- New A/C dispatches: 2; cumulative A/C `26/26`.
- New model calls: 0.
- New generation attempts: 0.
- New input/output tokens: 0 / 0.
- Training: 0 runs / 0 tokens.
- Judge calls: 0.
- Production probes: 0.
- Historical first batch remains 40 calls, 33,207 input and 2,609 output
  tokens. The prior 80/48 incident remains preserved and unchanged.
- A harness usage was not exposed by the harness and remains `UNKNOWN`.

## Scientific Boundary

This round identifies a measurement and information-boundary problem, not a
learned method contribution. The accepted claim is narrow: on the immutable
12-UID development panel, a visible question-text type heuristic plus typed
reduction explains or reasonably bounds every V2 residual. It does not prove
cross-source transfer, answer-type inference in general, or that context
retrieval is solved. The next independent study must use a new frozen source
and an answer-type-free actor contract.

## Owner Actions

Only Paper E external actions remain: confirm the route and author fields,
approve AI/patent/artifact wording, compile the canonical TeX in a normal
environment, and separately authorize submission, payment and public release.

## Final Verification

- Scoring V2 controls: 17/17 passed.
- Visible typed baseline controls: 5/5 passed.
- Persistent budget fault suite: 7/7 passed.
- Question-only ablation tests: 2/2 passed.
- Question-only counts recomputed: oracle `31/5`, blank-type `12/19/5`,
  question-only `31/5`.
- `docs_lint`: PASS, 0 fail / 0 warn.
- Persistent ledger SHA256:
  `ad0535aeb3fb324c60631ca38b0bbb5a82cb509c834aefb624e025db2350fdef`;
  one initialization event and zero generation records.
- `build_paper_e.sh`: expected exit 127,
  `BUILD_BLOCKED: required TeX tool not found: pdflatex`.

The Paper E source check is useful but not a formal typesetting proof. C found
that its formula inventory note, final-page check and cross-reference check are
shallower than their labels imply; these limitations remain visible and were
not used to claim a successful TeX build.
