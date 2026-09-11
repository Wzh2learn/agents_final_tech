# guard sentinel fixture

> Purpose: permanent regression target for the pre-commit summary-recompute guard.
> Lives under tests/ (NOT docs/) so it does not enter the docs-side marker census
> nor docs_lint coverage. Do not edit casually: tests/test_guard_sentinels.py asserts on it.

The file carries one genuine line-start receipt block whose digest matches the fixture
artifact. It is the POSITIVE CONTROL: any counterexample run must first prove this passes.

<!-- SUMMARY-GUARD
artifact: tests/fixtures/guard/sentinel_artifact.json
sha256: 6751dc29a0874394082a828404208cdb74eb481e5d6dab519b232781f3cbbf7c
claims:
  payload.sentinel = 1
END-SUMMARY-GUARD -->
