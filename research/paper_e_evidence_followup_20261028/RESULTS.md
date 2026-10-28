# Paper E six-system evidence audit — 2026-10-28

## Status and protocol

Post-hoc exploratory reanalysis, not preregistered or independent confirmation: the previous five-system BEIR analysis and the BGE versus BM25 result were already known. The six systems, 15 unordered comparisons per dataset, four metric conditions, and two-sided test were specified in `audit_six.py` before this run; there is no independent preregistration timestamp. Separate Holm families are used for each dataset and each metric condition; there is no correction across datasets or across the four conditions. Do not call this a prospective decision or human-user study.

Uses existing BEIR SciFact and NFCorpus corpora, qrels and test queries, the previous BGE-small-en-v1.5 top-100 run, and regenerates TF-IDF plus four BM25 runs. Graded and binary nDCG at 10 and 100 vary one contract at a time; `trec_eval` uses raw qrel grade as gain. No MAP or score rounding analysis is claimed. Ties for lexical systems are diagnosed by comparing doc-ID ascending and descending rankings. The BGE input retains top-100 IDs, not original dense similarity scores: dense tie frequency and 10/11 boundary ties are **not measurable** here and no dense tie claim is made.

Every pair uses two-sided paired sign-flip on the mean difference, 20,000 permutations, RNG seed 20261028, plus-one p = (1+number >= observed)/(20001). Holm adjusts the 15 p-values in each family. Bootstrap is separate, 2,000 query-level resamples, seed 20261028. Full 15-pair tables, raw per-query metric values, and top-100 IDs are in `six_system_result.json`. The randomization p resolution is 1/20001 ≈ 0.00005; Monte Carlo variability matters especially for conclusions near 0.05.

## Main decision example (graded nDCG@10)

| Comparison and dataset | BGE − BM25(1.2,.75) | 95% paired bootstrap CI, unadjusted | sign-flip p | Holm p (15 pairs) |
|---|---:|---:|---:|---:|
| SciFact, 300 queries | +0.05049 | [0.01368, 0.08913] | 0.00650 | 0.06500 |
| NFCorpus, 323 queries | +0.03759 | [0.01540, 0.06083] | 0.00125 | 0.01500 |

Example: before considering multiplicity, a positive paired CI would support a one-comparison claim. Under the specified 15-comparison, two-sided sign-flip family, SciFact's corresponding claim is not supported at 0.05 whereas NFCorpus's is supported. This is *not* evidence systems are equal, not evidence of a human changing a choice, and it does not attribute differing bootstrap/sign-flip outcomes solely to Holm. Since the SciFact adjusted p is close to 0.05, Monte Carlo uncertainty must be considered. For the unadjusted p≈0.0065, an approximate 95% binomial MC margin is 0.0011 before adjustment; it is not a confidence interval for the scientific effect.

On graded nDCG@10, unadjusted sign-flip supports 8/15 pairs and Holm supports 4/15 on SciFact; corresponding figures are 9/15 and 6/15 on NFCorpus. These are the same test, unlike a comparison of bootstrap counts to Holm-adjusted sign flips. With six systems, on NFCorpus at k=10, TF-IDF (0.30522) is below BM25(1.2,.75) (0.30620) under graded gain, but above it under binary gain (0.30652 vs 0.30575). Both are descriptive close scores; this change does not establish either superiority nor assert that the binary contract is inherently invalid. BGE ranks first by mean under the four examined metric conditions on both datasets; this single post-hoc model and two BEIR subsets do not establish general robustness.

### Higher-precision Monte Carlo sensitivity check

`mc_recheck.py` independently recomputed all 15 pairs in each dataset for graded nDCG@10 from the saved per-query arrays, using 200,000 sign flips per pair, seed 20261029 and 1,000-draw batches. It uses absolute signed-sum magnitude for a two-sided test, plus-one correction, and a separate Holm implementation; the direction of the saved difference is BM25 minus BGE. Two-sided sign flips require within-query exchangeability under a sharp null or appropriate symmetry of paired differences, and query independence is assumed for the resulting inference. The recheck is post-hoc numerical sensitivity, not an independent dataset or validation of these assumptions.

| Dataset | Old p / Holm (20k) | Recheck p / Holm (200k) | Approximate unadjusted MC SE |
|---|---|---|---|
| SciFact | 0.00650 / 0.06500 | 0.006410 / 0.066000 | 0.000178 |
| NFCorpus | 0.001250 / 0.01500 | 0.001295 / 0.015540 | 0.000080 |

The BGE/BM25 significance classification and all 30 pair classifications match the original run; the total significant pairs remain 4/15 and 6/15. MC standard errors above are approximate for the unadjusted simulated p, not confidence intervals for effects or adjusted p-values. Full per-pair exceedances and adjusted p values are in `mc_recheck.json`. GB10 elapsed 3.06s with single-thread BLAS; no generation or training. Script SHA-256 `ec44cc39f6aae804185c59fc5ae857fd07c3425b63cbacff1e38f88695d5bf47`; JSON SHA-256 `7038261675710b7b60b4d2b8d00450efefbd1d50839194bdfb4294e61aa54b5c`.

## Checks and provenance

- Matching query sets: 300/300 SciFact and 323/323 NFCorpus; qrels, corpus and query SHA-256 match the previously recorded dense inputs. Regenerated BM25(1.2,.75) top-100 exactly matches dense input's stored BM25 top-100 for all 623 queries.
- Official `trec_eval` run on converted TREC qrels and stored runs: graded nDCG@10 and @100 for all six systems and 623 queries, 7,476 per-query values; max absolute differences 0.00004972 / 0.00004997 respectively, within four-decimal printing precision. Verifies metrics for supplied ranks, not tie policy or statistical test. The initial invocation used BEIR TSV as a TREC qrels file and failed; it was corrected using an explicit qrels conversion before the successful run. Binary nDCG was not checked against the binary here.
- `beir_audit.py` pre-existing hand-calculated metric tests pass; its GB10 and local file SHA-256 is `4a48fbf69a62d14b972916760c5a0809ad2408eda97766d52eac580a300b410b`. GB10 trec binary SHA-256 `bb156b1d04806002dbe0dfd04db0836449145ff3bf97684391773c7ec2db25f5`.
- Script SHA-256 `505351d2a320ab97381d0da13d4e493de8806c8aed3a1e598d6eb66047a47012`; output SHA-256 `b4596b01db7557570f644fcecf0325af6a18261637e47b6c9e112480fb87acdc`. Input dense SHA stored in result JSON. The six corpus/query/qrel hashes are validated against the input dense manifest at runtime.
- GB10 command: `python3 /tmp/papere_audit_six_20261028.py /tmp/papere_audit_six_result_20261028.json`; previous dense input path and existing audit module locations are explicit in the script. CPU successful elapsed 13.72 s; no generation, judge, API, or training; the first failed run consumed extra CPU.

## Human reference feasibility

The supplied manuscript records 13 OCR-like items and 28 mutation-level semantic boundary items. This work did not identify their record-level join keys or independently establish overlap; do **not** claim 41 unique samples. Freeze task IDs and exact original/injected headers, document context and contract first; two independent annotators should record referential equivalence, disagreements and adjudication separately from actual downstream harm. Human consensus is not proof of deployed harmlessness. No human annotation was performed.

## Next independent checks

Have a second reviewer inspect sign-flip/Holm code and full results, qrel conversion and dense ranking provenance, then verify whether the 15-pair family addresses the intended author claim. Do not replace previous frozen results: this six-system family is distinct from the previous five-system, ten-pair family.
