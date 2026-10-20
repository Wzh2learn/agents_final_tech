# TQ5_PRE_RUN_REVIEW_v1 - Loop C independent pre-run review (S4 gate)

> Reviewer: `loopc_tq5_prereview` (fresh-context Loop C agent; delegated by Loop D under
> `OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md`, S4). Date: 2026-10-16 17:30 Asia/Shanghai.
> Scope: pre-freeze independent check of the TQ-5 source-separation developmental panel -
> source exclusion, references & scoring, input leakage, budget/schedule - performed BEFORE
> any TQ-5 model output existed.
> **Verdict: NO_SUBSTANTIVE_BLOCKER - the freeze holds; the conditional single-window run may proceed.**
> 中文摘要: 独立预检通过。来源排除可复算（12/12 选中表均不在 221 项排除并集内）；参考、评分与
> 原始 TAT-QA 语料逐字段一致（12/12）；输入无泄漏；预算与调度合规；v1→v2 修订为“可操作性修复”
> 而非降标。无实质阻断项，TQ-5 可进入运行。

## 0. Artifacts and method

- Script (independent re-implementation; no builder imports):
  `reviews/TQ5_PREREVIEW_RECOMPUTE_v1.py`, sha256
  `EE171292849369B3752E7ADDCFA8A0226ADB76DC5405F8E227E743096366132E`.
- Output: `reviews/TQ5_PREREVIEW_RECOMPUTE_v1.json`, sha256
  `30A1F0294095AFE5CE23BEC62F0A351F6FB5C8639F75845F22133E0DC59CBFE9`.
- Method note: the script was created via a controlled shell write after repeated `apply_patch`
  channel format failures (channel fault, not content fault); integrity validated by
  `python -m py_compile`, line review, and the hashes above.
- This `reviews/` directory is a post-freeze addition, deliberately OUTSIDE the frozen
  MANIFEST/pins; the frozen 49-file set is verified unchanged in section 1.

## 1. Frozen-set integrity - PASS

- `MANIFEST.json`: 49/49 files - raw sha256 recomputed OK; LF-normalized pins recomputed OK
  (`execution_v1/tq5_material_pins_lf_v1.json`, including its `source_manifest_sha256` link).
- No unexpected files outside the manifest (allowed exclusions only: `runs/`, `__pycache__`,
  this `reviews/` directory).
- Raw corpus: `tatqa_dataset_train.json` `2df6e722...`, `tatqa_dataset_dev.json` `8da095a8...`
  match `raw/FETCH_RECEIPT.txt` (TAT-QA repo tarball, master branch, fetch 2026-10-13).

## 2. Source exclusion - PASS (table-disjoint claim holds)

- Recomputed exclusion sets: origin_manifest 182 uids; pool_inventory 50 distinct uids
  (59 entries); case_provenance 12; TQ-4 natural log 4. Union recomputed = 221 = SELECTION_LOG's 221.
- **All 12 selected uids lie outside the union (0 hits); 12 unique table uids.**
- Exclusion source files' current sha256 all equal the hashes recorded at freeze.
- case_provenance rows cross-checked against raw records (uid + question_uid): 12/12 OK, i.e.
  TQ-3-era case tables are captured; TQ-4 N1-N4 uids are captured via the TQ-4 natural log.
- WP2 dry-run role lists are subsets of the origin manifest; WP2 `origins_total`=182 consistent.
- The package claims only **table-disjoint** status (no report-level independence, no
  "unseen by training" claim): confirmed by text scan - no overclaim found.

## 3. Selection determinism - PASS (exact reproduction)

- Independent re-run of the full eligibility pipeline reproduces every skip count exactly:
  record_excluded 221; skip_answer_from 3212; skip_answer_not_numeric 4749;
  skip_layer_unclassified 1560; skip_eval_none 9; skip_eval_mismatch 19;
  skip_pct_encoding_ambiguous 36; skip_operand_missing 2; qualified 2147 (difference) /
  493 (ratio) / 1329 (percentage_change); eligible_records 2258 = log value.
- Hash-order selection (seed 20261016; sha256(seed|table_uid|question_uid) ascending, first 4
  per layer, unique-uid guard) reproduces the frozen 12 rows exactly - same task order
  (T01-T12), same uids, same question uids, same first-16 rank keys; layer order
  difference -> ratio -> percentage_change.

## 4. References and scoring - PASS (12/12)

For each of T01-T12 (independently re-derived from the raw records):
- reference `official_reference` equals the raw record's fields (answer, derivation,
  answer_type, answer_from, scale, rel_paragraphs, req_comparison): 12/12 exact.
- Derivation recomputation matches the recorded answer within `0.5 x 10^-d`
  (d = decimal digits of the recorded answer) under the layer's encoding
  (direct, or x100 for percent-encoded ratios/changes): 12/12.
- Layer re-classification (spec v2 shape + encoding rules) equals GROUPS.json and the scoring
  `notes`: 12/12.
- scoring files: expected == answer; expected_precise == float(answer); abs_tolerance == the
  tolerance rule; unit_kind per spec mapping (percent / ratio / plain); compare_mode=numeric;
  scoring_version=v21: 12/12.
- Operand locatability (every numeric literal, minus `*100`, present in normalized
  table/paragraph text): 12/12.
- Per-file sha256 recorded in SELECTION_LOG's `selected[*].files` match the current files: 12/12.

## 5. Input leakage - PASS (12/12)

- `inputs/T*.json` keys are exactly {task_id, variant, question, table, paragraphs};
  `variant` = original.
- Table and paragraphs are byte-equal (after JSON load) to the raw record - no perturbation,
  no injection, no added context.
- Zero hits for forbidden markers: `*100`, `×100`, `"answer"`, `"derivation"`, `"reference"`,
  `perturb`, `stratum`, `injected`, `candidate`; table uid and question uid do not appear
  anywhere in the inputs.
- Prompt-level isolation for actor/B/C rendering was separately point-checked
  (`chain_point_checks_tq5_DESKTOP-EKG77SP_20261016T084722Z.json`: 14/14, including
  prompt-isolation-no-labels, b-sees-evidence / c-does-not, and duplicate-stimulus-pair byte
  checks); the current runner file sha256 equals the point-checked runner (`a7fb4ae2...`) and
  the runner that executed TQ-4.

## 6. Budget, schedule, and run-state - PASS

- `chain_config_tq5.json`: 36 steps = actor 12 / b 12 / c 12, unique keys 36; actors first, in
  T01-T12 layer order; B/C alternation pattern b,c,c,b,b,c,... as frozen; every b|c step
  references its actor output (`source_key = actor|Txx`).
- Budget: gen_cap 40, retry_cap 4, token_cap 400000, window_min 90, allowed_dates
  2026-10-16..19 - all within S4 limits.
- All referenced paths resolve (templates v2, MANIFEST, LF pins, scoring dir, GROUPS,
  authorization file, chain master ledger).
- Chain master ledger currently contains TQ-4 only (72 lines: reserve 36 / settle 36);
  `runs/` is empty - confirmed **no TQ-5 model output has occurred** (freeze precondition holds).

## 7. v1 to v2 revision legitimacy - PASS (operability fix, not criteria lowering)

- Re-measured corpus facts (whole raw corpus): slash-derivations 3436 (3133 in eligible
  records); those with explicit `*100`: 4; items passing all gates under the v1
  "percentage_change = contains '/' and '*100'" rule: 1. This matches the preserved v1
  shortage record (percentage_change trace selected = 1; NOT_RUN, no substitution).
- v2 changes only the CLASSIFICATION shape/encoding test that was inoperable on the corpus;
  numerical gates (eval within tolerance; operand locatability; answer_from; numeric answer;
  non-empty derivation; one question per table; unique uids; seed/hash order;
  shortage -> NOT_RUN) are unchanged and were independently reproduced.
- The revision was frozen before any model output (section 6); therefore it cannot be
  result-contingent, and no criteria lowering or substitution is present.

## 8. Non-blocking notes and limitations

- N-1: spec v2 cites "1/3061 slash-derivations"; recomputed exact figures are 4/3436 (all
  records) and 4/3133 (eligible), with exactly 1 fully qualifying item - qualitatively
  identical ("essentially never encodes percent-change as *100"). The cited denominator
  appears to predate exclusion-filtering or use a marginally different normalizer. Non-blocking.
- Upstream provenance is verified only to the extent of the recorded fetch receipt + file
  hashes (raw tarball master commit remains UNRESOLVED, as the package already states).
- Report-level independence remains unverifiable from available sources; all public claims
  must keep the "table-disjoint developmental panel" framing.

## 9. Verdict and boundaries

**NO_SUBSTANTIVE_BLOCKER.** The frozen TQ-5 package may proceed to the conditional
single-window run under S4 with no further owner steps. All four mandated check areas pass
(source exclusion / references & scoring / input leakage / budget).

Boundaries: this review certifies the above checks only; it is not a scientific validation of
the references (reference_validity stays NOT_ESTABLISHED), not a confirmatory result, and it
does not authorize anything beyond S4. Any modification to the frozen 49-file set (or to the
exclusion sources or the TQ-5 config) after this review invalidates it and requires a re-check.

- Reviewer: `loopc_tq5_prereview` (Loop C, fresh context; not the builder).
- Evidence: `reviews/TQ5_PREREVIEW_RECOMPUTE_v1.py` / `.json` (hashes in section 0).