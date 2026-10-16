# TQ-3 Developmental Dry-Run Panel

> DEVELOPMENTAL_DRY_RUN_NOT_HELDOUT - not confirmatory; not human gold.
> Built 2026-10-16 by Loop D (AI). No model calls.

- inputs_original/ - 6 original-variant inputs
- inputs_perturbed/ - 6 perturbed-variant inputs
- reference/ - reference-side official answers (never given to the system under test)
- scoring/ - reference-side scoring rules consumed by tools/tq3_scoring_entry.py
- PANEL_MANIFEST.json - file pins, counts, exclusions

All 12 inputs share one field structure: task_id, variant, question, table, paragraphs.
The panel pairs original/perturbed variants of the same 6 tasks (paired design; not 12 independent samples).
