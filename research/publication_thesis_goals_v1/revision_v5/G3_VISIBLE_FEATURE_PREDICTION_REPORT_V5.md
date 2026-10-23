# G3 Visible-Feature Learnability Diagnostic

Date: 2026-10-23

Status: `WEAR_SIGNAL_NOT_MODEL_METHOD`

## Question

Can the 43 useful rank-4/5 expansions among 400 STALE items be predicted from
features visible before expansion? This is separate from G2 state-to-action
transfer: the output is only `KEEP/EXPAND`.

## Frozen Setup

- Features: query token coverage, rank-3/rank-1 score ratio, past cue, update
  cue, score-tail flag and temporal-gap flag.
- Models: standard-scaled class-balanced logistic regression and depth-2
  class-balanced decision tree.
- Validation: five repeated five-fold outer splits with a three-fold inner
  cost-matched threshold. The threshold allows at most 10% EXPAND decisions.
- Hidden useful-expansion labels are evaluation references only and never enter
  model inputs.

## Results

| Strategy | Expand | Useful found | Precision | Recall | Expansion context cost |
|---|---:|---:|---:|---:|---:|
| Never expand | 0 | 0/43 | 0.000 | 0.000 | 0 chars |
| Always expand top-5 | 400 | 43/43 | 0.108 | 1.000 | 11,850,080 chars |
| Existing visible rule | 9 | 1/43 | 0.111 | 0.023 | 261,221 chars |
| Logistic regression | 40 | 2/43 | 0.050 | 0.047 | 1,203,502 chars |
| Depth-2 tree | 40 | 5/43 | 0.125 | 0.116 | 1,194,603 chars |

The depth-2 tree is the only model above the visible rule in recall and
precision at the matched 10% expansion budget. Its five true positives are
still small, and its cost is about 4.6x the visible rule. The logistic model is
worse than the transparent rule. Useful and non-useful score means are close or
reversed, so this is a weak signal rather than a reliable predictor.

## Decision

`KEEP_G3_AS_INDEPENDENT_CANDIDATE / STOP_VISIBLE_RULE / DO_NOT_CLAIM_LEARNING`.

The oracle result still shows useful headroom: 43 useful expansions can be
selected with 37,292 mean context chars versus 64,338 for always-expand. The
depth-2 result says some visible signal may exist, but not enough for a
deployable policy. The next G3 gate is a frozen held-out evaluation with
feature provenance and cost-aware utility, not another unbounded model grid.

This candidate remains distinct from G2 because it chooses additional evidence,
not how a recovered state maps to an action.
