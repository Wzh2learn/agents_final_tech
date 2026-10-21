# FinRank External Audit Run Card

Status: `DETERMINISTIC_OFFLINE_ONLY`

The pinned object is FinRank commit
`916dc27e77b90e294ea1b3a2cc5b0abcf07392d1` with arXiv record
`2608.07400v1`. The vendored upstream tree is evidence, not project code.

## Fixed Audit Question

How sensitive are FinRank's absolute pairwise metrics, hard-versus-random
contrast, and metadata-filter interpretation to:

1. counting exact score ties for the positive;
2. gold-first tie ordering in in-record MRR/nDCG;
3. corpus-order tie ordering in global ranking metrics; and
4. first-occurrence text deduplication and metadata assignment?

The author contract already discloses tie-positive pairwise scoring, the
curated-pool limitation, cross-record hard-negative overlaps, and first-
occurrence metadata loss. An observed sensitivity narrows interpretation; it
is not automatically an undisclosed implementation defect.

## Scope

- Included: official data, code, released outputs, paper text, deterministic
  TF-IDF/BM25 replay, synthetic fixtures, exact-tie and source-identity
  sensitivity on all 1,185 records.
- Excluded: new model inference, neural reruns, judge calls, training, edits to
  frozen project results, and claims about generator performance.
- Known source-informed probes: tie-positive pairwise scoring and
  first-occurrence metadata assignment were visible before application.
- V1 application object: full released records and seed-42 sampled random
  negatives, evaluated after synthetic fixtures and preregistration. V2 is a
  post-hoc identity-corrected reanalysis of the same object.

## Commands

```powershell
python finrank_audit.py manifest
python finrank_audit.py fixtures
```

`PRE_REGISTRATION.json` is frozen after fixtures and before the v1 application
outputs. Its bound audit-code hash identifies the v1 implementation.

```powershell
python vendor/FinRank/baselines/validate_release.py --data vendor/FinRank/FinRank.jsonl
python vendor/FinRank/baselines/run_baselines.py --data vendor/FinRank/FinRank.jsonl --out reproduced_official/skip_neural --skip-neural
python finrank_audit.py apply
```

All outputs are regenerated from the pinned inputs. Any request that invokes a
model endpoint is outside this run card.

## Execution Note

The preregistered v1 implementation compared cross-record role overlap on raw
exact strings, while the FinRank contamination audit uses canonical
`text_sha1` / trimmed identity and `hn_taxonomy.json`. V1 is therefore the
preregistered application, but its source-identity result is invalid for the
author's contamination question. V2 reports raw, trimmed, SHA-1 and
official-taxonomy counts separately. V2 is a post-hoc identity correction and
deterministic reanalysis, not a complete frozen application. The thresholds and
questions did not change. Tie-related v1/v2 values are identical, but v2 was
produced by changed code and is not retroactively preregistered.
