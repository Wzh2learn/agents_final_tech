# Remediation Commands and Status

All commands ran from the repository root on 2026-10-26 Asia/Shanghai.

| Command or operation | Exit/status | Evidence |
|---|---:|---|
| Authority blob and SHA256 checks | 0 | Git blob `a38252322189ccb00a1a45b7611f693ada292faf`; SHA256 `9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974` |
| `PYTHONPATH=src python3 -m research.publication_proxy_calibration_20261026_v1.raw.runner --mode dry-run` | 0 | `P2_ZERO_OUTPUT_DRY_RUN.json`; 36 arm rows, zero model calls |
| `PYTHONPATH=src python3 -m research.publication_proxy_calibration_20261026_v1.raw.runner --mode preflight` | 0 | `END_TO_END_PREFLIGHT_PASS` |
| Initial Qwen3-4B calibration process | 1 | Stopped after 40 calls during post-generation `TABLE:C1` normalization; preserved traceback and raw partial under `raw/runs/failed_attempt_20261026/` |
| Matcher normalization repair and focused unit tests | 0 | `Ran 12 tests`, `OK`; no model calls |
| Rescored existing 40-attempt ledger with `--mode calibrate` | 0 | `COMPLETE_12_ITEM_DEVELOPMENT_PANEL`; no additional generation calls |
| `python3 -m py_compile` for all owned Python sources | 0 | P1, matcher, raw chain, executed runner archive and PDF fallback converter compiled |
| `PYTHONPATH=src python3 -m unittest research.publication_proxy_calibration_20261026_v1.p1_rule_execution.test_public_actor` | 0 | `Ran 4 tests`, `OK` |
| `PYTHONPATH=src python3 -m unittest research.publication_proxy_calibration_20261026_v1.p1_rule_execution.test_public_actor research.publication_proxy_calibration_20261026_v1.p2_proxy_calibration.test_matcher_regressions research.publication_proxy_calibration_20261026_v1.raw.test_raw_chain` | 0 | `Ran 16 tests`, `OK` |
| `python3 paper_e_sncs/compile_package_pdf.py` | 0 | 15-page full-content fallback PDF; not a TeX-engine build |
| `pdfinfo`, `pdftotext`, citation census and figure-use checks | 0 | 15 pages, 6,879 extracted tokens, 24/24 cited entries, three figures with measurement-chain and visibility use counts of one |
| `git diff --check` | 0 | No whitespace errors |
| `python3 scripts/docs_lint.py --json /tmp/a_remediation_docs_lint.json` | 0 | `PASS (0 fail / 0 warn)` |
| Two consecutive Paper E fallback builds | 0 | Both PDF SHA256 values matched `f042958061bc1118e76f58b6a3504f5125f4161b82ebca28decc7548f3bf048c` |
| `(cd research/publication_proxy_calibration_20261026_v1/paper_e_sncs && sha256sum -c MANIFEST.sha256)` | 0 | `26/26` paper-local entries passed |
| `(cd research/publication_proxy_calibration_20261026_v1 && sha256sum -c ALL_FILES.sha256)` | 0 | `74/74` final task entries passed |

The prior negative P2 statement in `A_RETURN.md` and the prior zero-generation
section in `ZERO_TRAINING_EVIDENCE.md` are retained as historical A evidence.
The current scientific accounting is only the remediation raw ledger,
calibration result and `A_REMEDIATION_RETURN.md`.

## Final validation

- Focused P1: 4 tests, exit 0.
- Combined P1/matcher/raw-chain suite: 16 tests, exit 0.
- Formal pre-generation receipt: `END_TO_END_PREFLIGHT_PASS`.
- Paper E: 15 pages, 6,879 extracted tokens, 51,326 text bytes, 24 cited = 24
  bibliography entries, no orphan/missing citation keys, three source figures,
  one measurement-chain use and one visibility-figure use.
- P2: 40 raw rows, 36 unique question/arm pairs, four bounded retries, 2,609
  output tokens, 33,207 input tokens, zero training calls/tokens.
- Actor visibility: all 40 raw rows passed the forbidden-key/UID payload audit.
- Documentation lint and `git diff --check`: exit 0.
