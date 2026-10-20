# Intended Use and Use Restrictions

## Intended uses

- Scientific evaluation of counterfactual requirement-and-evidence reasoning.
- Comparison of explicit-rule, direct LLM, RAG, paired-learning, and structured multi-task methods.
- Study of selective decisions, abstention, localization, rationale grounding, and oracle disagreement.
- Reproducible requirements-engineering and benchmark-governance research.

## Required evaluation practice

- Preserve the supplied family-level partitions.
- Do not split derived records from one base/family across train and test.
- Report relation and handling separately.
- Report oracle-disagreement strata and parse failures.
- State that O3 is simulator-only shadow evidence.

## Prohibited or unsupported uses

- Live command, targeting, weapon control, or operational authorization.
- Claims of certified autonomy, certified physics, deployment readiness, or real-world safety.
- Re-identification of reviewers or linkage to controlled provenance.
- Training/test contamination by ignoring family and split-group boundaries.
