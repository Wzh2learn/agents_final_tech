# Post-Run Independent Scientific Review

Review date: 2026-10-21

Scope: the frozen VersiCode observability run, its 32 raw request/response
pairs, `MODEL_LEDGER.json`, `PROBE_RESULT.json`, `RECOMPUTATION.json`, and the
settled budget event. No run artifact was edited and no model call was made.

## Verdict

**Arithmetic and evidence integrity: PASS.**

**Scientific claim: bounded observability result only.** The run supports
task-level statements about symbol migration on eight selected VersiCode
name-change families. It does not support behavioral correctness or a general
representation claim.

## Independent Integrity Checks

- All 32 raw request files exactly match the frozen request snapshot.
- All 32 response files reparse to one nonempty `{"code": string}` object with
  valid model identity and additive token usage.
- Independent AST recomputation reproduces every reported syntax, target-name,
  old-name, and symbol-migration outcome.
- Arm totals reproduce exactly:
  - BASE: 0/8 correct, 2,170 tokens.
  - PROSE_MAPPING: 8/8 correct, 2,316 tokens.
  - STRUCTURED_MAPPING: 7/8 correct, 2,305 tokens.
  - PROBE_EVIDENCE: 5/8 correct, 9,126 tokens.
- Token arithmetic is exact: `2,170 + 2,316 + 2,305 + 9,126 = 15,917`.
  Prompt tokens `13,735` plus completion tokens `2,182` also equal `15,917`.
- `MODEL_LEDGER.json`, `PROBE_RESULT.json`, `RECOMPUTATION.json`, and the
  budget event agree on 32 attempts, 32 physical generation calls, and 15,917
  accounting tokens.
- `RECOMPUTATION.json` source hashes match the current task, snapshot, ledger,
  and result files.
- Frozen and current task/spec/snapshot files match. The current runner differs
  from `run_frozen/run_probe.py` only by the post-run `verify` command and
  recomputation function; the executed `prepare/run` path is unchanged.

## Task-Level Comparisons

The independently recomputed symbol-migration matrix is:

| Task | BASE | PROSE | STRUCTURED | PROBE | Gold probe rank |
|---|---:|---:|---:|---:|---:|
| `old_to_new_1` | 0 | 1 | 1 | 1 | 1 |
| `old_to_new_261` | 0 | 1 | 1 | 1 | 1 |
| `old_to_new_748` | 0 | 1 | 1 | 1 | 1 |
| `old_to_new_3276` | 0 | 1 | 1 | 1 | 1 |
| `old_to_new_3517` | 0 | 1 | 1 | 1 | 2 |
| `old_to_new_15048` | 0 | 1 | 1 | 0 | not in top 8 |
| `old_to_new_20283` | 0 | 1 | 1 | 0 | not in top 8 |
| `old_to_new_20751` | 0 | 1 | 0 | 0 | not in top 8 |

Supported within this task set:

- PROSE versus BASE: 8 wins, 0 ties, 0 losses.
- STRUCTURED versus BASE: 7 wins, 1 tie, 0 losses.
- PROBE versus BASE: 5 wins, 3 ties, 0 losses.
- PROSE versus STRUCTURED: 1 win, 7 ties, 0 losses.
- PROSE versus PROBE: 3 wins, 5 ties, 0 losses.
- STRUCTURED versus PROBE: 2 wins, 6 ties, 0 losses.

The BASE comparisons support the bounded observation that explicitly supplying
the old-to-new mapping facts was associated with correct symbol migration on
7-8 tasks, while BASE succeeded on zero of eight. This is an information
comparison, not a pure representation comparison.

## Prose Versus Structured

The 8/8 versus 7/8 result **does not support a general representation claim**.

The arms receive the same mapping facts and differ in serialization, so this
is the cleanest representation contrast available. However, there is only one
discordant pair: `old_to_new_20751`. PROSE generated
`mean_absolute_error`, while STRUCTURED retained `mae`. With one discordance,
an exact paired sign test has two-sided `p = 1.0` (one-sided `p = 0.5`).

The defensible statement is only:

> In this frozen run, prose succeeded on one task where the structured
> representation did not.

It is not defensible to claim prose is generally easier, more reliable, or
superior to structured mapping. Repeated generations or substantially more
independent task families would be needed for that hypothesis.

## Probe Evidence

PROBE_EVIDENCE gives a useful but narrow bounded conclusion:

- It succeeds on 5/8 tasks without explicitly supplying the hidden target
  name.
- Its successes align exactly with target-symbol availability in the top
  candidates: gold rank 1 on four tasks and rank 2 on one task. It fails on
  all three tasks where the target is absent from the top eight.
- The deterministic top-name rule succeeds on 4/8; the model improves this to
  5/8 by handling the rank-2 case.
- It costs 9,126 tokens, or approximately `4.21x` BASE, `3.94x` PROSE, and
  `3.96x` STRUCTURED total tokens.
- It is worse than PROSE on three tasks and worse than STRUCTURED on two, with
  no task-level wins over either direct mapping arm.

Therefore probe evidence is useful as a bounded fallback or discoverability
diagnostic when the target API is not explicitly known. On this task set it is
dominated by direct mapping in both accuracy and token cost. It is not evidence
that large candidate inventories are an efficient general prompting strategy.

## Claims Not Supported

VersiCode supplies reference code but no behavioral execution oracle. The
metric checks syntax and AST name usage only. Therefore this run cannot claim:

- semantic equivalence, correct arguments, correct output, or runnable migrated
  code;
- production migration validity or natural production drift;
- general model capability;
- superiority of prose over structured representations;
- robustness across argument, output, async, or non-name-change migrations;
- population-level effects from eight selected name-change families;
- uncertainty or stability across repeated samples;
- efficient use of probe evidence relative to direct mapping.

Even `symbol_migration_correct=true` means only that the hidden target name is
used and the old name is absent in syntactically valid generated code.

## Next Step

**Move the next scientific experiment to PyMigBench real-commit tests.**

Select migrations whose parent and target commits have deterministic runnable
repository tests, freeze both environments, and compare information conditions
against behavioral before/after outcomes. This adds the missing oracle and
moves beyond eight name-change families. Keep the current VersiCode run as a
bounded observability pilot, not as behavioral evidence.

No model or network calls were made during this review.
