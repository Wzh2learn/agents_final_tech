# TAT-DQA `joint-v1` data card

`joint-v1` is the approved public starting point for the JinRongAgents M1 → M2
baseline. It is not an M1, M2, OCR, retrieval, or model-quality result.

## Source and license

- Dataset: TAT-DQA
- License: CC BY 4.0
- Official project: <https://nextplusplus.github.io/TAT-DQA/>
- Official package: <https://drive.google.com/drive/folders/1SGpZyRWqycMd_dZim1ygvWhl5KdJYDR2>

The official Drive package contains the original PDFs and converted JSON. Those
files, any rendered pages, logs, and derived outputs stay in
`/home/testuser/wzh/datasets/tat-dqa/` and are never committed here.

## Reproduction

First inspect the expected compressed package size and available storage:

```bash
python scripts/tat_dqa_data.py plan
```

The catalog records 1,514,773,595 bytes (about 1.41 GiB) across seven official
files. Run the following only after the plan reports sufficient space:

```bash
python scripts/tat_dqa_data.py download \
  --status-out /home/testuser/wzh/datasets/tat-dqa/download-status.json
python scripts/tat_dqa_data.py validate \
  --status-out /home/testuser/wzh/datasets/tat-dqa/validation-status.json
python scripts/prepare_tat_dqa_joint_v1.py \
  --train-input /home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_train.json \
  --validation-input /home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json \
  --test-input /home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_test_gold.json \
  --manifest-out docs/datasets/tat-dqa-joint-v1-manifest.json \
  --checks-out docs/datasets/tat-dqa-joint-v1-checks.json
```

The downloader performs no automatic retry. If Drive access, quota, content
format, or disk capacity fails, it writes a sanitized external status and exits
non-zero; inspect and resolve that condition before issuing a new download.

## Acquisition status — 2026-07-23

The pre-download capacity check passed. One official download pass obtained all
four JSON files and the dev/test document archives. The train document archive
remains absent after a sanitized Google Drive proxy disconnect; the external
validation status consequently reports that expected file as missing. This is a
data-acquisition blocker only: the downloaded official JSON was sufficient to
freeze the public-ID manifest, but it is not evidence that the complete raw
package has been validated.

## Frozen sampling contract

- Seed: `20260722`
- Documents: 100 exactly; document-level train/validation/test split of 60/20/20
- Questions: at most 500
- Required answer-type coverage: `span`, `spans`, `arithmetic`, `counting`, and
  `comparison`
- Official split boundary: official train -> train, dev -> validation, and
  test-gold -> test; no official dev/test-gold document may enter training
- Leakage rule: a `document_id` may belong to exactly one split

The committed manifest contains only public IDs, source/assigned split labels, answer type,
page number, public source-block IDs, and license. It deliberately excludes
questions, answers, calculation programs, evidence text, PDFs, coordinates,
and model output.

The official labels `multi-span` and `count` are normalized to `spans` and
`counting`; records marked `req_comparison` normalize to `comparison`. Official
questions without an answer-type label are not selected for this typed baseline.

Focused verification uses the repository environment rather than the isolated
tabular environment:

```bash
/home/testuser/wzh/envs/agents_final_tech/bin/python -m pytest \
  tests/test_tat_dqa_joint_v1.py -q
```

On 2026-07-23 this completed with `9 passed`. The frozen manifest contains 300,
100, and 100 questions in train, validation, and test respectively; both the
document-level and official-source-split leakage checks are false.
