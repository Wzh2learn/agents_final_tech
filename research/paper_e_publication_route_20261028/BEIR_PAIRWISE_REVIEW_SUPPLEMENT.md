# BEIR lexical pairwise comparisons: private review supplement

Post-hoc calculation using the saved 2,000-draw five-system analysis and the later 200,000-draw six-system sensitivity recheck. The latter regenerates lexical query scores and is not an independent dataset. Differences and intervals are in the direction A minus B for graded nDCG@10.

Bootstrap intervals are unadjusted query-level 95% intervals; both p columns use two-sided sign flips with Holm over the ten lexical pairs, separately by dataset. These are different inference procedures. Non-significance does not establish equality; numerical precision does not verify sign-flip or query-independence assumptions.

## scifact (300 queries)

| A | B | Mean A − B | Unadjusted bootstrap 95% CI | Holm p, 2,000 draws | Holm p, 200,000 draws |
| --- | --- | ---: | --- | ---: | ---: |
| BM25_09_04 | BM25_12_075 | -0.00114 | [-0.01060, 0.00854] | 1.00000 | 1.00000 |
| BM25_09_04 | BM25_05_03 | +0.00589 | [-0.00359, 0.01579] | 1.00000 | 1.00000 |
| BM25_09_04 | BM25_15_06 | -0.00518 | [-0.01402, 0.00411] | 1.00000 | 1.00000 |
| BM25_09_04 | TFIDF | +0.02816 | [0.00466, 0.05266] | 0.14393 | 0.13364 |
| BM25_12_075 | BM25_05_03 | +0.00703 | [-0.00578, 0.01999] | 1.00000 | 1.00000 |
| BM25_12_075 | BM25_15_06 | -0.00404 | [-0.01131, 0.00234] | 1.00000 | 1.00000 |
| BM25_12_075 | TFIDF | +0.02930 | [0.00924, 0.04956] | 0.04498 | 0.03609 |
| BM25_05_03 | BM25_15_06 | -0.01107 | [-0.02413, 0.00301] | 0.78261 | 0.73938 |
| BM25_05_03 | TFIDF | +0.02227 | [-0.00194, 0.04805] | 0.55972 | 0.54075 |
| BM25_15_06 | TFIDF | +0.03334 | [0.01279, 0.05526] | 0.01000 | 0.01795 |

## nfcorpus (323 queries)

| A | B | Mean A − B | Unadjusted bootstrap 95% CI | Holm p, 2,000 draws | Holm p, 200,000 draws |
| --- | --- | ---: | --- | ---: | ---: |
| BM25_09_04 | BM25_12_075 | -0.00166 | [-0.00506, 0.00185] | 1.00000 | 1.00000 |
| BM25_09_04 | BM25_05_03 | +0.00348 | [0.00045, 0.00683] | 0.24788 | 0.25268 |
| BM25_09_04 | BM25_15_06 | -0.00469 | [-0.00899, -0.00070] | 0.22039 | 0.21618 |
| BM25_09_04 | TFIDF | -0.00068 | [-0.00806, 0.00650] | 1.00000 | 1.00000 |
| BM25_12_075 | BM25_05_03 | +0.00514 | [0.00037, 0.00974] | 0.24788 | 0.25268 |
| BM25_12_075 | BM25_15_06 | -0.00303 | [-0.00651, 0.00016] | 0.46477 | 0.44547 |
| BM25_12_075 | TFIDF | +0.00097 | [-0.00652, 0.00785] | 1.00000 | 1.00000 |
| BM25_05_03 | BM25_15_06 | -0.00817 | [-0.01378, -0.00287] | 0.02999 | 0.03715 |
| BM25_05_03 | TFIDF | -0.00417 | [-0.01288, 0.00411] | 1.00000 | 1.00000 |
| BM25_15_06 | TFIDF | +0.00400 | [-0.00283, 0.01064] | 1.00000 | 1.00000 |

The three supported pair classifications remain the same in the higher-draw sensitivity check. The source JSONs, code and hashes are listed in `lexical_holm_200k_sensitivity.json`; third-party dataset redistribution and anonymized artifact hosting remain subject to author approval and license review.
