# WP-2 Bridge v2 Offline Qualification Report

Task: `tatqa-wp2-bridge2-20261014`. This report covers implementation and offline qualification only; no model, judge, endpoint, database, or S4 run was performed.

## Layer Results

- L1/L4 constrained decoding: `outlines` install was blocked by PEP 668; the fallback processor was dry-run with a read-only tokenizer and no weights loaded. Dry-run PASS=True.
- L2 prompts: plan/consume templates contain exactly one locked example each; hashes are pinned in the receipt.
- L3 validation: synthetic corpus 9/9 passed across all three parse routes and schema violations.
- Replay: 8 ledger attempts were replayed from the available evidence. 7 distinct raw files remain; the overwritten duplicate is disclosed and not reconstructed. Prose plan rejection=True.

## Unverified Surfaces

- Online constrained generation on GPU/model weights is not run.
- S4c and all model/judge/probe budget calls remain unauthorized and unexecuted.
- The custom processor is not a replacement for a general grammar engine; tokenizer changes require a new dry-run.
