# Stage E Multi-Leaf v2 Robustness Preregistration Delta v1

> Status: `DESIGN_ONLY_NEW_NAMESPACE_REQUIRED` | Applies only to a future second-dataflow/non-degenerate run | Does not alter or rerun the v1 confirmatory result

## 1. Why a new namespace is required

The v1 result is internally valid but construct-sensitive. Post-hoc ablation shows that the fixed three-direct-leaf codebook alone achieves the same perfect macro-F1 as the full response vector. Loop C therefore identified a surviving reviewer attack:

> The evaluator writes a stage-specific response codebook from contract/gold predicates, so the classifier decodes the injection label rather than a general production visibility trace.

A future experiment must answer a stricter question:

> Can stage be predicted from raw checkpoint dynamics when features are extracted without access to stage labels and when stage signatures overlap?

## 2. Required design corrections

1. **Label-blind feature extraction.** The extractor receives only paired raw pipeline/checkpoint outputs. It cannot read `expected_first_affected_stage`, mutation type, sample ID namespace, stage-specific generation code or gold labels.
2. **Non-degenerate signatures.** Include at least one shared responsive leaf across two stages and at least one pair of stage classes with overlapping/non-identical response support. Constant one-hot codebooks are invalid for this v2 claim.
3. **Separate source/provenance audit.** Verify no table/document/report/task origin crosses roles, including semantic provenance aliases that literal ID comparison would miss.
4. **Fixed replicate counts.** The runner must hard-fail if `permutations != 10000` or `bootstraps != 10000`; CLI overrides are not allowed after freeze.
5. **Two-sided permutation definition.** For macro-F1 statistic `T`, freeze
   `p = min(1, 2 * min(P(T_null >= T_obs), P(T_null <= T_obs)))`.
   Store the full null distribution and both tail counts.
6. **Contract tests.** Unit tests must cover M/R feature construction, missing evidence, zero-vector class behavior, ties and direct-codebook negative controls.
7. **Ablation as preregistered secondary.** Report full vector, direct-only, non-direct-only and leave-one-leaf-out results. Full vector must add information over any simple contract codebook before a general localization claim is considered.
8. **Independent scorer requirement.** At least one non-trivial checkpoint must be reproduced by an implementation that does not share the injection generator or primary scorer code.

## 3. Candidate measurement surface

Best current candidate: `FINQA_PROCESS_CHECKPOINT_V2_NAMESPACE`.

Candidate stages:

- `E`: evidence grounding / required source availability;
- `P`: program operator/argument execution;
- `N`: numeric consistency / final outcome.

Candidate fault families must be fixed before outcomes and must create overlapping signatures, for example evidence removal, operator mutation, operand/reference mutation and cross-stage propagation. Exact sample IDs, gold and expected-first-stage are `NOT YET DEFINED` and require a separate preregistration before execution.

## 4. Primary metrics and claim gate

Primary metrics remain:

- leave-one-cluster-out macro-F1;
- top-1 stage accuracy;
- comparison to majority/chance and direct-codebook ablations.

A general stage-localizing claim is allowed only if:

1. label-blind full-vector macro-F1 exceeds the strongest codebook/non-localization baseline;
2. two-sided permutation p `< 0.05`;
3. cluster-bootstrap lower bound clears the baseline;
4. signature overlap is present and leakage audit passes;
5. at least one independent scorer reproduces a non-trivial checkpoint.

If full vector is no better than the direct codebook, report `NULL` for incremental localization information even if raw accuracy is high.

## 5. Explicitly forbidden

- rerunning v1 with a changed threshold/predictor and calling it confirmatory;
- feeding stage labels or mutation family into the feature extractor;
- removing ambiguous samples to improve separability;
- treating one-hot constant signatures as general localization evidence;
- changing the two-sided p-value rule after results;
- claiming hierarchy localization unless a hierarchy-derived predictor is separately validated.

`DECIDE NEXT LOOP: CONTINUE` only to prepare the FinQA v2 preregistration if licence, split and raw checkpoint adapter gates can be made explicit. No v2 experiment is authorized by this delta.
