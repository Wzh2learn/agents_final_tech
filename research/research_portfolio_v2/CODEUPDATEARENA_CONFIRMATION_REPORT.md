# CodeUpdateArena Independent-New-Family Confirmation

- Status: `COMPLETE_16_ATTEMPTS`
- Evidence identity: `PUBLIC_SYNTHETIC_EXTERNAL_EXECUTION_INDEPENDENT_NEW_FAMILY_CONFIRMATION`
- Decision: `BOUNDED_NEGATIVE_STOP`
- Source commit: `836e2d157739fd53f9cde421913eb5949d4eeeb8`
- Attempts used: `16/16`
- Accounting tokens used: `10995/50000`
- Physical generation HTTP calls: `16`
- Model identity probe calls: `1`

## Scope

This is an independent new-family confirmation on the same public synthetic
CodeUpdateArena source. It measures one local model on eight disjoint frozen
update families. It is not evidence about natural production drift and is not
a general model-capability benchmark.

## Paired Result

- Primary paired difference `update_info - base`: `-3` all-tests-pass families
- Base all-tests-pass families: `7/8`
- Update-info all-tests-pass families: `4/8`
- Base hidden tests passed: `44/48`
- Update-info hidden tests passed: `33/48`

| Family | Base | Update info | Paired delta |
|---|---:|---:|---:|
| `[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | true | true | +0 |
| `[re.fullmatch]:[modify-output-semantics]:[update-1]:[prog_syn-0]` | true | true | +0 |
| `[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]` | true | true | +0 |
| `[re.fullmatch]:[modify-argument-data_type]:[update-0]:[prog_syn-0]` | true | true | +0 |
| `[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]` | true | false | -1 |
| `[re.match]:[modify-argument-default_value(s)]:[update-0]:[prog_syn-0]` | true | false | -1 |
| `[itertools.islice]:[modify-output-data_type]:[update-0]:[prog_syn-0]` | false | false | +0 |
| `[re.sub]:[add-function]:[update-0]:[prog_syn-0]` | true | false | -1 |

## Secondary Metrics

| Arm | Parse | Syntax | Runtime | Test | Infra | Mean model s | Prompt tok | Completion tok | Total tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `base` | 0 | 0 | 0 | 1 | 0 | 3.087 | 2279 | 1411 | 3690 |
| `update_info` | 0 | 0 | 0 | 4 | 0 | 6.444 | 4205 | 3100 | 7305 |

## Evidence

- Frozen snapshot: `research/codeupdatearena_confirmation_v1/TASK_SNAPSHOT.json`
- Frozen run-time spec and runner: `research/codeupdatearena_confirmation_v1/run_frozen/`
- Pre-model report: `research/codeupdatearena_confirmation_v1/PRE_MODEL_REPORT.md`
- Model ledger: `research/codeupdatearena_confirmation_v1/CONFIRMATION_MODEL_LEDGER.json`
- Raw request/response pairs and Docker evidence: `research/codeupdatearena_confirmation_v1/evidence/`
- Machine-readable result: `research/research_portfolio_v2/CODEUPDATEARENA_CONFIRMATION_RESULT.json`

## Nonclaims

- CodeUpdateArena updates are public synthetic API updates, not natural production drift.
- The eight families are independent new-family confirmation observations on
  the same synthetic source and do not establish general model capability.
- The official paid GPT-4 scripts and finetuning workflows are excluded.
- No judge, training, external network, or production-memory write is used.
