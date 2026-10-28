# Loop A Return: Word Delivery, Scoring V3, New-Family Diagnostic

Task: `word-scoring-new-family-a-20261027`
Date: 2026-10-27 (Asia/Shanghai)
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `a2463f555f4ede2afcebb14dea2b627a0e5b99db`
Authority LF SHA256: `1414d5b1ce4dc1b47c736c2b5d661366b19d55faa3736dbae5d7c7a7066aac93`

## Scope And Boundary

- Completed one bounded A task under `research/word_scoring_new_family_20261027_v1/` and the two explicitly owned thesis-draft files.
- Preserved historical raw, V2 outputs, stop decisions, manifests, frozen files, production services, credentials and `memory/`.
- Training, LoRA/SFT, judge, paid API, service/endpoint, production, Memory writeback, formal submission, payment, public release and external contact: 0.
- This return does not claim DOCX/PDF visual acceptance, formal C acceptance, cross-source validation or method gain.

## Word Source Package

- Package: `paper_e_word/`; canonical Pandoc source: `paper_e_word/paper_e_word.md`.
- Sole content source remains the complete two-case manuscript at `research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex`; P1/P2 and this round's new-family results were not added.
- Source checks: PASS; structured abstract 208 words; 5 keywords; 3 figures; 4 editable Markdown tables; 24 cited keys and 24 bibliography entries; declarations and Data Availability present; raw BibTeX absent; owner fields marked `TBD_OWNER`.
- Conversion command is frozen in `paper_e_word/CONVERSION_COMMAND.txt` for local Pandoc 3.2.1:

  ```bash
  pandoc --version | head -n 1
  pandoc paper_e_word.md --from=markdown+pipe_tables+tex_math_dollars \
    --resource-path=. --reference-doc=reference_style.docx --output=paper_e.docx
  ```

- `reference_style.docx` targets 10 pt Times New Roman where supported. D must perform the Windows conversion and GB10 LibreOffice rendering; A did not run it.

## Scoring V3

- `scoring_v3/test_scoring_v3.py`: 7/7 targeted paired controls pass:
  - equal numeric values: correct role-only accepted, wrong-role-only rejected, indistinguishable role reference PENDING;
  - required evidence: exact+exact passes, exact+broad remains PENDING and is judged per operand;
  - single-element numeric span: legal positive accepted, contradictory `-999999` mutation rejected.
- V2 regression: 17/17 pass. Diagnostic interface controls: 5/5 pass.
- Pure rescore uses the immutable first 40-call batch selecting 36 final attempts plus saved oracle, blank-type and question-only outputs; no model load and no generation records.
- V2→V3 differences: 109 layer/UID difference rows; changed UID counts are blank-type 6, first-batch 8, oracle 11 and question-only 11. Final status counts remain:
  - blank-type: `12 ACCEPT / 19 REJECT / 5 REASONABLE_UNKNOWN`;
  - first-batch: `22 REJECT / 13 STRICT_FAIL / 1 PENDING_ADJUDICATION`;
  - oracle: `31 ACCEPT / 5 REASONABLE_UNKNOWN`;
  - question-only: `31 ACCEPT / 5 REASONABLE_UNKNOWN`.
- Historical `2/3/3`, `31/5`, `12/19/5` and manifests were not rewritten.

## Exposure And Freeze

- `exposure/EXPOSURE_MANIFEST.json` records source splits, training/development/confirmation/error-pool registers, prior UIDs, table/report families, inspected questions, hashes and exclusion counts.
- Eligible unexposed family count: 38. Deterministic selection froze 8 natural TAT-QA table families, one UID each, with answer/task diversity.
- Source identity: `SAME_SOURCE_NEW_TABLE_FAMILIES`; historical pretraining exposure is not auditable, so no pretraining-disjoint claim is made.
- `exposure/PANEL_FREEZE.json` and `mechanism/MECHANISM_FREEZE.json` were written before model output. Frozen items include reference-side question/scale/direction/evidence/accepted answers, question-only typed baseline, shared calculator, Scoring V3, model/checkpoint/tokenizer/decode/output contract and exactly 24 visible-only D/T/M prompts.

## Zero-Model Baseline

- Path: `baseline/results/ZERO_MODEL_BASELINE.json`.
- 8 rows: `7 REJECT / 1 REASONABLE_UNKNOWN`; 2 applicable and 6 failure/abstention; model calls and generation records: 0.
- This is a deterministic applicability diagnostic, not an accuracy or method-gain estimate.

## Three-Arm Diagnostic

- Raw responses: `generation/results/RAW_RESPONSES.jsonl`, 24 persisted rows (D/T/M = 8/8/8), with per-call receipts under `generation/receipts/`.
- Raw strict status: `STRICT_FAIL` for all 24 because of reasoning prefixes, truncation or incomplete JSON.
- Semantic/interface extraction after the raw strict check:
  - D: interface PASS 4, ACCEPT 2, REJECT 2, STRICT_FAIL 4; numeric correct 4; citation EXACT 2.
  - T: interface PASS 1, ACCEPT 1, STRICT_FAIL 7; numeric correct 1; citation EXACT 1.
  - M: interface PASS 0, STRICT_FAIL 8; numeric correct 0; citation unavailable 8.
- Complete strict delivery: D/T/M = 0/0/0. Formula status for arithmetic rows is `NO_EXPLICIT_FORMULA` in D and `UNAVAILABLE_INTERFACE_FAILURE` in T/M; non-arithmetic rows are `NOT_APPLICABLE`.
- T and M do not match on the frozen per-UID vector, but M has no repair beyond T and no binding validation passes. Stop decision: `M_DIFFERENCE_REQUIRES_REVIEW`; no confirmation card was prepared and no adapter was trained.
- Dominant alternative explanations are output-budget exhaustion before contract, raw strict format failure, and reference-unit ambiguity on some span/count rows. These are separated from any unsupported mechanism claim.

## Persistent Budget And Generation Accounting

- External append-only ledger: `/home/testuser/wzh/research_runs/persistent_budget/word_new_family_20261027/ledger.jsonl`.
- Ledger SHA256: `c7bd1f7207b610ad17c194727a8d0affdb0105996ed2e97603cfeea408ca71ac`.
- Physical reservations: 27; persisted raw responses: 27 reservation events total, 24 raw responses; real model generate calls: 25 (24 persisted + 1 discarded before raw append); preserved failures: 3 (2 pre-model tokenizer/reservation faults, 1 loader discard); bounded retries: 2.
- Persisted actual tokens: input 28,074, output 12,014, total 40,088. Uncertain consumed reservation upper bound: 5,966. Ledger consumed total: 46,054 / 240,000.
- Last generation process wall time: 718.5607316493988 s. Reservation-before-call, raw/fsync-before-scoring, crash/restart/output-directory/retry persistence and attempt-37/token-cap rejection are covered by `budget/BUDGET_FAULT_TEST_RECEIPT.json` (11/11 pass, no model load).
- No service, endpoint, judge, paid API, production or external harness calls; training 0.

## Nearest Work And Counterexample

- `mechanism/NEAREST_WORK_COMPARISON.json` covers the three pre-existing project notes: FinRank, VeriFin and Same-Number Citation Swaps.
- Single tested difference: M alone adds deterministic row/period/role/unit binding validation before execution.
- Counterexample: ordinary program-aided reasoning and typed schemas are established and are not claimed as novel.

## Verification

- Focused tests: Scoring V3 7/7; diagnostic interface 5/5; V2 regression 17/17; persistent-budget fault tests 11/11; all PASS.
- Word source rebuild/check: PASS (`abstract_words=208`, `references=24`).
- JSON parsing and hash validation: see `validation/VALIDATION_RECEIPT.json` and `validation/ARTIFACT_HASHES.json`.
- Document lint: PASS (0 fail / 0 warn); report at `/tmp/word_new_family_docs_lint.json`.

## Unknowns And Next Gate

- Historical base-model pretraining exposure is unauditable.
- One discarded model response has unknown actual usage; its reservation upper bound remains consumed.
- Frozen reference units may conflict with visible semantics for several non-arithmetic rows.
- D-side Pandoc conversion, DOCX/PDF visual checks and C review remain outside A. No confirmation, adapter training or new-family method claim is authorized by this return.
