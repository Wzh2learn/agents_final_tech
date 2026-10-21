# CodeUpdateArena Adapter Pre-Model Report

- Frozen at: `2026-10-21T15:09:37.671183+08:00`
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
- Reference hidden tests passed: `48/48`
- Oracle gate: `PASS`

| # | Family | Tests | Passed | All pass | Wall s | Status |
|---:|---|---:|---:|---|---:|---|
| 1 | `[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | 10 | 10 | true | 1.318 | `pass` |
| 2 | `[re.fullmatch]:[modify-output-semantics]:[update-1]:[prog_syn-0]` | 3 | 3 | true | 0.412 | `pass` |
| 3 | `[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]` | 9 | 9 | true | 1.221 | `pass` |
| 4 | `[re.fullmatch]:[modify-argument-data_type]:[update-0]:[prog_syn-0]` | 4 | 4 | true | 0.529 | `pass` |
| 5 | `[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]` | 5 | 5 | true | 0.657 | `pass` |
| 6 | `[re.match]:[modify-argument-default_value(s)]:[update-0]:[prog_syn-0]` | 6 | 6 | true | 0.788 | `pass` |
| 7 | `[itertools.islice]:[modify-output-data_type]:[update-0]:[prog_syn-0]` | 4 | 4 | true | 0.493 | `pass` |
| 8 | `[re.sub]:[add-function]:[update-0]:[prog_syn-0]` | 7 | 7 | true | 0.929 | `pass` |

## Frozen Attempt Order

| Attempt | Family | Arm | Request SHA-256 |
|---:|---|---|---|
| 1 | `[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | `base` | `cd25be8918c6eaa90a88e5b25edefc731afc0f7e0c39620b4f1bb603a51eb8a1` |
| 2 | `[re.subn]:[modify-argument-supported_value(s)]:[update-0]:[prog_syn-0]` | `update_info` | `71df8bf3d9b080cc27da869edb404901fe87dff6d104505cb75c8c8705c2dfb5` |
| 3 | `[re.fullmatch]:[modify-output-semantics]:[update-1]:[prog_syn-0]` | `base` | `689e268617d30e257e0c1baa026c5fb81a921a275b784efd1e5d1411d43db48f` |
| 4 | `[re.fullmatch]:[modify-output-semantics]:[update-1]:[prog_syn-0]` | `update_info` | `51f233fbd25a851c1d11b9a3eabda5bd248a456911f42facc63525a073069cf5` |
| 5 | `[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]` | `base` | `fde7447ba18fd0114dfca5418a6d488f9e833f771371f38a4540a12fe0a50df3` |
| 6 | `[re.match]:[modify-function-name]:[update-0]:[prog_syn-0]` | `update_info` | `cd004c5cb67c045f30209299cd04de9d6695a5798674baded1a10fbb5c018a51` |
| 7 | `[re.fullmatch]:[modify-argument-data_type]:[update-0]:[prog_syn-0]` | `base` | `c12a0dfddb90cb37fae717bc76762e21f8c1b540e247eb5b8f737bd248266dc1` |
| 8 | `[re.fullmatch]:[modify-argument-data_type]:[update-0]:[prog_syn-0]` | `update_info` | `d5f2cbdc090e259e8b727fabbedef94aef2efe0b5d75035df1a293f3cdf27c39` |
| 9 | `[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]` | `base` | `c8ea5404725939b8641399d76cdb792b966cd883d65f87712ebf7d8810bba2b4` |
| 10 | `[re.split]:[modify-argument-semantics]:[update-0]:[prog_syn-0]` | `update_info` | `b40e67a3cc5aefab5d8369826dba16f41a3d31406cfe56e1ed28dc84838634c7` |
| 11 | `[re.match]:[modify-argument-default_value(s)]:[update-0]:[prog_syn-0]` | `base` | `63e3eea755f7863c102c7d5098c2613e484b68863da522a9a242db24b937d910` |
| 12 | `[re.match]:[modify-argument-default_value(s)]:[update-0]:[prog_syn-0]` | `update_info` | `39a6e9d4bf5ae9b12d4916b9b313793092cd0cdc9e2edf1e3cda457ec6491c71` |
| 13 | `[itertools.islice]:[modify-output-data_type]:[update-0]:[prog_syn-0]` | `base` | `1c7eaf7ff2e663fd59e5e1f77d7a2a1b274b4e218ee8b907bd91c666ad30a33e` |
| 14 | `[itertools.islice]:[modify-output-data_type]:[update-0]:[prog_syn-0]` | `update_info` | `e094668164b412975c034a6159c6110f69db467a7c8168147d08cbae1ec7e599` |
| 15 | `[re.sub]:[add-function]:[update-0]:[prog_syn-0]` | `base` | `891bac56082d2e7fa762e3f152983886236ebff8e7b1fc711b888bb9ef01168d` |
| 16 | `[re.sub]:[add-function]:[update-0]:[prog_syn-0]` | `update_info` | `d113e0f51fab3fbd2ffd2f6d3a7adfc8c25cdfa8cbc31ce3e3627fb69df41f92` |

## Stop Rules

- No retry and one generation per task and arm.
- Generated syntax, runtime, timeout, and hidden-test failures remain model results and do not stop the batch.
- Model-identity mismatch, malformed JSON envelope, missing usage, HTTP failure, or sandbox infrastructure failure stops the batch.
- No official paid GPT-4 script, judge, training call, external network access, or production-memory write is permitted.
