# Decision-Residual Mechanism Neighbors

Status: evidence-bound neighbor audit; **no novelty claim**.

The two screened directions sit next to existing local literature, source-native
baselines and prior zero-model results. Renaming state adjudication, retrieval
neighbor expansion or exact reuse would not create an independent contribution.

## 1. CUPMem / STALE: structured state adjudication and propagation-aware search

- Neighbor: `reading_notes/2026_STALE_2605.06527.md` (SHA-256
  `e74b1aa1d7d3eb7366d5bc9acfcc0c9f8f9c90d9cfabe91169fcbea43cce3e61`).
- Existing mechanism: typed state deltas, observed-versus-inferred update
  separation, stale/unknown-current archival, propagation-aware candidate
  search and constrained readout.
- Difference needed for a genuine contribution: demonstrate a natural,
  downstream action residual that cannot be explained by typed lookup,
  propagation or a generic state card. None is present here.
- Boundary: CUPMem uses a predefined state schema and an embedding retriever;
  the STALE benchmark is generated and expert-edited rather than natural
  deployment history.

## 2. STALE evaluation boundary: judge and benchmark are not human gold

- Neighbor evidence: `reading_notes/2026_STALE_2605.06527.md`, fact cards and
  §6 limitations.
- Existing result: STALE decomposes state resolution, premise resistance and
  implicit policy adaptation, but its official evaluator is an LLM judge and
  its explanations encode intended dependency.
- Difference needed: independent human or fully executable semantic gold plus
  a real post-feedback action change. A state-card gain alone is insufficient.
- Current task use: this neighbor prevents treating generated role-collision
  fixtures or an LLM-judged explanation as natural decision history.

## 3. Adaptive V3: greedy transparency versus lookahead

- Neighbor: `research/adaptive_revalidation_v3/TASK_SPEC.md` (SHA-256
  `513c0931c2e2aed84653db6bb60c4504841ec55d87913b312f62eb32f97f3d0c`).
- Existing mechanism: nine authored scenario families, fixed repairer, budgets
  0 through 9 and paired comparison of greedy against two-step lookahead at
  matched query cost.
- Existing result summarized by the reuse map: greedy transparent policy is
  sufficient on the current fixtures; lookahead has no positive paired gain.
- Difference needed: a natural source family where the next legal evidence
  action is not already selected by a simple greedy or fixed-neighbor rule.
- Current task use: always-expand acquisition is already a stronger control
  than an adaptive selector until an independent adaptive residual is shown.

## 4. Exact cache and miss revalidation explain prior reuse savings

- Neighbor: `research/publication_thesis_goals_v1/revision_v4/REUSE_EXACT_CACHE_BASELINE_V2.json`
  (SHA-256 `8af63a21b657cdcbece6f52ee0a24c9b460f7dd8308859fe0043103a4a2f30eb`).
- Existing policy: defer when the scope fingerprint is missing; reuse only
  exact-input per-input evidence with unchanged dependency; otherwise
  full-check the miss.
- Existing result: 30 probes, 15 correct and 5 abstentions; the artifact states
  that the five-probe saving is explained by exact-input reuse only.
- Difference needed: a repeat-independent first-occurrence residual or a
  dependency change missed by exact identity and full-check fallback.
- Current task use: exact cache is a mandatory baseline, but it cannot explain
  the first-occurrence FinQA examples; ordinary source lookup already does.

## 5. FinQA source-native retrieval and paragraph closure

- Neighbor and pinned snapshot: `/home/testuser/wzh/phase1a_staging_20260925/finqa/dev.json`
  (SHA-256 `a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51`).
- Existing source-native signal: official top-3 retrieval covers 168/198
  text-only gold questions; top-5 reaches 171/198.
- Existing fixed-neighbor result: top-3 plus paragraph radius 1 reaches
  177/198, radius 2 reaches 186/198 and radius 5 reaches 195/198.
- Difference needed: retain only cases where gold evidence is legally absent
  or not recoverable by ordinary ranking, larger fixed k or document-local
  closure, then verify a complete semantic reference and bounded action.
- Current task use: the selected examples demonstrate acquisition failures but
  are fully explained by fixed neighborhood expansion, so they are NO_GO.

## Neighbor conclusion

Neither direction has an independent residual in the inspected material.
Future qualification should begin with a genuinely untouched natural source
family, not with renamed retrieval, cache or state-card mechanisms.
