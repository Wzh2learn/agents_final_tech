# Loop A Return

- Task ID: `finqa-executor-contract-a-20261019`
- Status: `EXECUTOR_FEASIBILITY_CONDITIONAL`
- Scientific outputs: 0
- Model/judge/API/database/training/service calls: 0
- Staged denominator: 7,134
- Terminal execution matches: 7,134 / 7,134
- Qualifying clean-replay records: 0 / 7,134
- Unresolved records: 7,134 / 7,134
- Unsupported records: 0
- Mismatch records: 0
- Non-deterministic records: 0

## Why conditional

The pinned official evaluator proves terminal execution against `qa.exe_ans`.
All 7,134 terminal values replay exactly. The pinned source does not prove how raw
intermediate execution values are rendered into `qa.steps[].res`, how formatted
`qa.answer` is derived, or how normalized dataset operator variants are interpreted.
Those rules are left `UNVERIFIED`, so no record can be admitted as fully clean under
the required every-step-plus-terminal comparison.

The clean-replay artifact reports all unresolved record IDs under:

- `STEP_RES_RENDERING_UNVERIFIED` — 7,134 records;
- `DISPLAY_ANSWER_DERIVATION_UNVERIFIED` — 7,134 records.

For transparency only, 5,319 step comparisons across 4,751 records differ under a
clearly labelled non-contract numeric diagnostic. Those diagnostics are not used as
scientific mismatches and do not shrink or enlarge the 7,134 denominator.

## Controls

All synthetic fixtures are `SYNTHETIC_CONTROL`, not research samples. The unchanged
sham is byte-identical, the evidence-only control leaves execution unchanged, legal
P and N mutations alter only their named target field and propagate through every
step value to the terminal execution answer, and direct `res`/`answer` editing is
rejected by the executor mutation API.

## Verification

| Check | Result |
|---|---|
| `python -m py_compile ...` | `COMMAND_NOT_FOUND`; Python executable is `/usr/bin/python3` |
| `python3 -m py_compile ...` | PASS |
| `PYTHONPATH=src python3 -m pytest ... -q` | FAIL: `No module named pytest` |
| `PYTHONPATH=src python3 -m unittest ... -v` | PASS: 15 / 15 |
| exact clean replay | PASS: 7,134 records; all hashes pinned |
| two-run replay `cmp` | PASS: byte-identical |
| replay SHA-256 | `993cd2328bc77739ed1f6e0ad14d6592695911801b526aabb16f825d77a8fbdb` |
| source manifest verification | PASS: 23 / 23 entries |
| manual `res`/`answer` negative tests | PASS |
| unsupported operation negative test | PASS |

No `loop_b_verify.sh` command was run.
