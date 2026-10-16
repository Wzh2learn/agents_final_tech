# tq4_calibration_v1 - TQ-4 calibration package (offline preparation)

> Round: 2026-10-16 adjudication (D1 revised approval, D2 folded into next round, D3 deferred).
> Status: PREPARED_AWAITING_AUTHORIZATION_V2 (no TQ-4 run has executed; zero model calls this round).

## Contents

- `scorer_v2/` - fixed scorer (percent explicit-unit conversion; no multi-number cherry-pick;
  list full-set equality; no guessing) + regression suite (18 checks; 8 v1-v2 flips).
- `evidence_protocol/EVIDENCE_PROTOCOL_v2.md` - typed evidence (cell/paragraph), 0-based, paragraph uid,
  legality vs support recorded separately.
- `rescoring/` - re-score of the 12 saved TQ-3 outputs with v2 (0 status changes; all-12 schema-illegal
  in the v2 legality view) + interpretation corrections report.
- `panel_v2/` - frozen materials: 4 new natural tasks (N1-N4, selection spec + log) and 12 manual
  candidates (Q02/Q03/Q04 x correct/incorrect x legal/illegal evidence).
- `run_card_v2/` - run card v2, prompt templates v2, authorization items v2.
- `reviews/` - focused independent review (to be recorded).
- `runs/` - future run outputs (gitignored, local only).
