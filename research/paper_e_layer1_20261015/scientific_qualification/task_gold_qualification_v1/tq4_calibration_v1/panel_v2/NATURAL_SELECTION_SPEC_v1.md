# TQ-4 Natural-Task Selection Spec v1 (frozen)

> Frozen: 2026-10-16, before any TQ-4 model output exists (TQ-4 has not run).
> Scope: four NEW natural tasks for the TQ-4 calibration run, part 1 (actor/B/C x 4).
> Structural selection only (no model outputs, no labels used to rank cases), consistent with the original
> policy note `output_label_access_in_selection = false`.

## Candidate pool

- `coordinator/pool_inventory.json` (59 entries; the same pool the TQ-3 twelve were drawn from).

## Inclusion criteria (all must hold)

1. `stratum` in {S1, S2, S3, S4}.
2. `injection_id` not in the TQ-3 used set (`coordinator/case_provenance.json`).
3. `uid` not in the TQ-3 used uid set, and not already used within this TQ-4 selection.
4. Corpus joins: uid present in `raw/tatqa_tables.json` and `raw/injected_tables.json`; source[uid][0][col] == original;
   injected[uid][0][col] == injected; and source[uid][1:] == injected[uid][1:] (only the injected header cell changes).
5. Raw record exists in `raw/tatqa_dataset_train.json` or `raw/tatqa_dataset_dev.json` (indexed by table uid).
6. Chosen question: among the record's questions with `answer_from` in {`table`, `table-text`}, ordered by the frozen
   question rank (`-overlap(question, original header)`; arithmetic first; question order; question uid), take the first
   question whose recorded answer is present AND numeric ("structural sanity"; all skips logged).

## Selection order (frozen)

- Strata in order S1 -> S2 -> S3 -> S4; exactly one task per stratum (4 total).
- Within a stratum: candidates sorted ascending by sha256(injection_id, UTF-8); take the first passing all criteria;
  if a candidate fails joins/record/question checks, continue down the sorted list (all skips logged).

## Model-visible variant (frozen)

- Model-visible input = the **perturbed** table variant (study object = perturbed documents); the original variant
  ships alongside for reference-side use only. Both are built once; nothing is added later.

## Scoring material (frozen derivation rules)

- `compare_mode = numeric` for all four (verified numeric at build).
- `unit_kind`: `percent` if the recorded derivation contains '%', else `plain` (no ratio case in this set).
- `abs_tolerance = 0.5 x 10^(-d)`, d = decimal digits of the recorded answer's canonical string form.
- `unit_scale_status = RESOLVED` (unit provenance recorded in the reference file).

## Freeze

- `SELECTION_LOG.json` records corpus hashes, pool hash, all skips, per-case joins, question rank, chosen
  question/reference, written-file hashes, and the freeze timestamp.
- After freeze, no modification; any change requires a NEW version with a new log.
