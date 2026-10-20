# Paper E External Audit: FinRank

Status: `POST_HOC_CORRECTED_DETERMINISTIC_REANALYSIS_COMPLETE`

## Executive Ruling

**Result: `NARROWER_CONTRACT_STABLE_WITH_REPRODUCIBILITY_CAVEAT`.**

The corrected deterministic FinRank reanalysis does not overturn the paper's main
hard-versus-random conclusion. Exact tie handling materially changes absolute
random-negative accuracy, but moves the hard-versus-random gap by only 0.34-0.36
percentage points and preserves its direction. The disclosed source-identity
limitations reproduce exactly.

This result is not a complete frozen application. The question, object and
decision thresholds were preregistered, but the first implementation used the
wrong source-identity normalization. The corrected source-identity analysis and
the v2 rerun occurred after that failure was visible. Tie metrics are identical
between v1 and v2, but under the corrected implementation they are evidence from
a preregistered question with a post-hoc corrected implementation, not a
fully frozen confirmatory application.

One narrower interpretation changes: the release is not bit-for-bit or
value-for-value reproducible in the declared pinned deterministic environment
on this platform. Global and metadata-filtered metrics differ from the bundled
result JSON by as much as 0.19 and 0.16 points, although in-record MRR/nDCG and
pairwise results reproduce exactly. Therefore the paper's phrase "exactly
reproducible from these artifacts" is stronger than this audit supports without
a locked platform, complete transitive environment, stored score matrices, or
tolerance-defined reproducibility.

This is a useful second implementation-level measurement case for Paper E:
observation, ranking, score identity and report identity must share the same
causally updated measurement object. It is not evidence of a general FinRank
failure and does not change model selection or the qualitative conclusion.

## Object and Identity

- Official repository: `https://github.com/datanxt/FinRank`
- Fixed revision: `916dc27e77b90e294ea1b3a2cc5b0abcf07392d1`
- Paper: arXiv `2608.07400v1`
- Dataset: `FinRank.jsonl`, SHA-256
  `B763EF4D58706370BD32F828B94852D2AA19F5227CB603481DD230D8121360AC`
- Released results: `baselines/results/results.json`, SHA-256
  `60517716D3F8DBD5D6D435991764E39988EF7DF90FACF92B9185AACC0BC1F411`
- License: CC BY-NC 4.0
- Release gate: `validated 1185 records: 0 violation(s)`

The complete hashes are in `paper_e_audit/outputs/SOURCE_MANIFEST.json`.
Downloaded public material is below 200 MB. No model, judge, training, or paid
research API call was made.

## Evidence Status

The audit distinguishes five evidence classes:

1. **Known source-informed probes:** tie-positive pairwise scoring and
   first-occurrence metadata assignment were visible in source/paper before the
   application.
2. **Development fixtures:** synthetic positive, negative, zero-score tie,
   all-tie in-record, candidate-order, and shared-text identity cases.
3. **Preregistered v1 application:** pair-level TF-IDF/BM25 ties, seed-42
   random overlap, raw-exact source identity, and ranking-order sensitivity over
   all 1,185 records. This is the only run bound to the exact audit-code hash in
   `paper_e_audit/PRE_REGISTRATION.json`. Its source-identity comparison was
   wrong because it used raw exact strings instead of FinRank's canonical
   trimmed/`text_sha1` identity.
4. **Post-hoc v2 correction:** the source-identity implementation was corrected
   to the author's canonical identity and all derived outputs were recomputed.
   Source-identity findings in v2 are a deterministic post-hoc reanalysis. Tie,
   gap, in-record and global-order values are numerically identical in v1/v2,
   but v2 was produced by changed code and must not be represented as the full
   frozen application.
5. **Post-application diagnosis:** explanation of the non-exact result
   reproduction. This did not change the frozen thresholds, but its cause
   remains unresolved.

The application is not blind. Official aggregate outputs and author-disclosed
limitations were known; full pair-level outcomes were not computed before the
freeze.

## Audited Dataflow

1. **Question and source identity:** each record carries question, canonical
   labels, filing metadata, gold passages, and hard negatives with originating
   ticker/year/document type.
2. **Candidate construction:** raw passage strings are globally deduplicated
   in first-occurrence order; the first occurrence supplies pooled-corpus
   metadata (`run_baselines.py:41-59`).
3. **Scoring:** TF-IDF, BM25 and neural systems score question-passage text.
   Source identity is not part of the score (`run_baselines.py:132-177`).
4. **Global ranking:** default `numpy.argsort` determines equal-score order;
   Recall/MRR/nDCG consume the resulting ranking (`run_baselines.py:62-73,
   177-196`).
5. **In-record ranking:** gold scores are concatenated before negative scores,
   then stable sorting gives gold precedence within exact ties
   (`run_baselines.py:76-87`).
6. **Pairwise scoring:** `score(gold) >= score(negative)` counts every tie for
   gold (`run_baselines.py:90-101`). The paper explicitly discloses this rule.
7. **Random control:** seed 42 samples one random corpus entry per hard
   negative, excluding only the record's own gold; sampled entries may overlap
   hard negatives (`run_baselines.py:213-217`).
8. **Metadata filter:** a text deduplicated to its first source identity can be
   removed from a later source-matched candidate pool (`run_baselines.py:275-307`).
9. **Aggregation:** per-record metrics are macro-averaged over records
   (`run_baselines.py:104-105`).
10. **Paper claims:** retrieval/reranking results are presented as a curated
    passage-ranking stress test, not full-document retrieval or answer
    generation. The authors already state the source-attribution and annotation
    limitations.

## Results: Preregistered Questions, Post-Hoc Corrected Implementation

The values below come from v2. The v1 preregistered implementation produced the
same tie-related values; only the source-identity analysis changed. Thresholds
remain frozen, but the implementation is not fully frozen.

### Exact ties in pairwise accuracy

| Model | Regime | Ties-positive | Strict win | Ties half |
|---|---:|---:|---:|---:|
| TF-IDF | hard | 77.756 | 77.030 | 77.393 |
| TF-IDF | random | 91.935 | 90.850 | 91.393 |
| BM25 | hard | 74.780 | 74.094 | 74.437 |
| BM25 | random | 87.789 | 86.760 | 87.275 |

TF-IDF has 91 hard-pair ties and 135 random-pair ties; BM25 has 83 and 125.
Changing ties-positive to strict-win moves random accuracy by 1.084 points for
TF-IDF and 1.029 for BM25, crossing the preregistered 1-point materiality
threshold under the post-hoc corrected implementation.

However, the reported hardness gap is stable:

| Model | Ties-positive gap | Strict gap | Half-credit gap |
|---|---:|---:|---:|
| TF-IDF | 14.179 | 13.821 | 14.000 |
| BM25 | 13.009 | 12.666 | 12.838 |

The gap changes by only 0.358 and 0.343 points and never reverses. Thus the
tie rule matters for absolute calibration but not for the paper's qualitative
claim that curated negatives are harder than the sampled random negatives.

### Tie ordering

- Gold-first versus negative-first in-record ordering changes MRR by 0.108
  (TF-IDF) and 0.101 (BM25) points.
- The corresponding nDCG@5 changes are 0.573 and 0.572 points.
- Forward versus reverse corpus order changes global MRR by at most 0.287
  points and Recall@10 by at most 0.141 points, below the fixed 0.5-point
  threshold.
- The all-tie fixture is diagnostic: pairwise accuracy is 100%, and gold-first
  in-record MRR/nDCG are both 1.0. Negative-first ordering drops MRR to 1/3 and
  nDCG to 0.5. Equivalent candidates are therefore not metric-neutral when
  scores carry no information.

### Source identity

- The author's canonical contamination identity reproduces exactly:
  **442 hard negatives across 305 records** overlap another record's gold.
- Raw exact string matching finds only 293/220; whitespace-trimmed and
  `text_sha1` matching both produce 442/305. The earlier 293/220 diagnostic was
  a superseded wrong identity rule, not a contradiction in FinRank.
- First-occurrence metadata filtering reproduces **33 records losing at least
  one gold and 2 losing all gold**, 92.8746% hard negatives eliminated, and
  172.9527 mean candidates.
- Forty-six exact raw texts carry more than one source identity. The score uses
  text only, while metadata uses the first occurrence. This is consistent with
  the paper's disclosed limitation, not hidden source binding.
- The seed-42 random draw equals a curated hard negative in 5 of 11,790 draws
  across 5 records. This is allowed by the stated sampling contract and too
  small to explain the 13-14 point gap.

### Release identity and reproduction

- Paper, dataset and released result JSON all specify a 5,230-entry raw-text
  pooled corpus. The repository README says 5,270 in one sentence. This is a
  documentation inconsistency; 5,230 recomputes from the data.
- Running the official `run_baselines.py --skip-neural` with the declared pins
  (`numpy 2.5.1`, `scikit-learn 1.9.0`, `rank-bm25 0.2.2`) reproduces
  in-record MRR/nDCG and all pairwise metrics exactly.
- It does not reproduce global or metadata-filtered values exactly:
  TF-IDF global deltas range from -0.07 to +0.19 points; BM25 from -0.12 to
  +0.13; metadata-filtered metrics from -0.16 to -0.11.
- A second run under Python 3.9 / numpy 1.26 / scikit-learn 1.5.2 gives
  different but still small global deltas (up to 0.47 for metadata MRR).
- The result pattern is consistent with unstable tied-ranking order and/or a
  result file generated under a not-fully-locked platform or transitive
  environment. This audit cannot distinguish those causes without the original
  score cache or execution environment.

## Interpretation Against the Paper

### Stable under the narrow author contract

- FinRank does not claim full-document retrieval; it explicitly calls the pool
  a curated passage-ranking stress test.
- FinRank does not claim generator performance; answer generation is left to
  future work.
- Tie-positive pairwise scoring is explicitly documented in the paper and code.
- First-occurrence metadata loss and 442 cross-record overlaps are explicitly
  disclosed and quantified.
- The hard-negative conclusion survives reasonable tie alternatives.

Therefore it would be incorrect to present the tie/source probes as discovery
of undisclosed defects or as a correction of the benchmark's main conclusion.

### Changed or narrowed

1. Absolute pairwise accuracy is tie-policy sensitive; it should not be read as
   an unqualified discrimination probability when zero-information ties are
   frequent.
2. In-record nDCG is slightly tie-order sensitive because gold precedes
   negatives on equal scores.
3. "Exactly reproducible from these artifacts" is not supported at raw
   precision by this external execution, even with the declared top-level
   package pins. Reproducibility claims should specify platform/transitive
   environment and numerical tolerance, or ship score matrices/rankings.
4. The README's 5,270 entry count should be corrected to 5,230.

## Consequences for Paper E

This case provides a real implementation-level measurement audit, but it does
not close the requirement for a fully preregistered independent application:

- It follows one real third-party identity, candidate pool, score, ranking,
  aggregation, and published claim chain.
- It freezes a proposition and thresholds before pair-level outcomes, but the
  v2 identity correction breaks full implementation freezing.
- It includes positive/negative fixtures and a full deterministic v2
  reanalysis, with v1 retained as the preregistered wrong-identity run.
- It separates a material absolute-score sensitivity from a stable qualitative
  decision.
- It yields a concrete external action: report tie sensitivity and exact
  reproduction tolerance, and ship ranking identities if "exact" is claimed.

The strongest defensible Paper E contribution is no longer merely "a checklist
helped interpretation." It is:

> A reproducible measurement audit can separate score-contract sensitivity from
> decision stability in a real evidence-ranking benchmark and expose a residual
> reproducibility gap consistent with tie-order or environment drift, whose
> cause remains unresolved, without changing the benchmark's qualitative
> hard-negative conclusion.

This still does not validate a universal audit method. Because v2 is a post-hoc
identity correction, it supports revising Paper E as a two-case
measurement-audit paper with bounded transfer claims, while retaining the need
for a genuinely frozen independent application before stronger validation
language.

## Negative Results and Limits

- No evidence was found that FinRank overclaims answer-generation quality.
- No hard-negative hardness reversal was found under strict or half-credit ties.
- No source-identity contradiction was found after using the author's canonical
  identity.
- The v2 corrected implementation was not frozen before application and cannot
  serve as the missing prospective independent validation.
- The audit did not rerun neural baselines and cannot establish exact
  reproducibility for those reported rows.
- AI analysis is not human semantic gold, blind review, or author adjudication.
- The exact cause of the residual global metric drift is unresolved.

## Reproducible Artifacts

- `paper_e_audit/finrank_audit.py`
- `paper_e_audit/PRE_REGISTRATION.json`
- `paper_e_audit/PRE_REGISTRATION_PROVENANCE.md`
- `paper_e_audit/RUN_CARD.md`
- `paper_e_audit/outputs/FIXTURE_RESULTS.json`
- `paper_e_audit/outputs/APPLICATION_RESULTS.json` (v2 post-hoc corrected)
- `paper_e_audit/outputs/APPLICATION_RECORDS.jsonl` (v2 post-hoc corrected)
- `paper_e_audit/outputs/SOURCE_MANIFEST.json`
- `paper_e_audit/reproduced_official/exact_pinned/results.json`
- `paper_e_audit/reproduced_official/exact_pinned/score_cache.npz`

The preregistered wrong-identity v1 application is preserved under
`outputs/*_v1_raw_text_overlap.*`. No raw application result, frozen manuscript,
old result, raw response, or vendored upstream file was modified.
