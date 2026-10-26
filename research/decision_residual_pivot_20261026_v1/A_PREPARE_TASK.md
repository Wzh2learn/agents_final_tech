# Loop A Task: Decision-Residual Qualification Preparation

Task ID: `phaseb-postb-prepare-a-20261026`

Goal ID: `DECISION_RESIDUAL_PILOT_20261026`

Role: A-EXP. File ownership:
`research/decision_residual_pivot_20261026_v1/a_prepare/`.

Bind this task to commit `19ddd7feffe90779f021304345ce894550c92816`, the
current research prompt and `D_PREMISE_CORRECTION.md`. Do not call a model,
judge, training service or production endpoint. Do not modify old Phase B raw,
reports, protocols or scores.

## Required Work

1. Verify the premise corrections from actual source and frozen receipts:
   active adapter path, model/tool responsibility, 5/3 unique corrections,
   39/217 repeated training composition, target scope and strict/embedded
   layers. Record commands and hashes.
2. Screen at most two natural decision-residual candidates from existing
   failures, frozen outputs, public-source snapshots and the reuse map:
   - conditional evidence applicability;
   - verifiable evidence acquisition;
   - or one evidence-backed better alternative.
3. For each candidate provide 3-5 real examples with:
   `natural_failure_input -> visible_signal -> legal_action -> new_evidence ->
   full_semantic_reference`.
   Separate natural missing information from artificial masking. Reject any
   example lacking a complete reference or deployable action.
4. Specify the strongest simple baselines. At minimum consider exact cache,
   metadata/period rules, ordinary retrieval/fixed lookup and always-expand or
   direct-answer controls as applicable. If a simple baseline explains the
   residual, mark `NO_GO`.
5. Give 3-5 concrete mechanism-neighbor differences from existing local
   literature/primary-source notes. Do not claim novelty from renaming generic
   retrieval or caching.
6. Mark every selected development example as exposed in the future exposure
   union.
7. Draft one freezeable probe contract for the single best qualified candidate:
   at most 48 physical generation attempts and 240,000 generation tokens,
   zero training, 2-4 necessary arms, fixed input/decode/tool budgets and
   separate oracle diagnostics. Report full semantic answer, wrong-to-correct,
   correct-to-wrong, reasonable UNKNOWN, wrong delivery, correct coverage and
   actual cost.

## Outputs

- `a_prepare/A_PREPARE_RESULT.json`
- `a_prepare/PREMISE_VERIFICATION.json`
- `a_prepare/CANDIDATE_SCREEN.json`
- `a_prepare/REAL_EXAMPLES.jsonl`
- `a_prepare/MECHANISM_NEIGHBORS.md`
- `a_prepare/PROBE_CONTRACT_DRAFT.json`

If neither candidate has an independent residual, output a documented `NO_GO`
and one missing condition. Do not invent synthetic gold or use oracle evidence
to qualify a deployable candidate. Final response must be compact JSON.
