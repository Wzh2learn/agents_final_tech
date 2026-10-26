# A Remediation Return

Task: `publication-proxy-calibration-remediate-a-20261026`

Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`

Authority Git blob:
`a38252322189ccb00a1a45b7611f693ada292faf`

Authority SHA256:
`9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974`

## Disposition

The prior A result and C audit remain historical evidence. Paper E is now a
complete two-case journal-derived manuscript, not an excerpt or cover sheet.
P1 preserves the accepted actor/regression while correcting three distinct
result identities. P2 has completed one bounded 12-item development-panel
calibration after `END_TO_END_PREFLIGHT_PASS`; it has not established
generalization or noninferiority.

## Paper E

- Canonical LaTeX:
  `paper_e_sncs/paper_e_sncs.tex`, SHA256
  `f1993042d344d97e7a47fe6cda1065ca3bfc42d7720565c492c8c6dfef173734`.
- Bibliography: `references.bib`, 24 entries; citation census is 24 cited,
  24 present, zero orphan and zero missing.
- Structured abstract: 195 words and consistent in the canonical manuscript
  and support file.
- PDF: 15 pages, 6,879 extracted whitespace-delimited tokens, 51,326 text
  bytes; SHA256
  `f042958061bc1118e76f58b6a3504f5125f4161b82ebca28decc7548f3bf048c`.
- PDF identity: deterministic PyMuPDF Story full-content fallback, not a
  TeX-engine compilation. Two consecutive builds produced the same PDF hash.
- The complete Introduction, Related Work, Method/Measurement Contract,
  Experimental Setup, Results, Discussion/Limitations, Data Availability and
  Declarations are present. The first-reviewer analysis remains outside the
  submission body.
- The checkpoint-level qualifier for `96/118`, post-hoc/clustered FinRank
  identity and unresolved reproduction gaps remain explicit.
- Author, affiliation, corresponding, funding, patent, artifact and
  submission fields remain `TBD_OWNER`. Paper E is not claimed to be accepted,
  published or school-recognized.
- D can compile the canonical source with:
  `pdflatex paper_e_sncs.tex && bibtex paper_e_sncs && pdflatex paper_e_sncs.tex && pdflatex paper_e_sncs.tex`.

## P1 Identity

The accepted public actor and `full_24_regression.json` were not rerun or
rewritten. Their corrected identities are:

- numeric program correctness: 23/24;
- complete semantic answer correctness: 13/24;
- observable unit agreement: 14/24;
- rule-conformant unit `UNKNOWN`: 10/24, not numeric failures.

The row-level direction conflict remains `UNRESOLVED`: later-minus-earlier is
`2019 - 2018 = -1955`, while the frozen reference uses the other acceptable
reading, `2018 - 2019 = 1955`. The focused `unittest` harness executed four
tests and passed; the three-module combined suite executed 16 tests and passed.

## P2 Calibration

The actor saw only the question and selected visible table/paragraph context.
The frozen 12 UIDs, seed, exclusions, replacements, prompt, model files,
decoder and calculator preceded output. The zero-output dry run covered
12 items × 3 arms, and formal preflight reached
`END_TO_END_PREFLIGHT_PASS`.

| Arm | ACCEPT | PENDING | REJECT | UNKNOWN | Error delivery | Input tokens | Output tokens | Mean visible chars | Generation wall s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| table + top-3 | 2 | 0 | 10 | 1 | 0.833 | 8,863 | 778 | 1,710 | 46.91 |
| table + top-5 | 3 | 0 | 9 | 1 | 0.750 | 9,780 | 778 | 2,040 | 46.45 |
| table + all | 3 | 0 | 9 | 2 | 0.750 | 11,384 | 786 | 2,630 | 47.69 |

Only one paired item changed: top-3 was `REJECT`, while top-5 and all were
`ACCEPT`. Thus the measured result is one additional ACCEPT with larger
context and input cost on this exposed 12-item panel. It is not a 2-point
noninferiority result, a generalization result, or an upper/lower bound.

The ledger contains 36 primary calls and four bounded retries, for 40 calls,
2,609 output tokens, 33,207 measured input tokens and 157.01 seconds summed
generation wall time. Training is 0/0. Cached tokens, Claude/A harness
input/cache/output/reasoning usage, subscription fees and cash cost are
`UNKNOWN`. Old 507-item heuristic counts remain separate.

The first 40-call attempt stopped after generation because the strict parser
accepted `TABLE:C1` but the semantic normalizer incorrectly required
`TABLE:<row>:<column>`. Its traceback and raw partial ledger are preserved.
The repair normalized the accepted column-only form; no new generation call
was made while completing scoring. This is an interface/reproducibility
qualification, not evidence about proxy information value.

## Scientific Accounting

- Proxy/reference defect: old heuristic counts and lexical matching remain
  non-complete semantic oracles; tri-state scoring retains
  `PENDING_ADJUDICATION`, although final panel results contain none.
- Retrieval/context omission: top-3 has one fewer ACCEPT than top-5/all on the
  paired panel, but this is too small for a general context conclusion.
- Actor reading/reasoning error: rejected final answers and strict-parser
  failures are retained separately in the raw ledger.
- Parser/interface failure: four bounded retries were used after preserved
  strict failures; every attempt remains counted.
- Semantic pending adjudication: zero final adjudications on this panel, with
  the mechanism still available for wrong-role/substring ambiguity.
- Actual cost/risk tradeoff: top-5/all each have ACCEPT 3 and risk 0.750;
  all uses 1,604 more input tokens than top-5 and 2,521 more than top-3.

## Receipts And Accounting

- `raw/runs/primary/P2_GENERATIONS.jsonl` — all 40 raw attempts, parse and
  semantic outcomes, risk flags, tokens, latency and retry identity.
- `raw/runs/primary/P2_CALIBRATION_RESULTS.json` — arm summaries, paired
  item differences and complete cost ledger.
- `raw/runs/primary/P2_EXECUTION_IDENTITY_RECEIPT.md` — component and artifact
  hashes; explicitly records the post-hoc runner-source reconstruction.
- `raw/runs/primary/P2_REMEDIATION_PREFLIGHT_BEFORE_GENERATION.json` — exact
  pre-generation passing receipt and its 15-test qualification output.
- `raw/runs/failed_attempt_20261026/FAILED_SCORING_ATTEMPT.md` — preserved
  failure and zero scientific meaning.
- `receipts/COMMANDS_AND_STATUS.md` — exact command/status record.
- `receipts/ZERO_TRAINING_EVIDENCE.md` — historical negative evidence plus
  current 40-call training-zero accounting.
- `paper_e_sncs/BUILD_RECEIPT.md` — engine, fallback identity, page/text
  counts and hashes.
- `receipts/P1_IDENTITY_REMEDIATION.md` and `receipts/P1_TEST_RECEIPT.md` —
  corrected identities and real test counts.

`ALL_FILES.sha256` was regenerated after all owned outputs were finalized and
verified before staging: 74/74 task entries passed. The paper-local manifest
also verified 26/26 entries. The historical `A_RETURN.md`, old formal
preflight/stop receipts and prior failed attempts are not rewritten into
current evidence.
