ROLE: Loop C / GB10 read-only scientific result autopsy
MODE: inquiry-methods fact-check
QUESTION:
Why did the frozen FinQA v3 run produce V=89/89 and D=0/89 in the V1D0 cell, and what scientific interpretation is supported?

INPUTS:
- `research/finqa_v2_20261010/build_finqa_v2_execution_freeze.py`
- `research/stage_e_multileaf_20261010/build_finqa_v2_candidate_manifest.py`
- `research/finqa_independent_observation_scorer_v2.py`
- `research/finqa_v2_20261010/FINQA_V2_ANALYSIS_PLAN.md`
- `research/finqa_v2_20261010/results_binding_v3_rerun/finqa_v2_formal_sample_rows.jsonl`
- `research/finqa_v2_20261010/results_binding_v3_rerun/FINQA_V2_FORMAL_RESULT_REPORT.md`
- existing scorer/freeze tests and the independent v3 recomputation audit.

REQUIRED FACT CHECK:
1. Derive the exact V and D predicates from source.
2. Trace E/P/N mutation operations to the scorer fields they necessarily change.
3. Determine whether `res` or terminal `answer` is recomputed after mutation.
4. Separate evaluation-split selection from injection-construction selection.
5. Inventory unchanged/sham/irrelevant/positive/negative controls already present.
6. Test explanations:
   A substantive protocol blindness;
   B visibility-by-construction;
   C detection-object mismatch;
   D injection-selection bias;
   E scorer-definition tautology;
   F legitimate construct separation.
7. Choose exactly one final class:
   STRONG_CONSTRUCT_SEPARATION;
   CONSTRUCT_SEPARATION_WITH_DESIGN_DEPENDENCE;
   MEASUREMENT_OBJECT_MISMATCH;
   INVALID.
8. Audit the proposed claim and recommend KEEP/DOWNGRADE/REWRITE/REMOVE plus a safer sentence.
9. Decide whether a non-degenerate experiment is required only for a stronger claim, and name the single gap.

FORBIDDEN:
- Modify artifacts.
- Add controls or run new experiments.
- Treat V=1/D=0 as protocol blindness without a causal path.
- Infer semantic correctness.

OUTPUT:
Return a read-only report with FACT/INFERENCE/UNVERIFIED labels, exact source lines, final classification, claim action, and strongest counterargument.
