# Loop A Task: Final Evidence And Matching-Rule Closeout

Task ID: `natural-error-cost-closeout-a-20261026`

Goal ID: `NATURAL_ERROR_EVIDENCE_COST_20261026`

Role: A-EXP. File ownership:
`research/natural_error_evidence_cost_20261026_v1/a_closeout/`.

Bind to commit `622b386986ca66c8119263e146f3d3e73c33e260`. Zero generation,
training, judge, production and confirmation calls. Preserve `a_prepare/`
and `a_remediate/` byte-for-byte.

## Required Closeout

1. Publish `MECHANISM_NEIGHBORS_CORRECTED.md`. Mark the old
   `a_prepare/MECHANISM_NEIGHBORS.md` row-2 `5/5` claim and `229/507` figure
   `SUPERSEDED`, and replace them with `4/5 overall / 4/4 genuine` and the
   corrected P2 figures.
2. Implement the declared answer normalization in a new executable matcher:
   Unicode NFKC, casefold, quote/dash normalization, whitespace collapse,
   thousands-separator removal between digits, terminal punctuation trim, and
   numeric handling for `$`, commas, `%`, parenthesized negatives and visible
   scale words only after unit compatibility.
3. Add self-tests for at least `68.07%`, `68.07 percent`, `$1,496.5`,
   `1,496.5`, parenthesized negatives, multi-span, count and UNKNOWN.
4. Re-freeze `P2_ANSWER_MATCHING_RULE_FINAL.json` and
   `P2_PREREG_RECEIPT_FINAL.json` after the implementation hash is fixed.
5. Clarify that the executed screen's primary proxy is
   `semantic_reference_potential` over 507 questions; future model evaluation
   uses `full_semantic_answer_accuracy` over the 506 complete references.
6. Derive all published aggregate counts at runtime rather than hardcoding
   literals. Replay `P2_RECOVERY_RECOMPUTE.py` or an equivalent final program
   and preserve row-level hashes.
7. Correct the P1 visible-example transcription: emit distinct visible rows,
   include the period-axis row, and make declared field lists match emitted
   fields.

## Outputs

- `a_closeout/A_CLOSEOUT_RESULT.json`
- `a_closeout/MECHANISM_NEIGHBORS_CORRECTED.md`
- `a_closeout/P2_ANSWER_MATCHING_RULE_FINAL.json`
- `a_closeout/P2_PREREG_RECEIPT_FINAL.json`
- `a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.py`
- `a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.json`
- `a_closeout/NATURAL_ERROR_DIAGNOSIS_FINAL.jsonl`
- `a_closeout/P1_SEMANTIC_LEDGER_FINAL.json`
- `a_closeout/STAGE_CANDIDATE_FINAL.json`

Final disposition must remain `NO_GO_STOP_MODEL_STAGE` unless the final
row-level replay actually produces a restricted frontier passing both the
frozen margin and budget. Final response must be compact JSON.
