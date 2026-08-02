# Audit Report — Loop C (de7336b + 97b8b9e)

- **Date:** 2026-08-02
- **Model:** deepseek-v4-flash-0731
- **Scope:** `de7336b` (schema synonyms) and `97b8b9e` (OCR prompt)
- **Verdict:** ✅ **ACCEPTED**

## Files changed (de7336b~1..97b8b9e)
- `config/m1_table_schema.json` (+711) — new file
- `scripts/m1_statement_parser.py` (+9/−2) — OCR vision prompt only
- `scripts/m1_accuracy_eval.py` (+1/−1) — use `resolve_schema_path()`
- `scripts/m1_rag_ingest.py` (+1/−1) — use `resolve_schema_path()`

## Findings

1. **Frozen-test gate — ✅ PASS.** `tests/test_m1_service.py` is NOT modified
   across the range (git grep: no match). All 18 tests pass:
   `18 passed in 0.03s`.

2. **Schema changes are additive — ✅ PASS.** `resolve_schema_path()` is a full
   **replace** (config/ wins over frozen `~/wzh/m1_samples/...`), so field loss
   was a real risk. Field-level diff vs the frozen default shows **zero fields
   removed** in any table or `header_meta_fields`. Table2 *adds* `持仓数量`,
   `摘要`. Synonym count: config 238 vs frozen 200 → **exactly +38**, matching
   the commit message.

3. **OCr prompt change is low-risk — ✅ PASS.** `97b8b9e` only edits the
   `_OCR_VISION_PROMPT` constant (adds a markdown-table format example). No
   parser/tokenizer logic touched.

4. **Hit-rate math — ⚠️ NOTE.** The audited check `print(round(7/8*100,1))`
   via `scripts/qwen_harness_tools.py code_interpreter` returns **87.5**, which
   does **not** reconcile with the commit's claimed **93.8%** (31.2% → 93.8%).
   `93.8%` appears only in the commit message and in no committed artifact.
   The synonym/shape changes are sound, but the headline figure is unverified
   against this formula — either a different denominator (e.g. 15/16) or an
   optimistic report. Recommend re-running the live accuracy eval to confirm.

5. **Working tree cleanup — ⚠️ NOTE (out of scope).** Uncommitted changes exist
   (`docs/experiments/2026-07-31_72b_reevaluation.md`,
   `docs/experiments/2026-08-01_field_accuracy.json`, untracked `.omc/`). Not
   part of the audited range but flagged so Loop C can decide on cleanup.

## Conclusion
Both commits are correct, targeted, and pass the frozen test gate. Blockers:
none. Follow-up: reconcile the 93.8% vs 87.5% figure.