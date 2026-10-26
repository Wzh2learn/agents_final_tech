# Loop A Task: Publication And Proxy Calibration

Task ID: `publication-proxy-calibration-a-20261026`
Date: 2026-10-26, Asia/Shanghai
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `a38252322189ccb00a1a45b7611f693ada292faf`
Authority LF SHA256: `9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974`

## Scope

Execute one bounded implementation task on GB10. Other loops may work in the
same repository; do not revert or overwrite unrelated changes. Do not restart
old R/E, do not train, and do not touch production services, databases,
credentials, or frozen evidence.

Create and own:

- `research/publication_proxy_calibration_20261026_v1/paper_e_sncs/`
- `research/publication_proxy_calibration_20261026_v1/p1_rule_execution/`
- `research/publication_proxy_calibration_20261026_v1/p2_proxy_calibration/`
- `research/publication_proxy_calibration_20261026_v1/raw/`
- `research/publication_proxy_calibration_20261026_v1/receipts/`
- `research/publication_proxy_calibration_20261026_v1/A_RETURN.md`
- `research/feedback_learning_phase_b_20261026_v1/thesis_draft/CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md`
- `research/feedback_learning_phase_b_20261026_v1/thesis_draft/EVIDENCE_TABLE.md`

You may add focused tests and scripts below the new research directory. Do not
edit `memory/STATE.md`, `memory/THREADS.md`, the unique research prompt, frozen
raw outputs, old score files, or audit-owned files.

## G1: Paper E Journal-Derived Package

Derive the existing two-case Paper E manuscript into a real SN Computer
Science submission package. Keep the two-case scope and preserve the original
ICAART package unchanged.

Required outputs in `paper_e_sncs/`:

- editable LaTeX and BibTeX;
- compiled PDF;
- figure sources already used by Paper E;
- 150-250 word Purpose/Methods/Results/Conclusion structured abstract;
- Methods-level disclosure of actual AI use;
- cover letter draft, declarations, data/artifact availability statement,
  author/affiliation/corresponding fields marked `TBD_OWNER`;
- one-page owner decision sheet with a single primary recommendation;
- package manifest and hashes.

Perform one substantive first-reviewer pass on contribution boundary, closest
work, post-hoc/clustered analysis identity, what the two cases changed, and
what remains unexplained. Do not add C2/C3 experiments or claim acceptance,
publication, or school recognition. Formal submission, signature, payment,
identity commitment, and public release remain owner actions.

## G2: Public Rule Actor And Full 24-Question Regression

Locate the frozen 24 ordinary original questions and the six ordered visible
rules in `P1_SEMANTIC_LEDGER_FINAL.json`. Implement one deterministic public
actor under `p1_rule_execution/`.

Actor visibility is limited to the question, complete visible table, and
visible headers/axes. It must not read gold answers, gold programs, evidence
row IDs, UID-specific branches, hidden unit scales, or manually edited
per-case values. The rules remain frozen: completeness, explicit period
binding, later-minus-earlier for unlabeled change, inclusive range, named
row/section scope, and numeric/unit validation with explicit UNKNOWN when
direction or unit is not legally observable.

Run all 24 ordinary originals, not only the five failures. Preserve the
original numeric scorer and separately report:

- 4 genuine model-error repairs;
- the 1 direction-reference conflict;
- damage to the 19 previously numeric-correct items;
- unmatched, ambiguous, UNKNOWN, unit, direction, and citation outcomes;
- executableability and test results;
- any failure caused by missing input or tooling versus semantic residual.

This is an exposed development regression, not new-source generalization.
Do not weaken tests or branch on task IDs to force expected values.

## G3: Real Answer/Cost Calibration

Before any new model output:

1. Preserve the old P2 matcher and fix the future evaluation path for R7 and
   R8. R7 must implement only the declared digit-adjacent thousands-separator
   normalization. R8 must reject negative integers for count answers. Add
   regression tests including the two known substring/role counterexamples.
2. Build a reviewable `question -> table/paragraph -> role/unit -> program/
   answer` reference chain. Record AI review identity; do not call it human
   gold or a complete semantic oracle.
3. With a fixed seed and frozen stratification rule, select at most 12 natural
   development UIDs before viewing model outputs, covering proxy-disagreement
   and proxy-agreement cases across source need and task type. Preserve the
   original 507-item denominator, exclusions, reasons, and replacement list.
4. Run the formal preflight in
   `docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`, including the actual
   model load path, source hashes, runner-to-adapter-to-scorer dry run, and a
   generation-stop receipt. Qualification failure must stop generation and
   produce a concrete failure chain.

If qualified, compare exactly three visible-context arms with one fixed actor,
prompt/output contract, calculator, decoding configuration, and context limit:

- table + top-3;
- table + top-5;
- table + all.

Default to 12 items x 3 arms = 36 scientific generation calls. At most 12
additional calls are allowed only for frozen interface positives, preserved
failures/retries, or preregistered supplements. Total hard cap: 48 generation
calls and 240,000 generation tokens. Training is zero. All calls, retries,
failures, and interface checks count.

For every raw response record the full answer, unit, direction, required
support, strict-format failure, reasonable UNKNOWN, error delivery, actual
non-padding input/output tokens, wall time, and call identity. Keep source
proxy counts, annotated recall, and visible characters separate from semantic
answer accuracy and measured cost. Do not claim a 2-point equivalence or
generalization from this small development panel.

## Scientific Disposition

Finish with a direct decision:

- proxy unreliable or actor/interface limited;
- full context accurate and cheaper, restricted context harmful;
- paired semantic improvement or a risk-cost tradeoff worth another stage;
- no information value and stop this candidate.

Explain the strongest simple baseline, what alternative explanations remain,
and what next experiment would change the decision. Negative and unresolved
results are valid.

## Completion Evidence

Return:

- actual files and hashes;
- exact commands and exit status;
- P1 full 24-row output and focused tests;
- P2 selection/reference/preflight receipts;
- raw model outputs and complete cost ledger if generation ran;
- zero training evidence;
- A usage separated into input, cache, output, and reasoning tokens where
  available;
- one substantive Chinese thesis paragraph and evidence-table update;
- commit hash containing only owned paths.

Do not edit global state ledgers. Do not claim C acceptance before the
independent C task exists.
