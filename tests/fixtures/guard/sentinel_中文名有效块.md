# guard sentinel fixture

> Purpose: permanent regression target for the pre-commit summary-recompute guard.
> Lives under tests/ (NOT docs/) so it does not enter the docs-side marker census
> nor docs_lint coverage. Do not edit casually: tests/test_guard_sentinels.py asserts on it.

CJK filename on purpose: this is the RW-1 regression target. The pre-commit hook used to
enumerate staged paths without core.quotepath=false, so a non-ASCII path came back as a
quoted octal escape string, git cat-file could not resolve it, and the guard was skipped
with only a WARN (fail-open). tests/test_guard_sentinels.py derives a tampered copy of
this block at runtime (digest replaced by 0x64) and asserts it is rejected.

<!-- SUMMARY-GUARD
artifact: tests/fixtures/guard/sentinel_artifact.json
sha256: 6751dc29a0874394082a828404208cdb74eb481e5d6dab519b232781f3cbbf7c
claims:
  payload.sentinel = 1
END-SUMMARY-GUARD -->
