# Independent Loop C audit of the schema role ruling and draft - FIRST PASS (model qwen3.8-max)

> Dispatched 2026-09-24; evidence packet inline; no tools; 1 turn(s), cost $0.1248.
> Verdict: REJECT - strict-verbatim charter: the first protocol excerpt dropped README fence lines 33/46 and trailing spaces on lines 37/47.
> Corrected in commit b5646de; re-audit follows in the sibling file. Body verbatim.

# Independent Loop C Audit — schema role ruling & P1-future draft

**Verdict: REJECT**

---

## Check 1 — Verbatim fidelity of protocol §6 excerpt vs FinQA README lines 31–47: **FAIL (Critical)**

Character-for-character comparison against the inline truth:

1. **Omitted fence lines.** README lines 31–47 comprise 17 lines, including the two markdown fence lines (`` ``` `` at README line 33 and line 46). The protocol §6 block reproduces only 15 lines; both fence lines are absent. The excerpt claims to quote lines 31–47 "逐字如下" (verbatim), yet the quoted range's fence lines are dropped rather than the line range being narrowed or the omission being noted.
2. **Trailing whitespace stripped.** README line 37 ends `...example index for this report. ` (trailing space) and line 47 ends `...no reference provided. ` (trailing space). Both trailing spaces are absent in the protocol excerpt.

All other characters (15 content lines, punctuation, indentation of the `qa.*` keys) match. However, the audit charter states that *any* mismatch between excerpt and README forces REJECT, and the protocol's own claim is strict verbatim quotation. Both deviations are real against the inline truth. **Severity: Critical — forced REJECT.**

*Remediation:* either (a) quote the full 31–47 range including the fence lines using a 4-backtick outer fence, or (b) declare the excerpt as lines 31–47 with markdown fences and trailing whitespace normalized, and record that normalization explicitly in the protocol and the draft JSON. Then re-audit.

## Check 2 — Draft `fields` list vs excerpt: **PASS**

Nine fields: `pre_text, post_text, table, id, qa.question, qa.program, qa.gold_inds, qa.exe_ans, qa.program_re` — exactly the field names appearing in the excerpt, with `qa.*` nesting preserved and prose lines (storage sentence, private-test sentence) correctly excluded. `qa` itself is a container, not listed as a standalone field — consistent with the excerpt's structure and with the protocol's "fields 九项" claim. The `private_test_note` correctly reflects README line 47 (question-only, no reference) and excludes it from binding. **Severity: none.**

## Check 3 — Provenance consistency: **PASS**

- FinQA: repo `czyssrs/FinQA` ✓; head `0f16e2867befa6840783e58be38c9efb9229d742` = 40 hex ✓; `doc_sha256` `eb86779c…07064605` = 64 hex ✓ and identical in draft and protocol §6; `doc_bytes` 6518 matches §6's "6 518 B"; `excerpt_lines` [31,47] matches §6's "第 31-47 行".
- TAT-QA (in `current_corpus_ruling`): head `870accc4…abdc0fbc3` = 40 hex ✓; 4689 B and sha256 `85c39817…15c14d5f` = 64 hex ✓ — both identical to the inline probe record and to protocol §6.

All provenance values agree across draft, protocol, and probe. **Severity: none.**

## Check 4 — BLOCKED ruling for current drift-v0 corpus: **PASS**

The inline TAT-QA probe confirms the README documents only the line-48 note ("facts" and "mapping" fields under `dataset_tagop`); no column-level table schema appears in the verified in-repo metadata. The protocol correctly states the detailed schema lives in the ACL2021 paper and project website, both outside the verified citation pool. Under the official-metadata-only ruling, BLOCKED is the correct and consistent outcome, and the `m1_table_schema` rejection is maintained in both draft and protocol. Draft `current_corpus_ruling` and protocol §6 are mutually consistent. **Severity: none.**

## Check 5 — Scope containment (no P1-future → current-corpus leak): **PASS**

Draft `scope` = "P1_FUTURE_PACKAGE (FinQA process/checkpoint stream); NOT the current drift-v0 corpus package"; `draft_status` = `DRAFT_COMPLETE_PENDING_PACKAGE_BINDING` (not bound); protocol §6 frames the draft solely under the P1-future heading and separately rules BLOCKED for the current package. No language binds the FinQA schema into the current corpus package. No scope leak. **Severity: none.**

## Check 6 — No dataset body fetched: **PASS**

Probe log contains only `*.README`, `*.LICENSE` fetches plus the probe annotation files `facts.txt` and `retrieved_at.txt`. No `dataset/*.json` or any other data-body fetch appears. Protocol §6's claim ("探针只取 README/LICENSE 元数据，未取 dataset/*.json 任何数据体") is corroborated. **Severity: none.**

---

## Summary

| # | Check | Result | Severity |
|---|-------|--------|----------|
| 1 | Excerpt verbatim vs README 31–47 | **FAIL** — fence lines (README 33, 46) omitted; trailing spaces on README 37, 47 stripped, under an explicit verbatim claim | Critical (forced REJECT) |
| 2 | Fields list vs excerpt | PASS | — |
| 3 | Provenance (repo/hex/sha/bytes/lines) | PASS | — |
| 4 | BLOCKED ruling consistency (TAT-QA) | PASS | — |
| 5 | Scope containment, no leak | PASS | — |
| 6 | No dataset body fetched | PASS | — |

**Verdict: REJECT.** Checks 2–6 all pass; the ruling logic, provenance, scope containment, and fetch discipline are sound. The sole defect is Check 1: the excerpt is not character-for-character identical to README lines 31–47 despite the verbatim claim. Per the audit charter this forces REJECT. The defect is presentational, not evidentiary — it is fully remediable by re-quoting with fences included or by declaring the normalization explicitly; no substantive rework of the BLOCKED ruling or the draft is required.
