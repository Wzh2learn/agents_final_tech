# Loop A Task: Word Delivery, Scoring V3, New-Family Mechanism Diagnostic

Task ID: `word-scoring-new-family-a-20261027`
Date: 2026-10-27, Asia/Shanghai
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `a2463f555f4ede2afcebb14dea2b627a0e5b99db`
Authority LF SHA256: `1414d5b1ce4dc1b47c736c2b5d661366b19d55faa3736dbae5d7c7a7066aac93`

## Boundary

Execute one bounded A task on GB10. Other loops may work in the repository;
do not revert or overwrite unrelated changes. Preserve old raw, V2 scores,
stop decisions, manifests and historical reports. Do not touch frozen files,
production services, credentials or `memory/`.

Create and own only:

- `research/word_scoring_new_family_20261027_v1/`
- `research/feedback_learning_phase_b_20261026_v1/thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md`
- `research/feedback_learning_phase_b_20261026_v1/thesis_draft/EVIDENCE_TABLE.md`.

No training, LoRA/SFT, judge, paid API, production call, Memory writeback,
formal submission, payment, public release or external contact is authorized.

## 1. Paper E Word Production Source

Use the current complete two-case manuscript as the sole content source. Do
not add P1/P2/new-family results to Paper E and do not create a second drifting
paper body.

Under `paper_e_word/`, prepare a directly convertible Word package:

- canonical Markdown or Pandoc-compatible source with the complete title,
  author placeholders, 150-250 word Purpose/Methods/Results/Conclusion
  abstract, 4-6 keywords, all sections, equations, 3 figures, editable tables,
  declarations and Data Availability;
- numeric bracket citations and a complete formatted 24-item reference list;
- `references.bib`, a numeric-bracket CSL, and a Word reference/style document
  if needed;
- a reproducible conversion command targeting local Pandoc 3.2.1;
- source and reference checks, conversion manifest and expected visual checks.

Use 10 pt Times New Roman as the intended body style where the reference DOCX
supports it. Keep author, affiliation, corresponding author, funding, patent,
AI disclosure approval and artifact fields marked `TBD_OWNER` where not
authorized. Remove ICAART-only boilerplate and raw BibTeX fields from the Word
content. Preserve real citations, publication status caveats and the two-case
claim boundary.

A does not need to run local Windows Pandoc. D will perform that conversion.
Your output must be sufficient for D to produce one DOCX and then transfer it
to GB10 for LibreOffice rendering.

## 2. Scoring V3 Paired Controls

Create `scoring_v3/`; do not overwrite `scoring_v2/`, V2 outputs or original
raw. Implement and test exactly these paired boundaries:

1. Equal numeric values in two rows:
   - a correct role-only citation is accepted when the reference independently
     identifies that role;
   - a wrong-role-only citation is rejected;
   - when the role reference cannot distinguish the rows, return PENDING;
   - do not require all equal-valued rows and do not search gold numeric values
     to fabricate role localization.
2. Required evidence support:
   - exact + exact can pass;
   - exact + broad cannot automatically pass the complete evidence contract;
   - each required operand/evidence item is judged separately;
   - broad support that cannot be role-bound remains PENDING.
3. Single-element numeric span:
   - when `answer` is a one-element list, `numeric_value` must agree with it;
   - a correct answer text with contradictory numeric value is rejected;
   - the legal positive and the `-999999` mutation are paired controls.

Each class needs at least one targeted positive and one targeted negative.
Synthetic/mutated controls are development tests, not natural error rates.
Reference roles must be derived independently from questions, rows, periods,
source annotations or reviewable reference chains; never from actor output.

Pure-rescore:

- the immutable first 40-call raw batch, selecting 36 final attempts;
- the saved oracle, blank-type and question-only actor outputs.

Report V2-to-V3 version differences by layer and UID. Keep `2/3/3`, `31/5`,
`12/19/5` and historical manifests unchanged. Distinguish semantic
equivalence, exact set completeness, unit/direction, evidence support, strict
format, UNKNOWN and PENDING.

## 3. Exposure Audit And Frozen New-Family Panel

Before any new output, build an exposure manifest from all relevant existing
artifacts: source split, training/development/confirmation/error-pool records,
prior UIDs, table/report families and this round's inspected questions. Record
hashes, date and whether historical pretraining exposure is auditable.

Select deterministically 8 previously unexposed natural table/document
families with one UID each. Preserve answer-type and task diversity; do not
select only known errors. If TAT-QA is used, label the result
`SAME_SOURCE_NEW_TABLE_FAMILIES`, not cross-source. Exclude every known
training, development, old confirmation, error-pool and inspected family. If
unexposed status cannot be established, stop model generation and report the
specific exclusion problem plus one obtainable alternative source.

Before model output, freeze:

- selected UIDs and family IDs;
- reference-side question, scale, direction, required evidence and accepted
  answers;
- the existing question-only typed baseline and shared calculator;
- Scoring V3;
- model/checkpoint/adapter/tokenizer/decode/output contract;
- D/T/M arm prompts, tools, budgets, metrics, predictions and stop rules.

Do not add question-keyword branches after seeing new outputs.

## 4. Three-Arm Mechanism Diagnostic

Use the same base model, checkpoint, tokenizer, decoding and output budget.
The actor sees only deployment-visible question/context. It must not receive
gold answer type, program, source requirement, correct row IDs, hidden units
or reference answers.

Run exactly three arms on the same eight UIDs:

- `D`: direct answer under the shared final JSON contract;
- `T`: ordinary typed evidence-to-program-to-calculator execution;
- `M`: T plus one frozen candidate mechanism, preferably explicit
  row/period/role/unit binding with validation before execution.

Public normalization and calculator capabilities must be shared where
applicable. If M retrieves more evidence or uses extra generation calls,
record every call and cost separately; no free extra context or reasoning.

Before model generation, run the frozen zero-model baseline on the new
families and report applicability/failure. Read only the 2-3 strongest nearest
works already available in project reading notes plus one counterexample, and
record the single mechanism difference being tested. Do not claim ordinary
program-aided reasoning or typed schemas are novel.

Report per UID and per family:

- complete delivery;
- correct repair, damage, strict failure, reasonable UNKNOWN, unnecessary
  refusal and PENDING;
- numeric correctness, formula correctness and visible citation support;
- direct/typed/binding mechanism differences;
- alternative explanations and total cost.

If T matches M, stop M. If M repairs corresponding natural failures without
only changing formatting or abstention, prepare a next-stage independent
confirmation card but do not run confirmation. If all arms fail, separate
model, reference and interface failures; do not train an adapter.

## 5. Persistent Budget And Generation

Connect the persistent budget guard to the actual local model loader before
generation. Use a new unique run ID and external append-only ledger:

`/home/testuser/wzh/research_runs/persistent_budget/word_new_family_20261027/ledger.jsonl`

Requirements:

- reservation before every real model call;
- token reservation equals actual tokenized input plus `max_new_tokens` upper
  bound;
- raw response and actual usage append/fync before scoring;
- generate/resume/rescore remain separate;
- crash, timeout, restart, output-directory changes and retries cannot reset
  totals;
- uncertain reservations remain consumed;
- no model load in rescore;
- attempt 37 and token-cap successors reject before loading.

Run no-model fault tests first. A real interface positive, if needed, consumes
reserve and must be reported.

Primary generation is 8 UID x 3 arms = 24 physical attempts. Reserve at most
12 attempts for preregistered interface positives, preserved failures or
bounded retries. Hard cap 36 physical attempts and 240,000 input+output
tokens. Training is zero. Every real generate call counts.

## 6. Completion Evidence

Write `A_RETURN.md` and structured JSON receipts. Include:

- Word source package and conversion command;
- Scoring V3 paired controls and V2/V3 rescore differences;
- exposure/freeze receipts and new-family source identity;
- zero-model baseline output;
- D/T/M raw responses and complete persistent-ledger accounting;
- nearest-work comparison and one counterexample;
- exact calls, tokens, retries, wall time, harness usage and unknowns;
- focused tests, JSON/hash validation and substantive Chinese thesis updates;
- a commit containing only owned paths.

D will convert/render the Word draft before C review. Do not claim DOCX/PDF
visual acceptance or C acceptance in A_RETURN.
