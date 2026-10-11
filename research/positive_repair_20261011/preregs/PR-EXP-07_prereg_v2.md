# Prereg — PR-EXP-07: Label-blind re-extraction (anti-tautology robustness)

> version: v2 (revision 1; closes audit-v1 conditions a-e) | experiment_id: PR-EXP-07 | candidate: PR-07 | role: ROBUSTNESS_ANTI_TAUTOLOGY (supporting evidence only; NOT a repair count)
> frozen: 2026-10-11 | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> Objective: re-test the multi-leaf result after removing every possible label / contract-construction information channel. NOT a new positive method.

## 1. Extractor blindness contract (provably enforced)
Inputs ONLY: the unordered pair {A,B} of paired raw observation states. Blind pairing: the PAIRING RULE is built from the frozen cluster structure only (which samples belong together is fixed by construction, never by response values); pair ORDER randomized by frozen seed; features computed as order-invariant (symmetric) functions; swap-invariance test required across all rows (feature(P) == feature(swap(P))).
Forbidden knowledge (structurally impossible): mutation family label; stage label; expected first stage; target checkpoint identity; gold outcome; sample namespace; generation code.
Label provenance (declared): decoded labels are injection-design stage labels fixed in the frozen freeze record before scoring; labels are never response-derived.
Freeze timing: extractor + feature sets frozen BY HASH BEFORE any feature-value observation (freeze first, then compute features, then evaluate). No post-hoc tuning; any edit -> new prereg.
Pairing-rule certification: record the pairing rule source + proof it reads no response values (code inspection note + hash).

## 2. Frozen feature sets and population
- Population: the frozen 216-row multi-leaf carriers (paths + hashes pinned in the implementation contract); LOCO groups = frozen cluster ids (rule referenced by hash from the freeze receipt).
- Feature sets frozen by hash: full label-blind set; direct-codebook subset (label-blind definition frozen); non-direct subset.
- NULL rule (binding): full <= direct -> NULL.

## 3. Primary metric and numeric criteria
macro-F1 / top-1 under frozen nearest-centroid + LOCO vs direct-codebook baseline vs chance (1/3).
Shuffled-label negative control (frozen seed) included.
Numeric "clearly above" (frozen): ROBUST requires (full point − direct point >= 0.05) AND (non-direct point >= 1/3 + 0.05).
Case taxonomy (complete): ROBUST (both criteria); NULL_DIRECT_CONCENTRATED (full > direct but non-direct <= chance margin); NULL (full <= direct); NULL_AT_CHANCE (full > direct but full ≈ chance within 0.05); NOT_EVALUABLE (undefined features / missing proof artifacts; row-level attrition accounting mandatory; never merged into NULL); INVALID (any leakage channel usable; swap-invariance or pairing proof fails).

## 4. Interpretation (owner-fixed)
- ROBUST -> robust supporting evidence.
- Degradation -> retain NULL/negative AND explicitly lower the original multi-leaf claim (recorded, never silent).

## 5. Required reports
- Quantified blind-vs-original delta on identical rows: Δ = full_labelblind_macroF1 − original_frozen_macroF1, reported with CI; explicitly declared non-comparable claim-wise (different measurement objects) while the numeric delta is recorded.
- Attrition table (rows per exclusion reason).

## 6. Cost / Stop
Zero model calls; deterministic; minutes of GB10 compute.
STOP: swap-invariance or pairing proof failure -> INVALID; then stop. No rescue tuning of the extractor.