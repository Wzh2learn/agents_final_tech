[loop-c] start 2026-10-09T17:17:18Z
All audit stages complete. No files were modified; no models, training, or network were used. Note: this environment denied interpreter access (`python3`, `python_repl`, `jq` all blocked), so independent recomputation was done with read-only `grep`/`sort`/`uniq`/`wc`/`sha256sum` over the raw JSONL/JSON plus hand arithmetic — fully independent of `run_multileaf_formal.py` and of both repo-side validators.

---

# Loop C Independent Quality Audit — Stage E Multi-Leaf (2026-10-10)

## Independence declaration

I am the independent Loop C auditor for this bounded result. I did not author the freeze, the runner, the results, the validators, or the result packet. I read only the audited files, recomputed all reported statistics from the raw `multileaf_prediction_rows.jsonl` / `multileaf_paired_artifacts.jsonl` / null / replicate arrays without invoking the runner or `validate_multileaf_formal_results.py` / `independent_multileaf_contract_audit.py`, and read `docs/research/stage_e_multileaf_result_packet_v1.md` **only after** criteria 1–7 were complete. Result summary JSON was treated as untrusted output and used only as a comparison target. This audit is read-only; zero files changed; zero model calls; zero network.

## Evidence table

| # | Criterion | Command / file / field | Observed value |
|---|---|---|---|
| 1 | Freeze precedes results | `stat -c '%y'` | receipt + manifest `01:01:51.769`; earliest result `multileaf_paired_artifacts.jsonl` `01:02:07.251`; `multileaf_formal_results.json` `01:02:44.885` |
| 1 | Absence asserted pre-result | `multileaf_preresult_freeze_manifest.json` | `status: FREEZE_COMPLETE`, `result_artifacts_absent_at_freeze: true` |
| 1 | Ordering enforced in code | `run_multileaf_formal.py:587,597-599` | `verify_pre_result_freeze()` before `mkdir`; refuses pre-existing `out_dir` |
| 1 | Manifest hash | `sha256sum …manifest.json` | `15639e1e6014…5163` = `.sha256` file = receipt:21 = `multileaf_formal_results.json:pre_result_manifest_sha256` |
| 1 | Frozen file hashes | `sha256sum` × 11 | runner `d99e9436…a4a4`, sample manifest `8e9121f2…1693`, test `b315f926…a22a`, trees `0931d952…bf25`, build `b60c3e5f…664c`, env `190474fd…5293`, diff `be2c1145…2ad8`, prereg `e489c32c…6934`, power plan `3a5778bd…5a62`, `multileaf_freeze.json` `7239feb6…fa34d`, tables `3e7e0568…64302` — **all match receipt lines 19–25, 56–64** |
| 1 | Git identity | `git log -1` | HEAD `e97340387888…b37e` = receipt:18 |
| 1 | Result chain | `sha256sum` × 4 vs `multileaf_run_receipt.json` | 4/4 match (`ae9cf1cf…`, `96adaa5a…`, `39c3a2c5…`, `37bb3601…`) |
| 2 | Confusion matrix (recomputed) | `grep -c` on `multileaf_prediction_rows.jsonl` (6 patterns) | M→M 72, R→R 72, N→N 72; all off-diagonals 0; total 216 |
| 2 | Macro-F1 / top-1 (recomputed) | hand arithmetic on above | F1 per class = 2·72/(2·72+0+0) = 1.0 → macro-F1 = **1.0**; top-1 = 216/216 = **1.0** |
| 2 | Stored `correct` flags | `grep -c '"correct": true/false'` | 216 / 0 — agrees with recomputed `predicted==true` |
| 2 | Response signatures (recomputed) | leaf-bit census, 12 `grep -c` | `parse.field.hit_rate` 72 (M only), `parse.table.regression` 72 (M only), `parse.reconcile.equations` 72 (N only), `qa.retrieval.source_required` 72 (R only); other 8 leaves **0 everywhere**; 3 disjoint constant signatures |
| 2 | Result classification (recomputed) | frozen rule `run_multileaf_formal.py:469` | contracts 216/216 PASS, leakage 5/5, p = 9.999e-05 < 0.05, `top1_ci_low` = 1.0 > 1/3 → **POSITIVE** = `multileaf_formal_results.json:result_status` |
| 2 | Baselines (recomputed) | hand arithmetic | always-M on 72/72/72 → top-1 = 1/3, macro-F1 = 1/6 = `0.16666666666666666` ✓ |
| 3 | Repeated measures | `grep -o cluster_id \| sort \| uniq -c` | 72 unique clusters, **every cluster exactly 3 rows**; 216 unique `sample_id` in both artifacts |
| 3 | Repeat structure | sample manifest | `repeat_within_cluster` 1/2/3 balanced 72 each; per-cluster injections differ by cell (e.g. `…-r0c2-1`, `…-r0c3-2`, `…-r0c0-3`) |
| 3 | LOCO fold unit | `run_multileaf_formal.py:406-408` | held-out unit = whole `cluster_id`; all 3 injections stay out of training together |
| 3 | Cluster-level inference | `:648-651`, `:663-666` | permutation permutes **cluster** labels; bootstrap resamples **clusters** |
| 3 | Leakage checks | `:375-384` + results `leakage_audit.detail` | sample_ids unique ✓, one stage per cluster ✓, 3 per cluster ✓, expected stage fixed ✓, M/N uid disjoint ✓ (48 distinct UUIDs) |
| 3 | Cross-stage id overlap | `grep -o source_uid / source_document_id` | M/N = 48 UUIDs, R = 24 md5 doc ids — no literal overlap; semantic R↔M/N overlap **not tested** (see F5) |
| 3 | Tie handling | `grep -o distance_margin` | min `1.4142135623730951` (√2), max `1.7320508075688772` (√3); zero zeros → `tie_count: 0`; tie→`__TIE__` scored incorrect (`:417-420`, test:37-44) |
| 3 | Frozen metric defs | prereg §6–§7 vs `:44-57` | nearest-centroid Euclidean LOCO, macro-F1 + top-1, chance 1/3, majority macro-F1 1/6 — all match |
| 4 | Permutation p (recomputed) | `grep -c '    1.0'` on null = **0**; `grep -o '[0-9]*\.[0-9]*' \| sort -g \| tail` = `0.5972222` | max(null) = 0.5972 < 1.0 → #{null ≥ obs} = 0 → p = (1+0)/10001 = **9.999000099990002e-05** ✓ both metrics; `wc -l` 20008 = 2×10000 + 8 structural ✓ |
| 4 | Bootstrap CI (recomputed) | `grep -c '    1.0,'` = 19998 (+2 unpunctuated), `grep -c '    0\.'` = 0, min decimal = `1.0` | all 20000 replicates = 1.0 → quantiles **[1.0, 1.0]** ✓ both metrics |
| 5 | Claim scoping | `multileaf_formal_results.json:claim_allowed/claim_forbidden` | allowed: "…**under the frozen M/R/N controlled injections**"; forbidden: "The hierarchy localizes failures." — identical in **all five** branches of `result_classification` (`:457-487`), not result-dependent |
| 7 | Contract tests | `tests/test_multileaf_formal_contract.py` | covers row-order (`:28-34`), tie-not-rescued (`:37-44`), macro-F1 denominators (`:47-52`); **no** coverage of leakage checks, permutation, bootstrap, or `check_*` response construction |
| 7 | R response construction | `run_multileaf_formal.py:295-301` | response bit **algebraically constant 1** for every R sample (see F1) |
| 8 | Packet scope | `stage_e_multileaf_result_packet_v1.md:24-31,78,137` | allowed claim scoped to controlled injections; forbids hierarchy localization **and** natural-task generalization; §5 discloses design-expected separability |

## Findings (by severity)

**F1 — HIGH (construct validity, not run-integrity): the response vector is a deterministic restatement of the injection label; perfect metrics are guaranteed by construction.**
- `run_multileaf_formal.py:295-301` (check_r): `baseline_bundle = sorted(expected | {"__DISTRACTOR_BLOCK__"})` forces `baseline_pass=True`; `injected_bundle = ["__DISTRACTOR_BLOCK__"]` forces `injected_pass=False`; therefore `response["qa.retrieval.source_required"] = int(True and not False) = 1` for **every** R sample regardless of sample content. The R bit carries zero sample-specific information.
- `run_multileaf_formal.py:248-258` (check_m): `baseline_hit = sum(token in canonical_set for token in canonical)/len(canonical)` is **identically 1.0** (each header token is trivially a member of the set built from itself). Both `parse.table.regression` and `parse.field.hit_rate` are set from the single predicate `mutated_hit < baseline_hit` (`:257-258`) — one predicate double-coded into two leaf dimensions. All 72 M injections are first-row header cells (`grep -c '"row": 0'` = 72 in the sample manifest), so the predicate is guaranteed to fire.
- `run_multileaf_formal.py:324-336` (check_n): the response bit is `int(original_pass and not mutated_pass)`, which is also a contract check (`:331-332`); a non-flipping injection aborts the run as INVALID rather than being scored. The bit cannot be 0 in any completed run.
- Consequence: stage → signature is a fixed codebook (M = {hit_rate, table.regression}, N = {reconcile}, R = {retrieval}), constant within stage, disjoint across stages. `predict_loco` then **must** achieve 1.0; the permutation null only rejects "the codebook is random"; the bootstrap CI `[1.0, 1.0]` is degenerate (every resample inherits a perfect labeling).

**F2 — MEDIUM: "four responsive leaves break the single-leaf degeneracy" over-reads the mechanism.** Effectively three response predicates exist, one of which (R) is a constant. The flat/hierarchy `affine_degeneracy_broken: true` and the packet's CONFIRMATORY "four leaves respond" (`stage_e_multileaf_result_packet_v1.md:51`) rest on the M double-coding at `:257-258`. Prereg §5's two-responsive-leaf requirement is met in letter, not in mechanism.

**F3 — LOW/MEDIUM: frozen-contract mismatch on permutation sidedness.** Prereg `stage_e_multileaf_preregistration_v1.md:126` specifies "a cluster-label permutation null at **two-sided** `alpha=.05`"; the runner computes a one-sided upper-tail p (`run_multileaf_formal.py:655`). Outcome-invariant here (two-sided p ≤ 2/10001 ≈ 2e-4 < 0.05), but it is a deviation from the frozen text.

**F4 — LOW: replicate counts are not freeze-gated.** Seeds are checked (`:591-594`) but `--permutations` / `--bootstraps` (`:832-833`) can silently deviate from the frozen 10000/10000. This run used 10000/10000 (`primary.permutation_replicates` / `bootstrap_replicates`), so no impact — but it is an unfrozen result-dependent knob.

**F5 — LOW: leakage audit omits cross-stage document overlap.** `:380-383` checks only `m_n_uid_disjoint`; R clusters are keyed by TAT-DQA `document_id` (md5) while M/N use drift_v0 table UUIDs, so a shared underlying document would be invisible to LOCO. Identifier spaces are disjoint in this freeze and the metric is saturated, so no numeric impact is possible in this run.

**F6 — LOW (definition nit, zero impact here):** `macro_f1` (`:391-395`) counts a `__TIE__` as FN for the true class only, never as FP — mild optimistic bias when ties occur. `tie_count = 0`, so zero effect.

**F7 — LOW (reporting hazard):** AUROC `1.0 / 1.0` is computed against `clean_scores = np.zeros(...)` (`:716`, `:726-727`) — vacuous by construction. The packet discloses the blocked operating point (`packet:97`); the bare number must not be cited standalone.

**F8 — INFO:** `tests/test_multileaf_formal_contract.py` (1996 bytes, 3 tests) is too thin to guard F1–F4; the tautologies in `check_r`/`check_m` are untested properties.

**Epistemic limits of this audit (not findings):** (a) freeze-before-result ordering rests on file mtimes, the hash-locked `result_artifacts_absent_at_freeze` assertion, and the runner's `out_dir` guard — not on an external timestamp authority; (b) leaf-bit census and null/replicate scans were performed with `grep`/`sort` counting rather than a full parser; the two repo validators (which do not import the runner) agree with every recomputed number.

## Strongest remaining failure scenario (reviewer attack that survives the perfect metrics)

**"You decoded your own injection label."** Every response bit is set by the evaluator from a predicate that is definitionally tied to which stage the sample was assigned to — and for stage R it is the constant 1 (`run_multileaf_formal.py:296-301`). Stage → signature is therefore a disjoint constant codebook; nearest-centroid LOCO with any reasonable distance reaches 1.0 for **any** sample of **any** quality, including samples whose real pipeline would fail for unrelated reasons. The permutation p = 1/10001 rejects only "the codebook was drawn at random," and the cluster bootstrap CI [1.0, 1.0] is a tautology resample, not uncertainty about generalization. A reviewer can therefore say: *the experiment shows that a variable the evaluator itself writes from the gold label contains the gold label; it does not show that any observed checkpoint-visibility trace from the production pipeline contains stage-localizing information, nor that a naturally occurring failure could be localized.* This attack is unaffected by the perfect confusion matrix, the p-value, the CI, the freeze receipt, or the leakage audit. It is bounded only by the claim's own scope clause ("under the frozen M/R/N controlled injections") and by the packet's §5 limitation sentence (`packet:78`).

## Does the result packet overclaim? (criterion 8)

**No material overclaim.** `docs/research/stage_e_multileaf_result_packet_v1.md` is scoped correctly: the allowed claim is restricted to the frozen controlled injections (`:24`); the forbidden list explicitly bars hierarchy localization and natural-task generalization (`:28-31`); §5 states plainly that "perfect separability is expected to a substantial degree because the controlled injections target distinct frozen direct leaves" and that the run "does not estimate natural-failure localization accuracy" (`:78`); §4 disclaims an independent semantic scorer (`:63`); the evidence map marks hierarchy localization `FORBIDDEN` and natural-task localization `FUTURE` (`:138-139`); the reviewer-attack matrix names the tautology attack (`:154`). Two residual soft spots: (i) grading "Controlled checkpoint signatures contain stage-localizing information" as `CONFIRMATORY` (`:104`, `:137`) is generous given F1 — the disclosure is present, but the grade outruns the mechanism for the R class specifically; (ii) `packet:51` ("four leaves respond") should read as "four leaf slots, three predicates, one of them constant" per F2.

## VERDICT: ACCEPTED

Acceptance covers **execution integrity, statistical recomputation, leakage/repeated-measure accounting, and claim scoping under the frozen design**. Every acceptance criterion (1–7) was independently verified against raw artifacts; the packet (8) does not materially overclaim.

Non-blocking items to carry forward (do not invalidate this run):

1. **F1/F2 must remain attached** wherever this result is cited: the confirmatory result is a property of the constructed observation surface. Any downstream sentence that drops "under the frozen M/R/N controlled injections" would become an overclaim immediately.
2. **F3**: implement two-sided permutation p (or amend the prereg in a new namespace) before any re-run.
3. **F4**: hard-fail `run_multileaf_formal.py` on `args.permutations != PERMUTATION_REPLICATES` / `args.bootstraps != BOOTSTRAP_REPLICATES`.
4. **F5**: extend the leakage audit to R `document_id` ↔ M/N `uid` provenance before any second dataflow.
5. **F8**: add contract tests asserting the `check_r`/`check_m` response construction (they would currently document the tautology as intended behavior — which is itself the honest record).

Because the verdict is ACCEPTED, no blocking evidence list is required. If a future revision removes the scope clause from the claim or upgrades natural-task generalization, this verdict does not carry over — that revision would need a new preregistration namespace and a new audit.
