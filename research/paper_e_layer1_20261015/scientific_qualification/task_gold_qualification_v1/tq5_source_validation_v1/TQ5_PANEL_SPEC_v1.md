# TQ-5 Source-Separation Developmental Panel - Spec v1 (frozen)

> Frozen: 2026-10-16, before any TQ-5 model output. Basis: OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md (S4).
> This is a bounded developmental validation, NOT a confirmatory study, NOT a large statistical validation.

## Sample source and exclusions (frozen)

- Source: existing public TAT-QA raw data (train+dev records; original public tables/context; no perturbation).
- Exclusion set = union of:
  1. all WP-1/WP-2 origin table uids (`source_refs/origin_manifest.json`, 182 origins, GB10 data copy fetched read-only);
  2. v4 development / 59-pool table uids (`coordinator/pool_inventory.json`, 50 distinct);
  3. all TQ material table uids (TQ-3 twelve + TQ-4 N1-N4).
- Report-level grouping is NOT verifiable from available sources (source_document_id unresolved); therefore the panel is
  claimed **table-disjoint only** - not report-level independent, not "unseen by model training".

## Eligibility (all must hold; ambiguity -> excluded with log)

- `answer_from` in {table, table-text}; recorded answer numeric; derivation is a non-empty string.
- Layer classification (frozen, on the normalized derivation string):
  - `percentage_change`: contains '/' and '*100';
  - `ratio`: contains '/' and no '*';
  - `difference`: contains '-' and none of '/', '*', '+';
  - anything else: excluded (unclassifiable).
- Deterministic recomputation: the derivation (whitespace/currency/comma normalized) is evaluated with a
  restricted arithmetic evaluator; the result must match the recorded answer within `0.5 x 10^-d`
  (d = decimal digits of the recorded answer). Mismatch -> excluded.
- Operand locatability: every numeric literal of the derivation (after dropping the '*100' multiplier)
  must appear in the normalized table text or paragraph text. Missing -> excluded.
- One question per table; table uids unique across the panel.

## Selection order (frozen)

- Three layers, fixed order: difference, ratio, percentage_change; 4 tasks per layer (12 total).
- Seed `20261016`; within each layer, candidates sorted ascending by `sha256(f"{seed}|{table_uid}|{question_uid}")`;
  scan in order, take the first 4 passing all gates.
- If any layer cannot reach 4 valid tasks, STOP (no lowering of criteria, no substitution); record the gap and set NOT_RUN.

## Scoring material (frozen)

- compare_mode = numeric. unit_kind: percentage_change -> `percent`; ratio -> `ratio`;
  difference -> `percent` if '%' in the raw derivation else `plain`.
- abs_tolerance = `0.5 x 10^-d` (same rule as TQ-4 natural tasks). unit_scale_status = RESOLVED.

## Freeze

- `panel/SELECTION_LOG.json` records source hashes, exclusion counts, per-reason skip counts, per-layer scan traces,
  selected rows (with file hashes), and the freeze timestamp. Post-freeze changes require a NEW version.
