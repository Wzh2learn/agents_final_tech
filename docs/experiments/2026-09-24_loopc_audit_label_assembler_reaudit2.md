# Loop C third-round audit of the assembler (model qwen3.8-max)

> Dispatched 2026-09-24 against commit adcd3bd; evidence packet inline; no tools; 1 turn(s), cost $0.1522.
> Verdict: PASS_WITH_NOTES - top-level type validation first and coded; no bare exceptions on any enumerated malformed shape; dead guard removed; tests cover the new paths; independence and artifact shape unchanged.
> Body verbatim.

**VERDICT: PASS_WITH_NOTES**

**Finding 1 — Top-level type validation is first and coded: CONFIRMED.**
The first three statements of `assemble` are `isinstance(r1, dict)`, `isinstance(r2, dict)` (combined guard → `invalid_review_doc`) and `isinstance(adj_doc, dict)` (→ `invalid_adjudication_doc`), all raising `LabelAssemblyError` with machine-readable codes. No `.get` dereference precedes them. The prior REJECT's core defect (bare `AttributeError` on list/string/number/null top-level docs) is fixed: all four non-dict shapes now hit the guards first.

**Finding 2 — No bare KeyError/AttributeError/JSONDecodeError on the enumerated malformed shapes: CONFIRMED.**
Trace of each shape:
- Non-dict top-level (r1/r2/adj): coded errors per Finding 1.
- Unparseable JSON in `main._load`: `json.JSONDecodeError ⊂ ValueError`, caught and re-raised as coded `invalid_input_json` (with `UnicodeDecodeError` also covered).
- Non-dict `judgments`: `isinstance(judgments, list)` guard → `invalid_review_doc`. Non-dict judgment items and missing keys (`sample_id/uid/col/action/target`): `any(k not in j ...)` and type guards → `invalid_judgment` before any `j[...]` subscript; all later subscripts (`a["uid"]`, `a["action"]`, `a["target"]`, `e["sample_id"]`) are provably key-present from upstream guards.
- Non-dict `entries`/entry items: `isinstance(entries, list)` → `invalid_adjudication_doc`; `isinstance(e, dict) and isinstance(e.get("sample_id"), str)` → `invalid_adjudication_entry` before `e["sample_id"]`.
- `sorted(set(j1) | set(j2))` sorts only `(str, int)` tuples enforced by `isinstance(sample_id, str)` / `type(col) is not int` — no mixed-type comparison TypeError (and `type(col) is int` correctly rejects bools).
- `adjudications` values are dict-validated at insertion, so `entry.get(...)` downstream is safe; `missing_adjudication` fires via the `isinstance(entry, dict)` check on `None`.

**Finding 3 — Dead adj type check removed; no newly unreachable guard: CONFIRMED, with one benign redundancy noted.**
Exactly one `adj_doc` isinstance check exists, at the top, before any dereference — the previously-dead late check is gone. `isinstance(entry, dict)` remains reachable (the `None`/missing-adjudication path, covered by `test_missing_adjudication_rejected`). Note: `_judgments_by_pair`'s own `isinstance(doc, dict)` guard and the `isinstance(a["uid"], str)` re-check in the row loop are unreachable via `assemble` (upstream guarantees subsume them). Unlike the prior round's defect, these are shadowed by *safe coded* validation, not by a bare-exception dereference, and the helper guard is exercisable by direct callers/tests — harmless defense-in-depth, not a fail-open bug.

**Finding 4 — Tests cover both top-level non-dict paths: CONFIRMED.**
`test_top_level_non_dict_review_doc_rejected` and `test_top_level_non_dict_adjudication_doc_rejected` exist, matching the two new guard branches. Minor note (name-level evidence only): cannot confirm from names whether the review-doc test exercises both the r1 and r2 disjuncts of the combined guard; recommend asserting both.

**Finding 5 — Independence rules and artifact shape unchanged: CONFIRMED.**
All protocol rules intact and ordered before data processing: generator ∉ {rid1, rid2, aid}; rid1 ≠ rid2; adjudicator ∉ reviewers; both reviews required per (sample, col); disagreement requires adjudication whose validated choice becomes gold; one labelled column per sample (`multiple_columns_per_sample`). Artifact remains pure JSON Lines — one `json.dumps(..., sort_keys=True)` object per `\n`-terminated line, keys exactly the eight LABEL_FIELDS, `quality_grade="Q3"`, LF newlines — with diagnostics confined to the sidecar meta file. No changes to row schema or meta fields relative to the audited baseline.

**Finding 6 (note, non-blocking, pre-existing scope) — Environmental I/O errors in `main` are not coded.**
`path.read_text` / `write_text` can raise `FileNotFoundError`, `IsADirectoryError`, or `PermissionError` as bare tracebacks; these are missing-path/OS conditions rather than the malformed-input shapes in scope, so they don't affect this verdict, but wrapping them (and catching `LabelAssemblyError` in `main` to print `code + detail` instead of a traceback, exiting non-zero) would complete the fail-closed ergonomics. Similarly cosmetic: the combined r1/r2 guard reports `reviewer="r1/r2"` without identifying which document was non-dict — still coded and fail-closed, slightly reduced diagnosability.

**Summary:** The prior REJECT grounds are fully remediated — top-level dict validation is first, coded, and pre-dereference; the dead adj guard is gone; both regression paths are tested; independence semantics and the JSON Lines contract are untouched. PASS_WITH_NOTES on the strength of Findings 3, 4, and 6 (redundant-but-safe guards, r1/r2 disjunct test coverage unverified at name level, uncoded OS-level I/O errors).
