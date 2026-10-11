# Prereg — PR-EXP-07: Label-blind re-extraction (anti-tautology robustness)

> experiment_id: PR-EXP-07 | candidate: PR-07 | role: ROBUSTNESS_ANTI_TAUTOLOGY (supporting evidence only; NOT a repair count)
> frozen: 2026-10-11 (Loop D) | authority: Human decision 2026-10-11 (first wave); execution requires Loop C pre-result verdict PASS
> Objective: re-test the multi-leaf result after removing every possible label / contract-construction information channel. NOT a new positive method.

## 1. Extractor blindness contract (must be provably enforced)
Extractor inputs ONLY: the unordered pair {A,B} of paired raw observation states. Blind pairing: pair order randomized by frozen seed; features computed as order-invariant (symmetric) functions; swap-invariance test required across all rows (feature(P) == feature(swap(P))).
Forbidden knowledge (structurally impossible to access): mutation family label; stage label; expected first stage; target checkpoint identity; gold outcome; sample namespace; generation code.

## 2. Frozen feature sets
- full label-blind feature set;
- direct-codebook subset (control);
- non-direct subset;
- NULL rule: full <= direct -> NULL.

## 3. Primary
macro-F1 / top-1 of stage decoding under frozen nearest-centroid + LOCO vs direct-codebook baseline vs chance.

## 4. Interpretation (owner-fixed)
- If label-blind full remains clearly above non-direct/chance -> robust supporting evidence.
- If it degrades -> retain the NULL/negative result AND correspondingly lower the original multi-leaf claim (recorded explicitly, never silent).

## 5. No-rescue rule
Extractor frozen by hash before evaluation; no post-hoc tuning; any edit -> new prereg.

## 6. Cost / INVALID / Stop
Zero model calls; deterministic; minutes of GB10 compute.
INVALID: any leakage channel found usable; swap-invariance or blind-pairing proof fails.
STOP: proof failure; else proceed.