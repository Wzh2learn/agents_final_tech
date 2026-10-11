# Track P Sprint Plan v1 (first round)

> Status: `DRAFT_PENDING_USER_APPROVAL` | 2026-10-11 | Track P must never block Track A (SANER manuscript).
> Hard freeze: 2026-10-20 18:00 Asia/Shanghai. After the freeze only wording/citation/formatting/figure polish/repro checks.

## Timeline (aligned with the user's schedule)

- 10/11: candidate mining + Loop C challenge + Top 3-5 selection. (THIS ROUND; no experiment execution.)
- 10/12: freeze per-experiment preregs for the selected top set (each experiment gets its own prereg; no shared vague prereg) + Loop C pre-result design audit per experiment (quick, packet-based).
- 10/12-10/15: first batch, staggered (target <= 2 days per experiment, all deterministic/zero-endpoint unless flagged):
  1. Highest-ROI low-risk slot first; GB10 Loop A executes; results + receipts materialized.
  2. Each completed run: Loop C post-result recomputation/claim challenge; registry updated (started/positive/null/negative/invalid).
- 10/15 checkpoint: if NO C-audited positive repair exists, STOP expanding experiments; Track A proceeds alone.
- 10/15-10/17: replication / second-context experiment for any surviving repair (mechanism generalization or held-out-cluster replication).
- 10/17-10/18: synthesis gate check: only if >= 3 C-audited positives across >= 2 stages / >= 2 mechanisms -> synthesis inquiry (inquiry-methods: cross-domain-borrowing or first-principles). If not reached: no method synthesis.
- 10/18: evidence-level call (max level actually supported by the registry; no level skipping).
- 10/18-10/20: fold any accepted Track P result into the manuscript ONLY as an addition that does not destabilize Track A; otherwise keep as future-work boundary.
- 10/20 18:00: MANUSCRIPT HARD FREEZE.

## Per-experiment pipeline (fixed)

1. Loop D: freeze the experiment prereg on disk (hypothesis / population / intervention / baseline / metric / cost / split / held-out / success / null / invalid / stop) + hash; registry entry moves to FROZEN_READY.
2. Loop C: pre-result design audit (packet-based; adversarial: definitional gain / observability vs label / held-out independence / fair baseline / fair cost / source-local / measurement-object comparability / NULL value).
3. Loop A: execute on GB10 only (one heavy task at a time where applicable); freeze-before-materialize discipline; receipts with hashes; zero frozen-artifact modification.
4. Loop B/C: independent verification/recomputation; claim-boundary challenge.
5. Loop D: accept/reject into portfolio; registry update; report started/positive/null/negative/invalid counts.

## Budget and discipline notes

- Compute: all candidates in the current draft set are deterministic re-analysis or sub-minute deterministic reruns; the real cost is preregistration + audit, not FLOPs.
- Model calls: only if an experiment explicitly requires them (none in the current top-8 draft except potentially PR-09/PR-12 reserves); any call is budget-tracked and logged.
- Protected surfaces: frozen Stage E numbers, matched-FPR corpus/thresholds, multi-leaf frozen artifacts, FinQA binding/governance closures must NOT be modified. New work uses new namespaces.
- Anti-cherry-picking: see POSITIVE_REPAIR_REGISTRY_v1.json.

## Track A parallel slots (never blocked)

- 10/12-10/14: Figure 1/2/3 source binding + reviewer-attack claim audit (already the recorded highest-ROI first task).
- 10/15-10/16: title / abstract / contributions freeze.
- 10/16-10/18: related-work / novelty positioning + NIST / construct-validity framing.
- 10/18-10/20: submission package / reproducibility checks.