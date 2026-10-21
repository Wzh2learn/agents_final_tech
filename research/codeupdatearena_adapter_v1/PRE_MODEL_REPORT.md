# CodeUpdateArena Adapter Pre-Model Report

- Frozen at: `2026-10-21T13:50:31.464658+08:00`
- Evidence identity: `PUBLIC_SYNTHETIC_EXTERNAL_EXECUTION_DEV_ONLY`
- Source commit: `836e2d157739fd53f9cde421913eb5949d4eeeb8`
- Dataset SHA-256: `99fa09f3c371efc107b086fb2ae221ecae815a08bc26116b72cf2c2c4a81eafc`
- Docker image: `python-sandbox:latest`
- Docker image ID: `sha256:0fc8b2941cd46391b8fdd1fea784d91ad9a7a0e31a3a703ae08842c653b33d40`
- Planned model attempts: `16`
- Reserved accounting tokens: `50000`

## Prompt Boundary

The `base` arm contains only scenario, problem, solution signature, and imports. The `update_info` arm adds only the public update description, rationale, docstring, and new signature. Reference solutions, hidden unit tests, update implementations, and update-enforcement statements are absent from every planned request.

## Docker Oracle

- Reference all-tests-pass families: `8/8`
- Reference hidden tests passed: `50/50`
- Oracle gate: `PASS`

| # | Family | Tests | Passed | All pass | Wall s | Status |
|---:|---|---:|---:|---|---:|---|
| 1 | `[itertools.compress]:[add-argument]:[update-0]:[prog_syn-0]` | 8 | 8 | true | 1.051 | `pass` |
| 2 | `[itertools.chain]:[add-argument-data_type]:[update-0]:[prog_syn-0]` | 6 | 6 | true | 0.733 | `pass` |
| 3 | `[math.comb]:[add-argument-default_value(s)]:[update-0]:[prog_syn-0]` | 6 | 6 | true | 0.803 | `pass` |
| 4 | `[itertools.chain]:[add-argument-semantics]:[update-0]:[prog_syn-0]` | 6 | 6 | true | 0.765 | `pass` |
| 5 | `[itertools.compress]:[add-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | 6 | 6 | true | 0.808 | `pass` |
| 6 | `[math.comb]:[add-function]:[update-0]:[prog_syn-0]` | 4 | 4 | true | 0.483 | `pass` |
| 7 | `[math.sin]:[add-output-data_type]:[update-0]:[prog_syn-0]` | 8 | 8 | true | 1.073 | `pass` |
| 8 | `[itertools.product]:[add-output-semantics]:[update-0]:[prog_syn-0]` | 6 | 6 | true | 0.777 | `pass` |

## Frozen Attempt Order

| Attempt | Family | Arm | Request SHA-256 |
|---:|---|---|---|
| 1 | `[itertools.compress]:[add-argument]:[update-0]:[prog_syn-0]` | `base` | `91435b400f89cbd583e278b0d10eae9790db586b920fe5f95fd3aed07c5486f7` |
| 2 | `[itertools.compress]:[add-argument]:[update-0]:[prog_syn-0]` | `update_info` | `f8d2b9dae9f033cf8cddb01132c821c513cc268337f2b7a2969adcc343a0e53d` |
| 3 | `[itertools.chain]:[add-argument-data_type]:[update-0]:[prog_syn-0]` | `base` | `13a150584a500a309f60a297d2c5a4ce26839227136d57edf62811f8b8b21103` |
| 4 | `[itertools.chain]:[add-argument-data_type]:[update-0]:[prog_syn-0]` | `update_info` | `1313dedab45812d25ef6438e785214188c2d4749e334ecbf38f83d99f45632e3` |
| 5 | `[math.comb]:[add-argument-default_value(s)]:[update-0]:[prog_syn-0]` | `base` | `e24d3c8e33d08ce8c76102687748e1131e819f1e639b5080361f098f3f62c778` |
| 6 | `[math.comb]:[add-argument-default_value(s)]:[update-0]:[prog_syn-0]` | `update_info` | `fcdd0927b6c32f8e20ed02484c821509854f757c56f6476d39d7e0dbdf7e57f8` |
| 7 | `[itertools.chain]:[add-argument-semantics]:[update-0]:[prog_syn-0]` | `base` | `5917d7b474c9ee22b37d2dbff2865b0991bef7ef2375f37adb9e15e71e7801e5` |
| 8 | `[itertools.chain]:[add-argument-semantics]:[update-0]:[prog_syn-0]` | `update_info` | `6b8c285371c6cc336c16fa34c1f6c37c9eafd3193e1b185a6da258c89b12e57f` |
| 9 | `[itertools.compress]:[add-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | `base` | `4171061e66c2dffc371716079b251b6a25deacff040f47fc6a098cecb7dcc80a` |
| 10 | `[itertools.compress]:[add-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | `update_info` | `0989db398e02ab09af4c2f7391d792bc039498120026da7999a8aef97d20ab03` |
| 11 | `[math.comb]:[add-function]:[update-0]:[prog_syn-0]` | `base` | `f33fc8c097ac8ac7e4384b74ca091fe854ef4d2419ead296cf9be245cb759705` |
| 12 | `[math.comb]:[add-function]:[update-0]:[prog_syn-0]` | `update_info` | `47f9e917a47ffec81c7ba95e042e96f5a0b1cd9e8cf2a88c4a1619d8dcc8c28a` |
| 13 | `[math.sin]:[add-output-data_type]:[update-0]:[prog_syn-0]` | `base` | `a63ae168fd8618fbafc9cfdd868c350fb448bf2d2a77838d044dbfe8cee83252` |
| 14 | `[math.sin]:[add-output-data_type]:[update-0]:[prog_syn-0]` | `update_info` | `2d44d56f6b08e4becd180b64df6082d7b72b616c7bcdb3d2eb388bda8f187348` |
| 15 | `[itertools.product]:[add-output-semantics]:[update-0]:[prog_syn-0]` | `base` | `30663054d312da59804541d2d20a58d565327b8095799592c072d5498269de3b` |
| 16 | `[itertools.product]:[add-output-semantics]:[update-0]:[prog_syn-0]` | `update_info` | `a7c0a4361b71ab23bbd20d42d5cec836b685060bfd4f3702c9af85878556c364` |

## Stop Rules

- No retry and one generation per task and arm.
- Generated syntax, runtime, timeout, and hidden-test failures remain model results and do not stop the batch.
- Model-identity mismatch, malformed JSON envelope, missing usage, HTTP failure, or sandbox infrastructure failure stops the batch.
- No official paid GPT-4 script, judge, training call, external network access, or production-memory write is permitted.
