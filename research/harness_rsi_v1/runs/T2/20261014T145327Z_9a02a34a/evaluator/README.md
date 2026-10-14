# R-axis independent evaluator

This directory contains a deterministic, Python 3.12, standard-library-only evaluator for the bounded T2 engineering qualification slice.

## Usage

```bash
python3 evaluator/evaluate.py --case evaluator/fixtures/call_boundary_block.json --out -
```

Exit codes are:

- `0`: a normal `ALLOW_WITHIN_SCOPE`, `BLOCK`, or `REVIEW_REQUIRED` result was written.
- `2`: CLI usage error.
- `3`: a fail-closed result was written because the bundle was incomplete, empty, unsupported or hash/path mis-bound.

The qualification runner invokes every synthetic fixture and every T1 v3 case bundle:

```bash
python3 evaluator/run_qualification.py --pass-id PASS_1
```

## Boundaries

- Evaluates direction R only; R, C and S are never combined.
- The candidate owns only candidate-artifact bytes. Candidate scoring code, labels, decisions and rubrics are never parsed.
- Synthetic evidence uses file SHA-256. T1 evidence uses the canonical Git blob id read-only from `HEAD:<path>`.
- Invalid or empty bundles fail closed and do not count as successful evaluation.
- No sealed material is present or read.

## Unverified surfaces

- Filesystem permissions separating candidate and evaluator identities are not implemented.
- The T1 adapter maps independently reviewed T1 v3 records to frozen assertion signatures; Loop C must audit that adapter.
- The fixtures establish known-signature discrimination, not population-level reliability.
- C/S evaluators, human agreement, production deployment and runtime performance are out of scope.
