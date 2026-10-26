# A Return: Publication and Proxy Calibration

Task: `publication-proxy-calibration-a-20261026`  
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`  
Authority Git blob: `a38252322189ccb00a1a45b7611f693ada292faf`  
Authority SHA256: `9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974`

## Scientific disposition

**P1: the public deterministic actor is promising but not a generalization result.** On the frozen 24 ordinary originals it reaches 23/24 numeric-correct versus the frozen model scorer at 19/24, with four genuine repairs, zero damage to the 19 previously numeric-correct items, and one preserved direction-reference conflict. Ten outputs correctly retain `UNKNOWN` for units not legally observable in the visible table text.

**P2: no information value yet; stop this generation candidate.** The future matcher is repaired in the owned path, a 12-UID development panel and question→table/paragraph→role/unit→program/answer chain are frozen before output, but the formal preflight fails the runner→adapter→scorer dry run because this task namespace has no executable three-arm P2 runner/adapter contract. Generation stopped before any model call. There is therefore no answer/cost comparison and no basis for claiming full context is more accurate, cheaper, or harmful to restricted context.

**Next experiment that would change the decision:** add a hash-bound P2 runner, visible-context adapter and scorer-input builder; run a zero-output dry run on all 12 UIDs; then, only after `END_TO_END_PREFLIGHT_PASS`, compare exactly table+top3, table+top5 and table+all with one frozen actor/decoder/calculator, recording every call, retry, token category and wall time.

## Owned outputs

- `paper_e_sncs/` — editable LaTeX/BibTeX, deterministic package PDF, copied figure sources, structured abstract, AI disclosure, cover letter, declarations, artifact statement, owner decision sheet, first-reviewer pass, manifest and original ICAART source/reference preserved unchanged.
- `p1_rule_execution/` — deterministic public actor, runner, focused tests, full 24-row JSON and Markdown report.
- `p2_proxy_calibration/` — R7/R8 future matcher, regression fixtures, deterministic selection/reference chain, formal preflight and generation-stop receipts.
- `receipts/` — P1 test receipt and zero-training evidence.
- Thesis updates in `research/feedback_learning_phase_b_20261026_v1/thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md` and `EVIDENCE_TABLE.md`.

All owned-file hashes are in `ALL_FILES.sha256`. Key hashes:

- P1 actor: `ea53a574ebe469ae97de3b0261e908b663cc4fc51a09db17095a28057c308ae3`
- P1 regression JSON: `d03da88bcf39e7d9d3e16d1618950784de32a3b1eaa8eb89eb3523a9ff19f6e4`
- P2 future matcher: `d5512f2966178428775bbdb0d04305c9ed78f43b7954f826c747b1b64e700ef4`
- P2 selection receipt: `484f5aa75f4a7d4d5d9c4f3fdfe4b36bb84720b45b93ddfd4c09224d726173a9`
- P2 preflight receipt: `bc1c02550a60f0dc359d4df29459279b3ed970a92d880a5ab73a993ce1fb8fd5`
- SNCS TeX: `aa4531afd8c6bebb115e9f4e541f957a2a73445f9ca4ac552b8d9ee9dacef898`
- SNCS package PDF: `9d9850f7fa3c0605b571fe2adf0cee9c6ac64fab6511e3b0a27ab5d84a2b80fc`

## Commands and exit status

1. `python3 -m py_compile .../public_actor.py .../run_full_regression.py .../test_public_actor.py` — exit 0.
2. `python3 .../run_full_regression.py --instances ... --results ... --output ...` — exit 0; emitted 24-row report.
3. `PYTHONPATH=src:... python3 -m pytest ...` — exit 1 because pytest is unavailable in the local Python 3.12 environment; no test weakening or fallback was used.
4. `python3 .../select_and_reference.py ...` — exit 0; selected 12 UIDs before output.
5. `python3 -m py_compile .../FUTURE_EVALUATION_MATCHER.py .../test_matcher_regressions.py` — exit 0.
6. Future matcher smoke tests for `1,496`, `1, 496`, `-5`, `(5)`, and `5` — exit 0; expected outcomes passed.
7. `/tmp/tectonic/tectonic paper_e_sncs.tex` — exit 126 (`Exec format error`; x86-64 binary on aarch64 host).
8. `python3 compile_package_pdf.py` — exit 0; deterministic reportlab package PDF produced. The TeX remains canonical for owner Overleaf compilation.
9. `runner-to-adapter-to-scorer dry run` — exit 1 by design; recorded as the formal qualification failure chain.

## Zero-training and token accounting

No model calls were made. P2 generation calls/tokens and training calls are zero. A usage is `NOT_APPLICABLE_NO_CALL`; no padding or unmeasured token category is presented as measured.
