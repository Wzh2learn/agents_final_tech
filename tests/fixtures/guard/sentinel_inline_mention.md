# guard sentinel fixture

> Purpose: permanent regression target for the pre-commit summary-recompute guard.
> Lives under tests/ (NOT docs/) so it does not enter the docs-side marker census
> nor docs_lint coverage. Do not edit casually: tests/test_guard_sentinels.py asserts on it.

This paragraph mentions the receipt-block opener mid-line, as prose: <!-- SUMMARY-GUARD (written here deliberately). There is NO real receipt block in this file, so the
line-start-anchored opener count is 0 and the parseable block count is 0.
Expect: guard check rc=0 with the message that there is no block to verify.
Regression covered: RW-3 (an unanchored opener regex used to count this prose mention
as an opening, making openings=1 != blocks=0 an unconditional FAIL, which blocked the
whole file from ever being committed).
