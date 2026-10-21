# G2 Target-Dependency Consumption Verification

Date: 2026-10-22, Asia/Shanghai

Status: `DEV_CANDIDATE_CONTINUE_WITH_LIMITED_CLAIM`

Evidence identity:

- three natural model candidates from the qualified NtripBrowser commit;
- seven explicitly labelled synthetic mechanism controls;
- deterministic isolated decode probes, zero model/judge calls.

## Research Question

How can a migration verifier allow reasonable equivalent implementations while
rejecting incomplete migration, dead target calls, unused target results and
old-API fallbacks?

The previous NtripBrowser result showed why behavior-only verification is not
enough: BASE passed all seven repository tests while failing to implement
`chardet -> cchardet`. The failure was masked when an unimported old detector
raised and the function fell back to UTF-8.

## Compared Verifiers

1. **Basic behavior:** the target decode path succeeds on a UTF-8 fixture.
2. **Static contract:** target import/call presence and source import/call
   absence.
3. **Runtime consumption:** a fake target detector records calls and returns a
   non-UTF-8 encoding for a legacy byte fixture; the verifier checks that the
   returned value is actually consumed.
4. **Hybrid:** runtime consumption, extended behavior and no source dependency.

Controls cover alias import, nested wrapper, dynamic import, adapter wrapper,
dead target call, unused target result and swallowed old-API fallback.

## Results

| Verifier | Correct | False accepts | False rejects | N |
|---|---:|---:|---:|---:|
| Basic behavior | 6 | 4 | 0 | 10 |
| Static contract | 8 | 2 | 0 | 10 |
| Runtime consumption | 10 | 0 | 0 | 10 |
| Hybrid | 10 | 0 | 0 | 10 |

Natural candidates:

- BASE: basic behavior passes, static/runtime/hybrid fail;
- PROSE: all four views pass;
- STRUCTURED: all four views pass.

Synthetic controls show the specific failure mechanisms:

- dead target call and unused target result pass static presence checks;
- old-API fallback passes the UTF-8-only behavior fixture;
- alias, wrapper, dynamic import and adapter forms are accepted by the
  consumption probe.

## What This Adds Beyond Existing Work

SWE Refactor Bench already separates migration completeness from behavioral
correctness and uses multi-stage verification. Therefore, “tests plus a
structural check” is not a contribution by itself.

The narrower candidate contribution is a verifier that checks **target result
consumption under controlled runtime intervention**, allowing alias/wrapper/
dynamic/adapter implementations while rejecting dead calls and ignored results.
This remains a development method candidate until it is tested on multiple
real commits and independent VALID/INVALID/UNRESOLVED references.

## Limits And Stop Conditions

- The synthetic controls are mechanism probes, not natural error frequencies.
- The isolated decode probe is not a full application execution trace.
- The current reference labels are deterministic controls, not human semantic
  gold.
- The result does not establish full semantic equivalence.
- Continue only if a second/third real migration reproduces the behavior-only
  false-positive mechanism and the consumption verifier improves false
  acceptance without rejecting reasonable implementations.
- If extended behavior tests or a simpler static/runtime rule are sufficient,
  narrow G2 to an evaluation-design finding rather than a method contribution.

## Reproduction

```text
python research/publication_thesis_goals_v1/g2_contract_verifier.py
python -m pytest -q research/publication_thesis_goals_v1/test_g2_contract_verifier.py
```

Observed tests: `3 passed`. Raw case rows and summaries are in
`G2_CONTROL_RESULTS.json`.
