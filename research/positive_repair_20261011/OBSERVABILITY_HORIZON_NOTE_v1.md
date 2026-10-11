# OBSERVABILITY_HORIZON_NOTE_v1.md

> date: 2026-10-11 | status: CANDIDATE_FRAMING (not a validated theory) | adopts Gemini-B's "Observability Horizons" ONLY as organizing language
> Rule: no new claim may enter through this framing; it must be explainable by existing frozen FACTs, and anything else is listed as analogy/inference.

## A. Frozen FACTs the framing can organize (mapping only)
1. **Stage E blind families (FACT).** Family-level observation boundary exists: OCR-like 0/13 injections unobserved across 11 clusters at every tested threshold; family visibility ranges 0.81-1.00; the frozen absorption definition is canonical-mapping preservation. Framing sentence: "for this observation surface, the absorbed family lies outside the surface's observation boundary." No new quantity claimed.
2. **Single-responsive-leaf affine/rank equivalence (FACT).** Flat and layered contrastive scores are a positive affine/rank transform in the current construction (slope 0.375 identity; Spearman 1.0), and the clean-only matched-FPR operating point is not identifiable. Framing: both protocols observe the same boundary, so the frozen evidence cannot rank them at matched FPR - it reports non-identifiability, not equality.
3. **Multi-leaf direct/non-direct ablation (FACT, construction-bounded).** Full vector and the direct three-leaf codebook both reach macro-F1 1.0; non-direct-only falls to 0.3333 (three-class chance), tie rate 0.6667; 8 of 12 leaf columns are identically zero. Framing: within a construction, what lies inside the observation boundary is set by explicit instrumentation, not by hierarchical organisation.
4. **FinQA second dataflow (FACT for the construction).** V=89/89, D=0/89, O=0/89 with D-fields a subset of V-fields and un-recomputed referents. Framing: the detection predicate's boundary does not include the perturbed object - a measurement-object mismatch, not protocol blindness.

## B. Analogy / inference only (NO experimental support; MUST NOT appear as facts)
- "distance decay" between fault stage and checkpoint (no distance definition, no propagation records; see PR-02_feasibility_factcheck_v1.md).
- "strict horizon" as a theorem (the boundary is demonstrated only per construction, never as a universal limit).
- "silent absorption law" (22/118 checkpoint-blind cases are documented; no law relating absorption to downstream behaviour).
- "dilution law" (aggregation dilution is observed once, in one construction).
- cross-system / modular-dataflow generality (one frozen corpus + one failed second flow; explicit limitation).

## C. Permitted use
One Discussion paragraph of organizing language, claim-free, e.g.:
> "The four frozen results can be read through a single lens: an evaluation's observation surface has a boundary set by its instrumentation and canonicalisation, and validity claims must be audited against that boundary per dataflow - what the surface cannot observe is invisible to its detectors, and what its detectors do not share with the perturbation is not measured."
This adds vocabulary, not claims; it repeats the frozen thesis. Do NOT attach quantitative horizon claims, "laws", or implied new experiments.

## D. Recommendation
Adopt as Discussion framing ONLY if it reduces repetition without adding claims; otherwise keep in this note. Decision is the owner's; no paper-body edit is made by this note.