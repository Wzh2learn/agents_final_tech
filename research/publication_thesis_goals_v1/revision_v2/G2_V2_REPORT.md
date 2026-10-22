# G2 V2 Report: Target-Result Consumption On A Real Migration

Date: 2026-10-22, Asia/Shanghai

Status: `CONTINUE_NARROWED_CANDIDATE`

## Question

Under a change contract that permits reasonable equivalent implementations,
when do target-dependency result-consumption checks reduce false acceptance or
false rejection beyond repository behavior tests and literal static checks?

## Independent Real Object

- Repository: `https://github.com/remix/partridge`
- Parent: `daefcbe6a03e92a0bfc0c2433279b9fd3d179f6c`
- Migration commit: `09e89d98b5a00db44394204d2f3e70c220b51764`
- Change: `chardet -> cchardet` in `partridge/utilities.py` and `setup.py`
- License: MIT
- Environment: GB10 Python 3.11.16, NumPy 1.23.5, Pandas 1.5.3, pytest 7.4.4
- Test harness compatibility patch removes obsolete `pytest.raises(message=)`
  arguments and is applied identically to all variants.

The parent and gold commits both pass all 42 repository tests. The repository
behavior suite therefore cannot identify this dependency-contract migration.

## Controls On The Real Repository Surface

| Object | Reference | Repo tests | Meaning |
|---|---|---:|---|
| Natural parent | INVALID | 42/42 | Old dependency remains; behavior-only false accepts |
| Natural gold | VALID | 42/42 | Exact migration commit |
| Target call then source fallback | INVALID | 42/42 | Calls `cchardet`, discards result, uses `chardet`; behavior-only false accepts |
| Alias implementation | VALID | 42/42 | Equivalent target import; literal static contract false rejects |

Hardcoded UTF-8 and Latin-1 probes were also run. They pass 40/42 rather than
42/42, so this repository suite detects those two simplistic failures. Those
negative probes remain evidence against claiming that all fallbacks are hidden.

## Verifier Result

The v2 verifier distinguishes `VALID`, `INVALID` and `UNRESOLVED`, rejects the
audited call-then-discard pattern, permits alias/dynamic target access and keeps
cache-equivalent observation unresolved. On 11 rows, the combined
target-consumption rule has 10 correct, 0 false accepts, 0 false rejects and 1
unresolved among resolved controls. Runtime evidence alone still cannot certify
migration completion because source-only parent code is not a target migration.

## Decision

Continue G2 as a **task-scoped completion-evidence candidate**, not a general
verifier contribution. The current evidence supports the narrower proposition:

> On this real dependency migration, repository behavior tests alone miss an
> old-dependency fallback, while literal static checks reject a valid alias.
> Controlled target-result consumption plus behavior distinguishes the four
> objects.

Stop or narrow if another independent migration family shows that a simpler
static rule or stronger behavior tests remove the same errors, or if the
consumption intervention cannot distinguish valid caches/equivalent adapters
without excessive unresolved cases.

## Reproduction

```text
python research/publication_thesis_goals_v1/revision_v2/g2_contract_verifier_v2.py
python -m pytest -q research/publication_thesis_goals_v1/revision_v2/test_g2_contract_verifier_v2.py
```

Formal GB10 results: `G2_CONTROL_RESULTS_V2_GB10.json`.
