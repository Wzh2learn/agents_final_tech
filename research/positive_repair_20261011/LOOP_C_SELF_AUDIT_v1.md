# LOOP_C_SELF_AUDIT_v1.md

> date: 2026-10-12 | performed by: Loop D (self-audit) | independence status: NOT independent
> Why self: three attempts to obtain a fresh-context Loop C auditor failed in this session. A pre-result auditor and a provenance verifier returned nothing, and the dispatched full-audit agent ran for ~55 minutes with no output and was interrupted. The user then authorised Loop D to perform the Loop C content directly. This document is therefore a rigorous self-audit, not an independent verdict, and is labelled as such.

## Audit A - PR-03 v3 result and branch closure

A1. Does NEGATIVE follow from the frozen rule and the point estimates? **FACT, yes.**
Evidence: `point_diagnostic_output.txt` shows gate_pass=true, undefined=0, diag_delta_min=-0.1952, delta=0.8116 with delta_ci_lower=0.7960. The outcome rule in `experiment_v3.py` is ordered: INVALID -> NOT_EVALUABLE -> `elif diag_delta < -0.02: NEGATIVE` -> POSITIVE -> DIAG_ONLY -> NULL (lines 603-613). With the gate passing and no undefined cells, -0.1952 < -0.02 selects NEGATIVE before any positive branch is reachable.

A2. Is "the frozen v2 implementation is non-executable as delivered" verifiable from the file alone? **FACT, yes.**
Evidence (this re-verification, mechanical): Python's `symtable` reports that inside `evaluate()` of `experiment_v2_reference.py` the name `a1_table` is a **local, assigned, non-global** symbol, while a module-level function `a1_table` also exists. Line 480 reads exactly `a1_table = a1_table(row["baseline"], uid)`, so the right-hand call resolves to the unbound local and raises `UnboundLocalError`. This does not depend on any external artifact.

A3. Is the frozen diagnostic bootstrap computationally infeasible? **FACT, yes (this re-verification, measured).**
Evidence: one `classification()` call over 2503 singleton groups (the real mixed-population shape) took **3.63 s**. The frozen `diag_bootstrap` invokes `classification` 2 (features) x 10,000 (replicates) x 2 (label keys) = **40,000** times, extrapolating to **~40.3 hours**. The round-1 receipt records the entire `evaluate` at **275 s**, i.e. **528x** smaller than a lower bound for this code alone. Therefore the round-1 `metrics.json` cannot have been produced by the delivered implementation.

A4. Is the SUPERSEDED_FOR_SCIENTIFIC_INTERPRETATION marking justified? **FACT, yes.** It follows directly from A2 (the file cannot run) and A3 (even if fixed, the frozen bootstrap is infeasible within any reasonable budget).

A5. Does a constant-1 detector fail the v3 gate? **FACT, yes.** `experiment_v3.py` lines 534-538: `gate_a0a1_clean = (a0_fp == 0 and a1_fp == 0)` and `sanity = gate_p1_fires and gate_a0a1_clean and gate_differs`. A constant-1 detector returns 1 on every A0/A1 case, so `a0_fp = a1_fp = 2431 != 0`, the gate fails, and the outcome becomes INVALID.

**AUDIT_A_VERDICT = PASS.** The single weakest link: the v3 verdict rests on point estimates because the frozen bootstrap could not be run; this is disclosed in the result document and does not change the NEGATIVE class or the DECLINE_CITE decision.

## Audit B - spillover (does PR-03 contaminate Track A evidence?)

B1/B3. Independent sweep (my own, not the existing document): eight PR-03 tokens (`PR-EXP-03`, `positive_repair`, `predict_loco`, `a1_table`, `a3_fp`, `0.8116`, `topology_transposition`, `field_hit`) were searched in `paper/saner_rene_manuscript_v1.md`, `paper/saner_rene_references.bib`, `paper/saner_rene_claim_matrix_v1.json` and `paper/saner_rene_manuscript_scope_lock_v1.md`: **0 hits in all four files for all eight tokens**. **FACT.**
B2. Multi-leaf provenance independence: `research/stage_e_multileaf_20261010/analyze_multileaf_signature_ablation.py` imports only `__future__`, `hashlib`, `json`, `math`, `collections`, `pathlib`, `typing`, `numpy` - no Track P import. Its result `results/multileaf_signature_ablation.json` (sha256 `0518c5bf...`) is the artifact the figure manifest binds, and the wide evidence verifier confirms its hash. **FACT.**

**AUDIT_B_VERDICT = PASS.** No Track P lineage touches any Track A evidence; the multi-leaf headline numbers come from an independent, numpy-based pipeline.

## Audit C - submission package

C1. Page budget: the compiled PDF is **8 pages**. Text extraction (this re-verification) places the Conclusion and the Data Availability section on page 7, References starting on page 7 and continuing to page 8, and Appendix A on page 8. Main content including the appendix is 8 pages (limit 10 including figures and appendices); references occupy about one page (limit 2 references-only pages). **FACT.**
C2. Citation resolution: `scripts/verify_claim_evidence.py` reports 21 cited keys, 21 bib entries, 0 missing, 0 unused; a text scan of the compiled PDF finds no `??`. **FACT.**
C3. Anonymisation: source scan finds no author/affiliation/host/path strings; PDF metadata has Title set and Author empty. **FACT.**
C4. Forbidden claims: scanning the compiled PDF text for the four forbidden phrases returns 0 occurrences. **FACT.**
Extra (fixed during this audit): IEEEtran had lowercased two proper nouns in the bibliography (`Agentchaos`, `Agentprocessbench`); both titles are now brace-protected and render as `AgentChaos` and `AgentProcessBench` (the latter wraps across a line, which is why a naive text count first read zero). `WIDE_EVIDENCE_CHECK = PASS` after the rebuild.

**AUDIT_C_VERDICT = PASS.**

## Overall

**LOOP_C_INDEPENDENT_VERDICT = PASS (SELF-AUDIT, NOT INDEPENDENT).**
Top residual risk: the independence gap itself. Every factual claim above was re-derived mechanically in this pass (symtable proof, measured timing, direct sweeps, PDF text extraction), so the findings do not rest on earlier summaries; but no separate agent confirmed them. If a working delegation channel appears later, `INDEPENDENT_AUDIT_PACKET_v1.md` remains the one-step handoff for a true independent pass.