# D-B 正式 licence_record 接受证据（2026-10-04）

> 状态：证据件，不是 package-wide licence 授权 | 运行环境：GB10 生成，local 仅登记
> 记录文件：`docs/datasets/phase1a_licence_record_v1.json`

## 1 接受行为

| 字段 | 值 |
|---|---|
| `status` | `accepted` |
| `accepted_by` | `Wzh` |
| `accepted_at` | `2026-10-03T17:01:42Z`（GB10 生成现场 UTC 时间） |
| `permitted_uses` | `training`, `tuning`, `evaluation`, `rule_acceptance` |

`accepted_at` 由 GB10 生成命令的 `datetime.now(timezone.utc)` 现场产生；未回填历史时间，未使用
`fixture-user` / `data-owner` 测试夹具。

## 2 covered_artifact_sha256 scope

只覆盖 D-B annex 实测的三件：

| id | 工件 | sha256 |
|---|---|---|
| `finqa_repo_license` | FinQA `LICENSE` | `92c0e67bd762c15c07ba60de09558338315a8ebf99aac4f51f487179809ac087` |
| `finqa_readme` | FinQA `README.md` | `eb86779cfed6f0a253913761d8e4fabe032a29d9fcf2944e56c23bf007064605` |
| `valentine_repo_license` | Valentine `LICENSE` | `f4960433bd98568685898d782e724fc28b5481be2a4b57b6280bf6e8c262e99d` |

不覆盖 `source_tables`、`injection_map`、`schema`、`label_ledger`、`learnability_feature_ledger`、
ConvFinQA、其他数据源或其他许可文本。记录显式排除 `redistribution`、`public_release`、
`commercial_use`、`other_data_sources`、`other_licence_interpretations`。

## 3 数据边界

- D-C 最小下载已完成：FinQA `train.json` / `dev.json`、Valentine 十个 NYC 目录、`LICENSE`、`bench.py` 在 GB10 仓外暂存并通过 manifest 核验。
- 本件不新增下载、不读取数据体、不把 fetch 脚本/PID/log/bytes manifest 误报成数据集。
- Q3 runner 的 10 pair × 3 文件 allowlist 是下游复核输入约束，不改变 D-C 目录级批准范围。
- 该 licence_record 不解除 `DATA_NO_GO`，不提供缺失的 label/schema/confidence/analysis_plan/parser receipt/feature ledger，不构成 `DATA_GO` 或训练许可。

## 4 机械校验

- GB10 目标测试：`tests/test_phase1a_licence_record.py`、`tests/test_phase1a_data_contract.py`、`tests/test_phase1a_role_chain_integration.py`、`tests/test_document_governance.py` 共 `49 passed`。
- GB10 全量 pytest @ `c26ae04`：`824 passed / 13 skipped / 1 deselected`。
- `validate_paper_claims.py`：`PASS / 73 checks`。
- `docs_lint`：`rc=0 / 0 fail / 4 warn`，四条与既有基线同构。
- 记录文件 sha256：`57592fa141806d83791bb13a8b110edc0a007f0003279c80a949b6e8a85dd8d8`。
