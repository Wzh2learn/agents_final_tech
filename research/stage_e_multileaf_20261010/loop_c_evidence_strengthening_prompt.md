ROLE: Loop C / GB10 independent review
RESEARCH QUESTION:
Are the Paper E evidence-strengthening artifacts scientifically identified, independent, and correctly scoped without relying on the same M/R/N direct-codebook significance?

INDEPENDENCE ORDER:
1. Read raw result artifacts and source manifests first.
2. Independently recompute the key counts/claims.
3. Only then read Loop D and Loop A conclusion documents.
4. State any prior-conclusion ingestion in an independence declaration.

INPUTS:
- Frozen multi-leaf results and ablation artifacts under research/stage_e_multileaf_20261010/results.
- multileaf_mechanism_generalization_audit.json and its Markdown report.
- finqa_v2_causal_join_audit.json and finqa_v2_candidate_sample_manifest.json.
- research/finqa_independent_observation_scorer_v2.py and its tests.
- research/finqa_evidence_argument_resolver_v2.py and its tests.
- Loop D drafts and Loop A execution outputs under research/stage_e_multileaf_20261010/.
- PRM formal-pilot proposal and source qualification artifacts.

ALLOWED ACTIONS:
- Read-only inspection and independent arithmetic/statistical recomputation.
- Run existing unit tests or deterministic validators where needed for independent verification.
- Verify source hashes, sample counts, gate statuses, evidence classes and figure source values.
- Write a fresh-context audit report only.

FORBIDDEN ACTIONS:
- Modify source artifacts, paper text, contracts, thresholds or sample manifests.
- Run formal FinQA or PRM training.
- Re-run the M/R/N experiment to manufacture new significance.
- Treat the independent observation scorer as semantic correctness evidence.
- Accept a claim without citing raw artifact fields or exact commands.

OUTPUT:
- A fresh-context audit report in docs/experiments/2026-10-10_loop_c_evidence_strengthening_audit.md.
- Evidence table for claim boundary, mechanism generalization, FinQA gates, scorer independence, PRM readiness, Figure 3 and paper contributions.
- Findings ordered by severity.
- `VERDICT: ACCEPTED`, `CONDITIONAL`, or `REJECTED`.
- A short list of the strongest remaining reviewer attacks.

EVIDENCE CLASS:
PRIMARY: claim-boundary and identifiability.
SECONDARY: gate status, power/resource contract and figure mapping.
EXPLORATORY: mechanism feasibility and visual candidates.
ENGINEERING: independent scorer/resolver implementation.
NEGATIVE: non-identifiable generalization or blocked formal pilot.
