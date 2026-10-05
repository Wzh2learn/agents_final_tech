# Training dependency audit（2026-10-05）

> Status: `AUDITED_READY_FOR_DRY_RUN`
> Scope: dependency metadata, installation and vulnerability query only; no model load or training

## 1. Decision

| Package | Decision | Version | Reason |
|---|---|---|---|
| `peft` | install | `0.21.2` | Required for QLoRA adapters |
| `trl` | install | `1.14.1` | Required for SFT/DPO orchestration |
| `datasets` | transitive install | `5.0.1` | Required by `trl` |
| `deepspeed` | do not install | candidate `0.19.7` | Unnecessary for the single-device QLoRA path; source distribution and distributed dependencies avoided |
| accelerator alternative | keep | `accelerate==1.14.0` | Single-device training orchestration already present |

## 2. Environment and dependency checks

- Python: 3.12 virtual environment on GB10.
- `pip install --dry-run` identified `peft 0.21.2`, `trl 1.14.1`, `deepspeed 0.19.7` and the transitive `datasets/pyarrow` surface.
- Installed exactly `peft==0.21.2`, `trl==1.14.1`, `datasets==5.0.1`, `pyarrow==25.0.1`, `dill==0.4.1`, `multiprocess==0.70.19`.
- `pip check`: `No broken requirements found`.
- `peft` license metadata: Apache.
- `datasets` license metadata: Apache 2.0.
- `trl` package metadata does not expose a license field in `pip show`; source/licence file verification is required before any model execution or external distribution.

## 3. Vulnerability metadata query

OSV metadata-only queries on GB10 returned no listed vulnerabilities:

- `peft==0.21.2`: `{}`;
- `trl==1.14.1`: `{}`;
- `datasets==5.0.1`: `{}`.

This is not a formal security certification. It records the exact query result and leaves package provenance/commit or vendored source review pending for any later public-release decision.

## 4. Execution boundary

Dependencies are ready for a **dry-run import check**, but MODEL_GO/TRAINING_GO, exact model/tokenizer revisions, licence review, SOURCE/LABEL/SPLIT/POWER/BASELINE gates and Stage D necessity remain unapproved. No model was loaded, no S0/A0/A1/A2/A3 ran, and no training result exists.
