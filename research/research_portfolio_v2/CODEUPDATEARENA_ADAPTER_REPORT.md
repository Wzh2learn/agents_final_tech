# CodeUpdateArena External Adapter Report

- Status: `COMPLETE_16_ATTEMPTS`
- Evidence identity: `PUBLIC_SYNTHETIC_EXTERNAL_EXECUTION_DEV_ONLY`
- Decision: `BOUNDED_NEGATIVE_STOP`
- Source commit: `836e2d157739fd53f9cde421913eb5949d4eeeb8`
- Attempts used: `16/16`
- Accounting tokens used: `9986/50000`
- Physical generation HTTP calls: `16`
- Model identity probe calls: `1`

## Scope

This is `PUBLIC_SYNTHETIC_EXTERNAL_EXECUTION_DEV_ONLY`. It measures one local model on eight frozen CodeUpdateArena synthetic update families. It is not evidence about natural production drift and is not a general model-capability benchmark.

## Paired Result

- Primary paired difference `update_info - base`: `-1` all-tests-pass families
- Base all-tests-pass families: `3/8`
- Update-info all-tests-pass families: `2/8`
- Base hidden tests passed: `28/50`
- Update-info hidden tests passed: `22/50`

| Family | Base | Update info | Paired delta |
|---|---:|---:|---:|
| `[itertools.compress]:[add-argument]:[update-0]:[prog_syn-0]` | true | true | +0 |
| `[itertools.chain]:[add-argument-data_type]:[update-0]:[prog_syn-0]` | true | false | -1 |
| `[math.comb]:[add-argument-default_value(s)]:[update-0]:[prog_syn-0]` | true | true | +0 |
| `[itertools.chain]:[add-argument-semantics]:[update-0]:[prog_syn-0]` | false | false | +0 |
| `[itertools.compress]:[add-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | false | false | +0 |
| `[math.comb]:[add-function]:[update-0]:[prog_syn-0]` | false | false | +0 |
| `[math.sin]:[add-output-data_type]:[update-0]:[prog_syn-0]` | false | false | +0 |
| `[itertools.product]:[add-output-semantics]:[update-0]:[prog_syn-0]` | false | false | +0 |

## Secondary Metrics

| Arm | Parse | Syntax | Runtime | Test | Infra | Mean model s | Prompt tok | Completion tok | Total tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `base` | 0 | 0 | 5 | 0 | 0 | 3.045 | 2078 | 1388 | 3466 |
| `update_info` | 0 | 0 | 6 | 0 | 0 | 5.256 | 4024 | 2496 | 6520 |

## Evidence

- Frozen snapshot: `research/codeupdatearena_adapter_v1/TASK_SNAPSHOT.json`
- Pre-model report: `research/codeupdatearena_adapter_v1/PRE_MODEL_REPORT.md`
- Model ledger: `research/codeupdatearena_adapter_v1/MODEL_LEDGER.json`
- Raw request/response pairs and Docker evidence: `research/codeupdatearena_adapter_v1/evidence/`
- Machine-readable result: `research/research_portfolio_v2/CODEUPDATEARENA_ADAPTER_RESULT.json`

## Nonclaims

- CodeUpdateArena updates are public synthetic API updates, not natural production drift.
- The eight families are development observations and do not establish general model capability.
- The official paid GPT-4 scripts and finetuning workflows are excluded.
- No judge, training, external network, or production-memory write is used.
