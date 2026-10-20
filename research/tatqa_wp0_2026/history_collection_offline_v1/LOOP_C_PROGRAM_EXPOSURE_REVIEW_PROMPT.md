# Loop C independent program-reference exposure review

Task id: `history-program-exposure-review-20261018-r1`
Role: Loop C independent reviewer.
Mode: bounded read-only evidence audit over the 165 proposed future/development/reserve source clusters.

This review must use real file evidence and shell commands before making any claim. Do not trust the task description, prior return text, commit messages, or another review's conclusion as proof. Do not modify reviewed artifacts, raw data, old WP-2 files, frozen materials, scores, or prior review reports. Do not start a service, collect data, run a scientific model, train, pilot, write memory, authorize collection, switch source, or release data. This AI review is not human semantic gold.

## Decision object

`EXPOSURE_AND_SPLIT_AUDIT.json` currently contains:

- 165 clusters in `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` with at least two contract-valid tasks;
- proposed deterministic groups: 8 future, 2 development, 155 reserve;
- 170 UIDs classified as `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` in total;
- a 233-UID non-structural exposure register with canonical hash
  `d6c37842dd6ebb1f8d512ca0ad3f0f94a1a6ba5e39c8fbeefe4b16c710724070`.

First recompute these counts from JSON. If they differ, stop and report the mismatch instead of silently using the figures above.

## Evidence standard

Assign every reviewed UID/cluster to exactly one category:

| Category | Required evidence | Future-test consequence |
|---|---|---|
| `STRUCTURAL_SCAN_ONLY` | scripts plus bounded input/output/log evidence showing only ID registration, structure scanning, or deterministic qualification | may remain eligible for a developmental test; not automatically excluded |
| `PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE` | positive data-flow evidence that generated task/reference output was produced by a bounded deterministic process and did not enter designer, actor, feedback, correction, or effect-analysis context | may remain eligible after review |
| `METHOD_DEVELOPMENT_OR_DIAGNOSTIC` | content entered human/AI diagnosis, prompt design, rule design, or related method-development context | exclude from new test |
| `MODEL_OR_FEEDBACK_EXPOSURE` | content entered an actor request, response, feedback, correction attempt, or effect analysis | exclude from new test |
| `EXPOSURE_UNKNOWN` | evidence is absent, ambiguous, internally inconsistent, or only inferred from lack of logs | exclude until resolved |

Important corrections:

1. Membership in a TQ-5 exclusion list is not execution or exposure evidence.
2. Deterministic program processing is not model exposure.
3. Absence of a log is not positive evidence of no exposure.
4. Program-generated output that was visible to designers or used to choose, debug, prompt, score, or interpret methods is not a clean future-test source.
5. A raw UID need not appear literally in a prompt if deterministic content mapping establishes that its content entered the prompt.
6. Do not treat independent human gold as required for this exposure audit. This review only qualifies access/exposure evidence and task-contract eligibility.

## Required evidence work

Use shell commands first and record the commands or mechanical checks in the report. At minimum:

1. Enumerate all 165 eligible pending-review cluster IDs and their UIDs, task counts, and proposed split membership from `EXPOSURE_AND_SPLIT_AUDIT.json` and `SPLIT_PROPOSAL.json`.
2. Trace how `PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW` is assigned in `exposure_classifier.py` and `build_exposure_and_split_audit.py`.
3. Inspect the pinned candidate task/reference source and its generating or consuming scripts. Establish which artifacts contain generated tasks/references and which later workflows read them.
4. Search bounded project evidence for those content identities in TQ-4, TQ-5, WP2, prompt/debug/design artifacts, actor requests/responses, feedback, correction, and effect-analysis records.
5. Distinguish literal UID references from deterministic content mappings and opaque-ID mappings.
6. Check the proposed 8 future clusters first, then development and reserve. Report per-cluster evidence, not only aggregate counts.
7. Verify every cluster still has at least two contract-valid tasks and that future, development, history, and reserve groups are disjoint.

Do not expand into SEC EDGAR, MultiHiertt, public web search, or unrelated repository audits.

## Output

Write exactly one new report:

`research/tatqa_wp0_2026/history_collection_offline_v1/LOOP_C_PROGRAM_EXPOSURE_REVIEW.md`

Return one verdict:

- `FUTURE_POOL_QUALIFIED`: at least 8 disjoint proposed future clusters are positively supported as non-exposed and contract-valid;
- `CONDITIONAL`: some clusters are supportable but the evidence or required count remains incomplete;
- `INSUFFICIENT_EVIDENCE`: the available evidence cannot positively qualify any future pool.

The report must include:

1. recomputed source and split counts;
2. a complete table of all 165 clusters, or a complete machine-readable-style appendix listing every cluster/UID with category and evidence path;
3. special findings for the 8 proposed future clusters;
4. excluded clusters and exact reasons;
5. commands/checks actually run and any checks not run;
6. a conservative qualified future count after applying `EXPOSURE_UNKNOWN`;
7. whether at least 8 clusters survive;
8. unresolved provenance or report-identity limits;
9. explicit statement that this is AI evidence review, not human semantic gold;
10. explicit statement that online collection remains not authorized by this review.

Do not create a second summary file. Do not revise `OFFLINE_RETURN.md`, the hash bundle, split proposal, or implementation in this review. If write access is denied, return the complete report in the task output for Loop D to transcribe.
