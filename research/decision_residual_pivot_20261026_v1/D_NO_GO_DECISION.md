# Decision-Residual Screening Decision

Goal ID: `DECISION_RESIDUAL_PILOT_20261026`
Date: 2026-10-26, Asia/Shanghai

## Decision

`NO_GO_FOR_MODEL_PROBE`

The Phase B R/E stop remains unchanged. A's preparation produced no qualified
natural decision residual after strong deterministic controls. Per the current
research prompt, model generation is not released when qualification fails.

## Candidate Disposition

1. `C1_CONDITIONAL_EVIDENCE_ROLE_APPLICABILITY`: `NO_GO`.
   The stated label+period rule explains 3/4 selected failures; a
   positional/ordinal role-equality rule explains 4/4. The earlier `4/4` figure
   is valid only under that strengthened positional rule. Exact cache does not
   create a decision and cannot establish a learned residual.
2. `C2_VERIFIABLE_EVIDENCE_ACQUISITION`: source-scope corrected.
   The FinQA snapshot may remain historical evidence but is not reauthorized as
   a new task source. It is excluded from the new candidate claim. A separate
   TAT-QA natural text-evidence screen gives the same practical result: on 389
   text-only dev questions, TF-IDF top-3 covers 378, top-5 covers 385,
   top-3 plus top-1 neighbor covers 385, and top-10 covers 389/389. Fixed
   neighborhood/top-k or always-expand explains the acquisition headroom.
   However, top-10 is already always-expand for 359/389 questions and top-5 is
   already always-expand for 262/389; the screen measures evidence coverage,
   not a cost-aware policy advantage. No cost-aware expansion residual is
   established or tested here.

Both routes therefore lack a residual that survives the strongest simple
baseline. The correct next requirement is an untouched natural source family
with a complete semantic reference, legally retrievable missing evidence, and a
residual that survives exact cache, metadata/period rules, retrieval, fixed
lookup, larger top-k and always-expand/neighbor controls.

## Evidence Identity

- A preparation: `phaseb-postb-prepare-a-20261026`
- A source: `a_prepare/A_PREPARE_RESULT.json`
- Fresh D TAT-QA screen: 389 text-only TAT-QA dev questions, no model calls
- No generation attempts, training runs, judge calls or production calls
- Development examples are exposed and cannot become a future confirmation set
- No mechanical qualification or small-sample signal is promoted to a method

## Collaboration Accounting

- A/C dispatches used before this decision: 1 preparation dispatch
- C independent audit: `phaseb-postb-nogo-audit-c-20261026`
- Remaining dispatches: 1
- The model-probe A execution and probe C audit remain unused because the
  qualification gate failed. C independently verified this no-go and the
  source-scope correction through `phaseb-postb-nogo-audit-c-20261026`.

## C Audit Disposition

C returned `CONDITIONAL` only for evidence-chain precision. D files the five
conditions without rewriting A artifacts:

1. The authority hash discrepancy is a line-ending false positive:
   `e4c535...` is the LF-to-CRLF view of git blob `5c3f970d...`; canonical GB10
   LF SHA-256 is `327fb04a...`.
2. Current `D_PREMISE_CORRECTION.md` SHA-256 is
   `8f3911c624e3685f8ad7018a70abe7d27ed2a7c1e58cc02b4e1d21ec5461da60`;
   A's earlier receipt predates the later D corrections.
3. C1 is corrected to 3/4 under label+period and 4/4 under positional role
   equality, as stated above.
4. The 39/217 composition carries asymmetric `11/7/7/7/7` correction weights
   and is not an independent 39-example denominator.
5. FinQA-derived counts are excluded from the new evidence claim and are not
   carried as historical receipts.

With these disclosures, D accepts `NO_GO_FOR_MODEL_PROBE`. This does not turn
the deterministic screens into a method result.
