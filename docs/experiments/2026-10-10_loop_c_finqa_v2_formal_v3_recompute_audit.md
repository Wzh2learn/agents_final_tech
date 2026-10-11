# FinQA v2 Formal V3 — Fresh-Context Independent Recomputation (Loop C)

**Nature of document.** Advisory independent recomputation report (Loop C / GB10 fresh-context). It recomputes and compares; it does **not** repair, re-run a formal experiment, or adjudicate the final class. No Loop A output and no frozen artifact was modified; all scratch computation ran in `/tmp`.

**Research question.** Does the visibility-detection separation transfer to a different reasoning-oriented dataflow under an independently implemented observation scorer?

**Audited object.** The Loop A formal binding-v3 rerun under `research/finqa_v2_20261010/results_binding_v3_rerun/` (task `finqa-v2-formal-rerun-v3-loop-a-20261010`), its `A_RECOMMENDED_CLASS=SECOND_FLOW_MIXED`, and the frozen analysis plan / manifests / binding-v3 contract / unchanged scorer / authority map / preflight certificate.

**Independence declaration.** Fresh-context Loop C; I did not build the audited artifacts (Loop A did) — this is not a self-audit. I recomputed V/D/O **from the five frozen observation-vector fields** using the plan's literal definitions (I did not trust A's stored `V`/`D`/`O` columns), derived all estimands from the frozen formulas, and re-implemented the 10,000-replicate cluster bootstrap from scratch in `/tmp` (own code, `numpy.random.default_rng(20261017)`, documented `overall30→E10→P10→N10` draw order per replicate). I formed my numbers and class reasoning before opening A's conclusions at the comparison step; agreement is reported as corroboration, not manufactured as a finding.

---

## 1. Exact A/C comparison (all matched)

**A. Scorer success / failure and V/D/O (independently derived from `observation_vector`).**

| Quantity | C (recomputed) | A | Match |
|---|---:|---:|:--:|
| Evaluation rows | 89 | 89 | ✅ |
| Unique `sample_id` | 89 | 89 | ✅ |
| Scorer success (VALID, not missing/invalid/fail/unevaluable) | 89 | 89 | ✅ |
| Scorer failures / missing / invalid / unevaluable | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | ✅ |
| V=1 count | 89 | 89 | ✅ |
| D=1 count | 0 | 0 | ✅ |
| O=1 count | 0 | 0 | ✅ |
| V/D/O row-wise mismatches vs stored columns | **0** | — | ✅ |
| V/D/O mismatches vs `finqa_v2_v_d_o_rows.jsonl` | **0** | — | ✅ |

V/D/O definitions applied literally: `V = 1` iff any of the 5 fields = 1; `D = 1` iff `step_result_consistency==1 OR answer_consistency==1`; `O = 1` iff `answer_consistency==1`. Observation vectors are stage-structured — E lights `evidence_required_hit`, P lights `operator_consistency`, N lights `argument_consistency`; `step_result_consistency` and `answer_consistency` are 0 on all 89 rows.

**B. Primary estimands (point) — 56/56 exact, 0 mismatches.**

| Estimand | C | A |
|---|---:|---:|
| Visibility count / rate | 89 / 1.000000 | 89 / 1.000000 |
| Detection count / rate | 0 / 0.000000 | 0 / 0.000000 |
| 2x2 V0D0 count/rate | 0 / 0.000000 | 0 / 0.000000 |
| 2x2 V0D1 count/rate | 0 / 0.000000 | 0 / 0.000000 |
| 2x2 V1D0 count/rate | 89 / 1.000000 | 89 / 1.000000 |
| 2x2 V1D1 count/rate | 0 / 0.000000 | 0 / 0.000000 |
| P(D=1\|V=1) | 0.000000 | 0.000000 |
| P(D=1\|V=0) | NOT_IDENTIFIABLE (den=0) | NOT_IDENTIFIABLE |
| Terminal O count / rate | 0 / 0.000000 | 0 / 0.000000 |

**C. E/P/N secondary profiles — exact.**

| Stage | V count/rate | D count/rate | V0D0 | V0D1 | V1D0 | V1D1 |
|---|---|---|---:|---:|---:|---:|
| E | 30 / 1.000000 | 0 / 0.000000 | 0 | 0 | 30 | 0 |
| P | 30 / 1.000000 | 0 / 0.000000 | 0 | 0 | 30 | 0 |
| N | 29 / 1.000000 | 0 / 0.000000 | 0 | 0 | 29 | 0 |

**D. Frozen 10,000 report-cluster bootstrap @ seed 20261017 — all intervals / valid / failed exact, 0 mismatches.**

- Per-replicate cluster multiplicities: **10,000 / 10,000 identical** to A's `finqa_v2_bootstrap_replicates.jsonl` (overall + per-stage + failed-estimand lists).
- Aggregate interval / interval-label / valid / failed counts: **56 / 56 identical**.
- RNG-sensitive count estimands reproduced exactly: `visibility_count` [87.0, 90.0]; `visibility_detection_2x2.v1_d0_count` [87.0, 90.0]; `stage.N.visibility_count` [27.0, 30.0]; `stage.N.…v1_d0_count` [27.0, 30.0] (all `PERCENTILE_95`, valid=10000, failed=0).
- Degenerate/unidentifiable reproduced exactly: `detection_rate_given_visibility_positive` [0,0] `DEGENERATE`; `detection_rate_given_visibility_negative` `NOT_IDENTIFIABLE` (valid=0, failed=10000); `stage.E/P.visibility_count` [30,30] `DEGENERATE` (uniform size-3 clusters).
- `PERMUTATION_TEST = NOT_USED` preserved.

## 2. Population, denominator, leakage, and integrity audit

| Check | Result |
|---|---|
| 89 samples / 30 report clusters | ✅ 89 unique sample_id; 30 unique `report_cluster_id` (1:1 with stage-scoped `cluster_id`) |
| Stage denominators | ✅ E=30, P=30, N=29; overall N_eval=89 |
| Exact denominator (no reduction) | ✅ every estimate uses N_eval=89 / stage 30·30·29; no surviving-row substitution |
| Split roles in eval set | ✅ all 89 `split_role=evaluation`; 0 train / 0 calibration scored |
| Group disjointness / assignment / leakage-fail-closed | ✅ PASS / PASS / PASS; independent check: 0 groups span >1 role |
| Exclusions after split | ✅ 0. The single exclusion (`JOIN_AMBIGUOUS`, `FINQA-V2-N-71dc5f1550d1…`, N:ZBH/2007) is `BEFORE_SPLIT_ASSIGNMENT`, `result_dependent_exclusion=False`, `denominator_reduced=False` |
| Threshold / metric changes | ✅ none. 56 estimands = frozen set; `additional_result_metrics_authorized=False`; `threshold_change / metric_or_test_addition / adverse_case_deletion / result_dependent_claim_change = False`; `result_class_rules.modifiable_after_outputs=False` |
| Raw/normalized binding hashes | ✅ raw==manifest_artifact 89/89; raw≠normalized 89/89; scorer_payload==normalized 89/89; `binding_v3_status=PASS` 89/89; 0 hash problems |
| Prior-run immutability | ✅ `results` receipt `2d94d300…` and `results_binding_v2_rerun` receipt `8a0017e1…` byte-identical (independent rehash == authority-map digests); preflight `drift=0, unchanged=True` |
| Frozen authority hashes (independent rehash) | ✅ analysis-plan MD/JSON, sample manifest, split manifest, scorer-binding manifest, scorer source `b48ed17c…` all MATCH authority-map digests |
| Frozen / nested paired hash logs | ✅ `60` frozen checks `0` mismatches; `645` nested paired checks `0` mismatches; end-to-end preflight checker `PASS` |
| Adverse/null case preservation | ✅ all 89 rows preserved; V1D0=89, V0D1=0, V0D0=0, V1D1=0; V==D 0, V≠D 89 |

**Data-provenance note (not a defect).** 89 evaluation samples rest on **61 unique underlying records** (78 unique raw content hashes) via within-cluster repeat injections (`repeat_within_cluster` design). This is exactly why the resampling unit is the report cluster (30), not the sample — cluster bootstrapping correctly absorbs within-cluster dependence; naive per-sample independence would overstate precision.

## 3. Claim-boundary audit

A's report stayed within the authorized boundary: it labels overall V/D estimands `CONFIRMATORY`, per-stage/O/bootstrap `SECONDARY`, adverse/null cases `NEGATIVE`; it reports the construct distinction **only** as `A_RECOMMENDED_CLASS`, explicitly deferred to Loop C audit and Loop D decision; and it lists — without asserting — every forbidden claim (hierarchy-beats-flat, hierarchy localization, scorer semantic superiority/correctness, natural-failure localization, harmfulness, automatic Stage-E transfer). No forbidden claim was made; `semantic_correctness_claim=False` is preserved. The frozen estimand surface was not expanded (56 = authorized). **Claim boundary: VALID.**

## 4. Recommended class: `SECOND_FLOW_MIXED`

Applying the frozen result-class rules to the verified facts (contract valid; V≡1 constant; D≡0 constant; V≠D for all 89; uniform across E/P/N):

- `SECOND_FLOW_POSITIVE` — **not available**: requires *both* V and D nonconstant; both are constant here (even though the `≥1 sample V=1,D=0` clause holds, 89-fold).
- `SECOND_FLOW_NULL` — **not met**: requires `V=D for every sample` (false; V≠D for 89/89) **or** "no informative nonidentity" (false; informative nonidentity V=1,D=0 is observed for 89/89).
- `SECOND_FLOW_INVALID` — **not met**: no contract/leakage/scorer/split/failure-handling violation.
- `SECOND_FLOW_MIXED` — **met** via the branch "one construct is degenerate while nonidentity remains informative": the constructs are degenerate (constant), yet the nonidentity (V=1,D=0) is real, total, and informative.

This matches A's `SECOND_FLOW_MIXED`. **C audit = PASS**; the class is supportable. Final adjudication belongs to Loop D.

## 5. Scientific reason

The visibility–detection separation **transfers** to the FinQA v2 reasoning-oriented dataflow under an independently implemented observation scorer: visibility and detection are maximally non-identical (V=1 with D=0 on 89/89; zero V=D), uniformly across E, P, and N. The scorer "sees" the paired-checkpoint observation reproduction (V=1) without conflating it into step/answer detection (D=0) — the two constructs remain empirically distinct, which is exactly what the research question asks. But the transfer is a **degenerate corner**: both constructs are constant, so the joint structure is a single populated cell and the class is `MIXED` (degenerate construct with informative nonidentity), not `POSITIVE` (which would require nonconstant V and D to show separation across regimes). In short: the separation phenomenon carries over (positive transfer signal), but the evidence is a corner solution that cannot characterize when detection would fire.

## 6. Strongest positive finding

**Uniform, maximally-nonidentity separation that survives both a new dataflow and a new scorer.** Across 89 evaluation samples / 30 report clusters / 3 stages, the visibility–detection separation holds at 100%: every sample is V=1,D=0, so V≠D on every row and the constructs are never conflated. The pattern is identical in E, P, and N (not stage-specific), it is reproduced exactly by an independent Loop C implementation (56/56 estimands, 10,000/10,000 bootstraps), and it is robust to the cluster-level uncertainty model. This is direct confirmatory-grade evidence that the separation is a property of the construct pair, not of one dataset or one scorer.

## 7. Strongest negative / boundary finding

**The result is a degenerate corner, so it cannot characterize the joint regime.** V≡1 and D≡0 are both constant; only the V=1,D=0 cell of the 2×2 is populated; `P(D=1|V=0)` is `NOT_IDENTIFIABLE` (zero V=0 denominator — reported, not substituted); and the bootstrap is `DEGENERATE_EMPIRICAL_INTERVAL` for every rate/cell/conditional estimand (only count estimands with non-uniform cluster sizes — overall [87,90], stage.N [27,30] — have non-degenerate intervals; E/P are [30,30] because their clusters are uniform size-3). Consequently the study cannot distinguish "cleanly separable constructs with a rich joint structure" from "an injection design + deterministic scorer that always lands in one corner cell," cannot estimate the visibility-negative regime, and establishes **no** detection capability, failure localization, harmfulness, or semantic-correctness property (all remain in the forbidden set). Because there is no variation, the honest reading is maximal nonidentity in a single regime — a strong "separation transfers" signal but a degenerate characterization of it.

## 8. Verdict

**`VERDICT: PASS`** — All primary and secondary recomputations match A exactly (56/56 point estimands, 10,000/10,000 bootstrap replicates and every interval/valid/failed count, 0 V/D/O mismatches); denominators are exact with no manipulation; no leakage; frozen hashes and prior-run immutability verified independently; the allowed/forbidden claim boundary is respected; and the recommended class `SECOND_FLOW_MIXED` is supportable under the frozen rules. **Single blocker (if not PASS): none** — this is a clean PASS. The degenerate-boundary caveat in §7 is filed as a standing scientific limitation for Loop D adjudication, not as an audit defect.

---

**Boundary respected.** No Loop A output or frozen artifact modified; no replacement formal experiment; metrics/thresholds/split/scorer/bootstrap unchanged; no PRM, Stage D, or Paper E work. Zero-endpoint, non-training (this recomputation consumed frozen sample rows only — no model, endpoint, database, or training call). All scratch computation ran in `/tmp/loop_c_recompute/`.
