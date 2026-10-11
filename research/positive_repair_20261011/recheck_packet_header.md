# Loop C Pre-Result Design RE-AUDIT — Track P First-Wave Preregs v2 (single budgeted re-audit)

You are the independent Loop C auditor. This is the ONE budgeted re-audit after revision 1 (user rule). Read-only, packet-only, report-only. No tools, no file reads, no network, no edits.

## Context and consequence
- Audit v1 (2026-10-11) returned CONDITIONAL for all four experiments: none FAIL, all SCOPE_CHANGE: NO. Loop D then applied ONE batched revision of prereg / implementation-contract text only (v2 files below) plus two shared contracts.
- This re-audit is final. PASS -> execution is authorized for that experiment (Loop D auto-dispatches; no further user approval). CONDITIONAL at this stage is treated as final non-PASS -> STOP_BRANCH (no further revision is authorized). FAIL -> STOP_BRANCH. Scientific scope must NOT change.
- If a residual issue does not undermine executability/interpretability, you may note it as non-blocking under PASS. If it does undermine, mark FAIL and state why.

## Audit-v1 condition closure map (claimed; verify against the v2 texts)

### PR-EXP-03
- (a) no-op + specificity arms + FP side -> v2 section 4 Arms A0/A1 (must return 0), section 5 secondary (A0/A1 false-positive counts), section 7 POSITIVE requires A0/A1 pass; constant-1 documented control.
- (b) attribution operationalization -> contracts/SOURCE_LOCAL_RESPONSE_v1.md per-experiment test; v2 section 5 attribution-pass definition (unique catches + A0/A1 clean + constant-1 documented failure).
- (c) complete outcome taxonomy + sanity-gate definition -> v2 section 7 (POSITIVE / DIAG_ONLY / NULL / NEGATIVE / INVALID / NOT_EVALUABLE; sanity gate defined; NOT_EVALUABLE never merged into NULL).
- (d) freeze verbatim rules/hashes -> v2 section 3 (selection rule verbatim + exclusion registry + extraction command), section 4 (baseline verbatim extract + hashes), section 8 implementation-contract requirement.
- (e) cost tolerance + P1 ground-truth labels -> v2 section 6 exact-equality check-count tolerance; section 3 ground truth (stage "M", family "topology_transposition"); section 5 mixed-population diagnosability definition + LOCO groups.

### PR-EXP-01
- (a) surfaces + non-identity-on-scored / hash-identity-on-truth + NOT_EVALUABLE fallback -> v2 section 2.
- (b) threshold rule incl. ties/strictness -> v2 section 4.
- (c) checker independence + panel completeness -> v2 section 2.
- (d) empirical clean-row bridge report -> v2 section 7.
- (e) single canonical outcome label -> v2 section 6.

### PR-EXP-04
- (a) cost section -> v2 section 6.
- (b) symmetric gate / attrition -> v2 section 3 (N1 descriptive attrition reported; N2 gate; declarations).
- (c) numeric directional taxonomy -> v2 section 7 (margin m=0.05; SUPPORTED / NULL fingerprint-bound / NEGATIVE / NOT_EVALUABLE with insufficient-groups clause).
- (d) harness confound control -> v2 section 4 harness-equivalence control (mandatory; failure = INVALID); conclusion bound to the shared generation harness; confound recorded.
- (e) numeric baselines + group definition + contamination declaration -> v2 section 5 (frozen numbers), section 3 (group definition; N1-development contamination declared).

### PR-EXP-07
- (a) NOT_EVALUABLE + attrition rule -> v2 section 3 taxonomy + section 5 attrition table.
- (b) label provenance + pairing-rule certification -> v2 section 1 (injection-design labels; pairing rule built from frozen structure; certification note).
- (c) population/fold pinned by hash + freeze timing -> v2 section 2 (population pinned; folds referenced by hash) + section 1 (freeze before feature-value observation).
- (d) numeric "clearly above" + taxonomy completeness -> v2 section 3 (0.05 margins; NULL_DIRECT_CONCENTRATED; NULL_AT_CHANCE).
- (e) quantified blind-vs-original delta + robust binding -> v2 section 5 (delta on identical rows) + section 3 (robust criteria).

### Global closures
- SOURCE_LOCAL_RESPONSE defined with per-experiment operational tests (see contract).
- Shared-surface ordering: contracts/shared_surface_freeze_v1.json pins runner / carriers / manifest / canonicalizer hashes; no edits after observation; GB10-only inputs noted for execution-time pinning.
- Anti-cherry-picking: failures retained; NOT_EVALUABLE never merged into NULL; PR-07 compliance fixed; PR-01 labels canonicalized.

## Audit questions (answer ALL 10 per experiment; one line each)
1. Is any improvement guaranteed by definition (or achievable only via definitional construction)?
2. Does the design change observability rather than labels / task truth?
3. Is the held-out set independent and correctly partitioned (leakage, UID overlap, freeze order)?
4. Are baselines fair and complete for this experiment type?
5. Is cost accounted fairly; is a same-budget comparison possible?
6. Can a source-local-only gain be ruled out (or is source-locality handled in the right direction)?
7. Are before/after measurement objects comparable, with non-comparabilities correctly declared?
8. Is NULL / NOT_EVALUABLE informative and correctly separated?
9. Does anything change the scientific scope relative to the human-approved prompt? (also set SCOPE_CHANGE)
10. Are any mandatory conditions still missing? (list precisely)

## Required output format (machine-parseable)
## PR-EXP-03
- Q1..Q10 lines
- VERDICT: PASS | CONDITIONAL | FAIL
- SCOPE_CHANGE: NO | YES (<desc>)
- RESIDUAL_NOTES: (optional; non-blocking)
- BLOCKING_REASON: (only if FAIL or if CONDITIONAL would stop the branch)
(repeat for PR-EXP-01, PR-EXP-04, PR-EXP-07)
## GLOBAL
- <notes>
End with the literal line: RE-AUDIT_COMPLETE

--- BEGIN PR-EXP-03 prereg v2 ---