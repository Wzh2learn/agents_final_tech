ROLE: Loop C / GB10 independent challenge
MODE: reviewer-style fact-check
QUESTION:
Is the FinQA causal-exposure design non-tautological and ready for preregistration, or must it remain blocked?

INPUTS:
- `docs/research/finqa_causal_exposure_preregistration_proposal_v1.md`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_design.json`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_feasibility.json`
- `research/finqa_causal_exposure_20261010/finqa_causal_exposure_source_ledger.json`
- `research/finqa_causal_exposure_20261010/FINQA_CAUSAL_EXPOSURE_LATER_EXECUTION_TASK_CARD_NOT_EXECUTED.md`
- frozen FinQA v2 source, scorer and prior autopsy evidence.

REQUIRED CHALLENGES:
1. Is V still guaranteed by injection construction?
2. Does D have a real causal path through deterministic execution?
3. Does re-execution change the measurement object relative to the old failed transfer?
4. Is there label/outcome leakage in eligibility?
5. Is any substantive case manually changing `res` or terminal answer?
6. Are controls scientifically segregated from primary cases?
7. Does the design accidentally target a particular VxD cell distribution?
8. Is the causal-exposure eligible denominator and rate well-defined?
9. Are E/P/N classifications justified?
10. Are missing executor semantics a preregistered condition or a current BLOCKER?

OUTPUT:
- FACT / INFERENCE / UNVERIFIED sections.
- Three strongest scientific objections.
- `FINQA_CAUSAL_EXPOSURE_READY_FOR_PREREG` or `BLOCKED`.
- If READY, list mandatory preregistration conditions.
- If BLOCKED, state the single primary blocker.
- Safe final RQ and claim boundary.

FORBIDDEN:
- Modify any artifact.
- Run the experiment.
- Add controls or metrics.
- Resolve missing semantics by invention.
