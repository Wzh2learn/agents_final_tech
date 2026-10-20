# Reuse Opportunity Goal

Determine whether the restricted tool task has useful real-experience reuse headroom, using a frozen B0-first diagnostic and a reproducible continue/stop decision.

## Done when

1. Trajectory classification separately records completeness, reference match, tool success, answer/tool consistency, and post-feedback action change; complete failed/refused trajectories remain complete.
2. Real historical contexts contain only approved historical task, actual operation, tool return, actual answer, and feedback. No invented lessons or corrections.
3. Synthetic fixtures validate success, failure, refusal, and missing-record classifications and never enter the research pool.
4. A targeted independent review accepts the definitions and implementation before protocol freeze.
5. B0 runs on all 16 future tasks within 32 requests and is judged only by the pre-frozen branch gates.
6. R/C/H run only if the B0 gate permits; otherwise the stop branch is completed without additional generation.
7. `RESEARCH_DECISION.md` reports actual results, complete ledger, reuse headroom, what H adds over B0/R/C, and a continue/stop/undetermined judgment.

## Never touch

- Old `PILOT_STOP_U_E_IDENTICAL`, old raw runs, previous manifests/protocols, model/runtime/output contract, or historical experience evidence.
- No retries, sample additions, task changes, prompt tuning after B0, training, memory write-back, source switch, or new model.

## Stop if

- B0 is all-success, limited-headroom, or technically invalid under the frozen gates.
- Any identity/reference/isolation/tool-chain failure occurs.
- R/C/H content or selection would change after B0 results are known.
- The 128-request diagnostic or overall 228/2.45M budget would be exceeded.
- Any generation remains after 2026-10-19 22:00 Asia/Shanghai.
