# Structured abstract (211 words)

**Purpose.** We audit whether reported evaluation scores distinguish observed defects from silent absorption and whether evidence-ranking conclusions survive implementation choices.

**Methods.** We retain the original two-case scope: a frozen staged document evaluator with controlled header perturbations, instrumentation and a nested FinQA measurement-object probe; and FinRank, a public provenance-sensitive evidence-ranking benchmark. We inspect visibility, detection, harmfulness, score algebra, tie policy, identity construction, and reproduction.

**Results.** In the staged case, 96/118 header injections are visible, the OCR-like family is unobserved on the frozen surface (0/13), and flat versus layered scores are affine/rank-equivalent. Explicit instrumentation explains stage separation, while clean-only calibration does not identify a deployment threshold. In FinRank, tie policy changes absolute metrics but preserves the hard-versus-random direction; a post-hoc text-sha1 correction finds 442 overlapping hard-negative occurrences across 305 records and gold loss in 33 records. In-record and pairwise values reproduce exactly, but global and metadata-filtered drift remains unexplained.

**Conclusion.** The two cases support a bounded review discipline: bind observations to measurement objects, separate score sensitivity from decision stability, preserve identity contracts, and report unresolved reproduction gaps. We do not claim a universal causal theory, formal acceptance, or generalization beyond these cases.
