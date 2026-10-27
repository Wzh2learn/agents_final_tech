# Loop C Fixed-Snapshot Review: Word, Scoring V3, New-Family Diagnostic

Task ID: `word-scoring-new-family-c-20261027`
Date: 2026-10-27, Asia/Shanghai
A scientific snapshot: `62c637ba5f3a21e370669a596298d45d3544ca82`
Integrated snapshot including D Word render: `911fb800c01ab145514eaffbfbbf25a7b0c5293b`
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `a2463f555f4ede2afcebb14dea2b627a0e5b99db`
Authority LF SHA256: `1414d5b1ce4dc1b47c736c2b5d661366b19d55faa3736dbae5d7c7a7066aac93`

## Ownership And Boundary

Perform exactly one independent review of the fixed integrated snapshot. Own
only:

- `research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md`
- `research/word_scoring_new_family_20261027_v1/audits/TASK_RESULT_C.json`
- focused audit scripts/fixtures below the same `audits/` directory.

Do not edit A/D source, raw, scores, Word/PDF, manifests, thesis, external
ledger, memory or the unique prompt. Do not generate model answers, train,
call judges, probe production or use external services. Other loops may work
in the repository; do not revert unrelated changes.

## 1. Paper E Word Route

Independently verify:

- `paper_e_word.md` remains the unchanged extracted source and
  `paper_e_word_fixed.md` is a structural conversion derivative;
- author placeholders, 208-word four-part abstract, five keywords, three
  figures, four editable tables, numeric citations, 24 references,
  declarations and Data Availability are present;
- `paper_e.docx` has real Word tables and no raw TeX/BibTeX keys;
- `rendered_final/paper_e.pdf` and all 14 page PNGs match
  `D_PAGE_HASHES.sha256`;
- the final PDF is a real LibreOffice 24.2 render, not a fallback text PDF;
- page review covers every page for clipping, overlap, table continuation,
  figure sharpness, formula readability, references and final-page integrity.

Distinguish internal Word-route acceptance from publisher formatting,
submission acceptance and school recognition.

## 2. Scoring V3

Re-run the paired controls and verify the three required boundaries:

1. same numeric values in different rows: correct role-only accepted,
   wrong-role-only rejected, indistinguishable role PENDING;
2. exact + exact passes, exact + broad is PENDING, each required evidence item
   judged separately;
3. one-element numeric span requires answer/numeric_value consistency and
   rejects contradictory values.

Independently replay the immutable first-batch and saved-actor pure rescore.
Check that old `2/3/3`, `31/5`, `12/19/5` and V2 artifacts remain unchanged,
and that V2-to-V3 differences are reported by layer/UID rather than converted
into natural error rates.

## 3. Exposure And Frozen Panel

Audit the exposure registers and selection:

- source identity is `SAME_SOURCE_NEW_TABLE_FAMILIES`, not cross-source;
- 8 unique table families and 8 UIDs were frozen before model output;
- answer/task signatures are diverse;
- training, development, confirmation, error-pool and inspected-family
  exclusions are reproducible;
- historical pretraining exposure remains explicitly unauditable;
- zero-model baseline and Scoring V3 were frozen before generation.

## 4. Persistent Budget And Raw Accounting

Verify the external ledger at
`/home/testuser/wzh/research_runs/persistent_budget/word_new_family_20261027/ledger.jsonl`
and reconcile:

- 27 physical reservations;
- 25 real `generate` calls;
- 24 persisted raw rows;
- 3 preserved pre-raw failures, including 1 real generation discarded before
  raw append;
- 2 persisted retries;
- persisted actual input/output totals 28,074 / 12,014;
- uncertain consumed upper bound 5,966;
- ledger consumed 46,054 / 240,000;
- training/judge/paid API/service/production calls all zero.

Check reservation-before-call, raw/fsync-before-scoring, restart/output-dir
persistence, separate generate/resume/rescore and pre-load cap rejection.

## 5. D/T/M Mechanism Decision

Independently inspect all 24 raw responses and Scoring V3 diagnostic rows.
Verify the reported outcomes:

- D: 2 ACCEPT, 2 REJECT, 4 STRICT_FAIL;
- T: 1 ACCEPT, 7 STRICT_FAIL;
- M: 8 STRICT_FAIL;
- M has no repair family beyond T;
- complete strict delivery is zero for all arms.

Decide whether `M_DIFFERENCE_REQUIRES_REVIEW` should become `STOP_M`, remain
conditional, or require another bounded test. Separate binding-mechanism
effects from raw strict failure, output-budget exhaustion and reference-unit
ambiguity. Do not infer method gain from interface normalization.

## Required Judgment

Return one verdict:

- `ACCEPTED`;
- `CONDITIONAL`;
- `REJECTED`.

Separate blocking defects from limitations. Include exact paths/lines,
independent hashes/counts, commands and exit status, Word visual status,
Scoring V3 validity, exposure boundary, budget reconciliation, D/T/M decision,
and the smallest follow-up. Independent AI review is not human gold, publisher
acceptance or school recognition.
