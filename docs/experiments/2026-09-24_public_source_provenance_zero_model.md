# 公开来源取证（零模型）：P1 FinQA/ConvFinQA 与 P2 Valentine NYC 的 head 与 license

> 状态: 证据件（2026-09-24, Loop D）| 零模型调用、零生产端点、**不下载任何数据体**
> 取证时间: finqa / convfinqa = 2026-09-24T08:05:05Z；valentine_nyc = 2026-09-24T08:05:21Z（GB10 执行）
> 关系: 服务 LC-RESEARCH-001-ONLINE 的 P1/P2 优先级（用户 2026-09-24 裁定），但该卡仍 BLOCKED 待模型裁定；
> 本件是 Loop D 的零模型取证，**不消耗该卡 <200 预算**，也不改动该卡拥有的
> `docs/datasets/paper-public-source-registry-v1.json`（append-only 行留待卡解锁后补）。

## 1 方法

- `git ls-remote <official_repo> <ref>` 取默认分支 head（finqa / convfinqa 用 `refs/heads/main`，
  valentine 用 `HEAD`——其默认分支是 `master`，用 `refs/heads/main` 会空结果，这是本件实测出的口径差异）。
- `curl -fsS https://raw.githubusercontent.com/<org>/<repo>/<head>/LICENSE` 只取 license 文本（元数据，非数据体），
  记录 http 码、字节数、sha256；license 范围**逐字引用**不改写。
- 全部输出落 GB10 `/tmp/prov_20260924/`，仓外；未写任何仓内文件；未触碰 production。
- 模型调用 0；除 github.com / raw.githubusercontent.com 的公开元数据外无任何网络目标。

## 2 逐源事实（与 registry 对照）

| dataset_id | official_repo | 本次 head | registry checked_default_head | 漂移 | license 文件 | 字节 | sha256 | license 族（据首行引用） |
|---|---|---|---|---|---|---|---|---|
| finqa | czyssrs/FinQA | `0f16e2867befa6840783e58be38c9efb9229d742` | `0f16e2867bef` | **无** | LICENSE | 1067 | `92c0e67bd762c15c07ba60de09558338315a8ebf99aac4f51f487179809ac087` | MIT |
| convfinqa | czyssrs/ConvFinQA | `cf3eed2d5984960bf06bb8145bcea5e80b0222a6` | `cf3eed2d5984` | **无** | LICENSE | 1067 | `5c7b6fe25d37f4b6cc7e0e76267bce7146765b7661d4bb0e9ecc4eb0ed34fb4c` | MIT |
| valentine_nyc | delftdata/valentine | `5d5163f04da304985bd51a476ccf7653de3979c3` | `5d5163f04da3` | **无** | LICENSE | 11365 | `f4960433bd98568685898d782e724fc28b5481be2a4b57b6280bf6e8c262e99d` | Apache-2.0 |

三个 head 与 registry 记录**逐字节前缀一致**，即 registry 的 `checked_default_head` 在 2026-09-24 仍有效，
SOURCE_GO 的「commit/release 已核」一项对这三个源**前进了一步**（从「曾核」到「今日复核且哈希在案」）。

过程中两次假象已排除并记录，避免误报缺陷：① 首轮对 convfinqa 用 `ls-remote <url> HEAD` 得空串，
拼出 `.../<空 sha>/LICENSE` 触发 raw 的 307，实为**本件自己的空 sha URL**，非仓库改名；② valentine 无
`refs/heads/main`（默认分支 `master`），同理会得空 sha。两者均改用正确 ref 后 http=200。

## 3 license 范围逐字引用（前若干行，不改写）

finqa / convfinqa（MIT，仅版权年不同：2021 / 2022，作者 Zhiyu Chen）:

```text
MIT License

Copyright (c) 2021 Zhiyu Chen            <- convfinqa 为 2022

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
```

valentine（Apache License Version 2.0, January 2004）:

```text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
```

## 4 对七个缺失角色的后果（只推进草案，不造工件）

- `schema`（P1）: 候选必须来自 FinQA/ConvFinQA 官方仓库自带的字段文档（README / 论文附表结构），
  **不得**再用已否决的 `m1_table_schema.json`。取这些文档文件属元数据取证，可在卡解锁后或按本件同口径零模型完成。
- `label_ledger`（P1）: FinQA/ConvFinQA 的 gold 标注是**数据体**，本件未取、也不得在未批准下载前取；
  故 LABEL_GO 仍需「批准下载 + 两个独立 reviewer + 裁决记录」，当前不可过。
- `licence_record`: 仓库 license 现已可见、已哈希、已逐字引用，但 licence_record 工件要求
  `accepted_by` / `accepted_at` / `permitted_uses` / `covered_artifact_sha256`，是**人工接受行为**；
  本件的引用只是其输入证据。MIT/Apache-2.0 对仓库内数据文件的覆盖范围属法务判断，本件**不作**判断，
  保留 registry 的 `REPO_LICENSE_VISIBLE_DATA_SCOPE_REVIEW_REQUIRED` 口径。
- `confidence_manifest`（P1）: FinQA 无自带置信度字段 ⇒ 按合同只能记 `missing_policy = unmeasurable`，
  且 `gain_collateral_substitution` 必须为 false；这是可由本件事实直接推出的草案结论。
- P2 valentine_nyc: Apache-2.0 覆盖 valentine 仓库；registry 另记的 NYC 上游与扰动 provenance 复核
  （`NYC_UPSTREAM_AND_LLM_PERTURBATION_PROVENANCE_REVIEW_REQUIRED`）**仍然开放**，本件不关闭它。
  按 dataset_protocol，P2 只作 **action 来源**，不与 P1 拼同分布主实验。

## 5 本件不做的事

- 不改 `docs/datasets/paper-public-source-registry-v1.json`（卡属 append-only 路径）；本件的 head 与
  license sha256 留待卡解锁后以 append-only 行入册。
- 不下载数据体、不解冻 TAT-DQA、不动旧 TAT-QA 池（仍 HISTORICAL_ONLY）。
- 不产生任何 baseline / 论文数字；不改 DATA_NO_GO；不改任何门、阈值或 oracle。
- 不消耗 LC-RESEARCH-001-ONLINE 的 <200 预算（模型调用 0）。
