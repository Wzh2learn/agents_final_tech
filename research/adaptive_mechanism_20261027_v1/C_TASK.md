# Loop C Fixed-Snapshot Joint Review

Task ID: `adaptive-mechanism-c-20261027`
Date: 2026-10-27, Asia/Shanghai
A snapshot: `276c858839ecbd9c190b8067552c683372efc193`
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `17f6895e3f2734f5e597f1a1d7853af22ae2adf4`
Authority LF SHA256: `73da0c8a44512c4b47d677efa3a7c71b45fb7d15e582a77737c27c284f800d12`

## Ownership And Boundary

Perform exactly one independent joint review of the fixed A snapshot. Own
only:

- `research/adaptive_mechanism_20261027_v1/audits/C_JOINT_AUDIT.md`
- `research/adaptive_mechanism_20261027_v1/audits/TASK_RESULT_C.json`
- focused recomputation/audit scripts and fixtures below the same `audits/`
  directory.

Do not modify A source, raw, scoring labels, manuscripts, manifests, thesis
text, external budget ledger, memory or the unique prompt. Do not generate
model answers, train, call judges, probe production or use external services.
Other loops may work in the repository; do not revert unrelated changes.

## Review Scope

### Paper E Formal Build

Independently inspect `paper_e_formal_build/`:

- Is the source bundle actually buildable in a normal TeX environment?
- Are TeX, BibTeX, bibliography style, figures, commands and dependencies
  complete or explicitly obtainable?
- Is `BUILD_BLOCKED` supported by the exact tool search and failed command?
- Are source checks substantive: two cases, full sections, 24 citations,
  formulas/tables/figures, cross-references and final-page content?
- Does the first-reviewer pass cover contribution/nearest-work separation,
  two-case interpretation changes, clustered/post-hoc identity and claim
  boundaries?

Do not accept the historical fallback PDF as a formal build.

### Scoring V2 And Zero-Model Rescore

Replay the scoring tests and rescore from immutable first-batch raw without
loading a model. Check:

- all positive and adversarial controls, not only the old defects;
- separate strict, answer, numeric/unit/direction, evidence and final-delivery
  layers;
- `PENDING_ADJUDICATION`, `STRICT_FAIL`, `REASONABLE_UNKNOWN` remain distinct;
- string/dict/list program reference reconstruction and visible paragraph
  mapping;
- exact 12 UID x 3 arm final-attempt selection;
- corrected input deltas 917 and 1604;
- historical `2/3/3` remains visible and is not overwritten.

Look for over-strict rejection, hidden gold use, wrong-role acceptance, extra
span acceptance, missing/nonexistent reference acceptance and unit/scale
conflicts.

### Persistent Budget

Inspect the external append-only ledger and repository implementation.
Independently run the no-model fault suite or equivalent focused commands.
Verify:

- reservation before call, immediate raw append and conservative uncertain
  consumption;
- separate generate/resume/rescore;
- crash, scoring exception and output-directory change cannot reset totals;
- attempt 37 and token-cap successor reject before model load;
- the main ledger hash is stable and actual generation remains zero.

### Visible Typed Baseline And Mechanism Stop

This is the central scientific review. Determine whether the reported
`31 ACCEPT + 5 REASONABLE_UNKNOWN` is genuinely supported by deployed visible
information.

Specifically inspect:

- whether `answer_type` is deployment-visible in the original task contract,
  or an answer/reference-derived oracle feature;
- whether the actor or selector uses expected refs, gold answers, expected
  programs, hidden units, UID branches or reference reconstruction before
  producing its answer;
- whether the mean and count signals are solved by a transparent typed
  reduction rather than copied expected values;
- whether `REASONABLE_UNKNOWN` is justified by absent visible evidence, not
  used to hide errors;
- whether the baseline is shared fairly and would remain valid without
  `answer_type`;
- whether 31/36 and 5/36 recompute from the rows and source contexts.

If `answer_type` is not deployment-visible, require an answer-type-free
ablation or classify the baseline as oracle-assisted. Do not let a strong
zero-model baseline conceal hidden reference access. Decide whether
`STOP_BEFORE_GENERATION` remains valid, becomes conditional, or must be
reopened with a specific bounded test.

## Required Judgment

Return one verdict:

- `ACCEPTED`;
- `CONDITIONAL`;
- `REJECTED`.

Separate blocking defects from limitations. For each finding provide exact
path/line or artifact, evidence, impact and smallest follow-up. Include:

- independent hashes and counts;
- actual commands and exit status;
- Paper E build readiness;
- scoring V2 validity;
- budget guard validity;
- visible-baseline information boundary;
- generation/training/judge/production totals;
- whether any new physical generation is justified.

Independent AI review is AI review, not human gold, venue acceptance or
school recognition.
