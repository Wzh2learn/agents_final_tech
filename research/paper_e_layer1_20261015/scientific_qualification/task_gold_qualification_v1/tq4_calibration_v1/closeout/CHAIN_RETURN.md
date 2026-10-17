# CHAIN_RETURN

> 链式授权: `OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md`（S1-S5）| 作者: Loop D（AI）
> 状态: `COMPLETED_WITH_NOTES` | 日期: 2026-10-17 Asia/Shanghai
> 边界: TQ-4/TQ-5 分开评价；无 confirmatory claim；`scientific_gold_validity = NOT_ESTABLISHED`

## 阶段完成表

| 阶段 | 状态 | 证据 |
|---|---|---|
| S1 实现与离线核验 | 完成 | scorer v2.1、18/18 回归、双面板 14/14 点检、TQ-4/TQ-5 49+49 材料 pin；TQ-5 增加 8 文件哈希快照 |
| S2 TQ-4 校准运行 | 完成 | `20261016T082849Z_430d927a`：36 attempts、0 retry、40,205 tokens、194 秒 |
| S3 TQ-4 分析/复核收口 | 完成 | `POST_RUN_REVIEW_v1.md`、`POST_RUN_REVIEW_DISPOSITION_v1.md`、`TQ4_RUN_RETURN_ERRATA_v1.md`、`execution_v1/recovery_v1/tq4_analysis_v22_20261017/` |
| S4 TQ-5 来源隔离验证 | 完成 | `20261017T072340Z_5d8942bd`：36 attempts、0 retry、44,867 tokens、196 秒；`TQ5_RUN_RETURN.md` |
| TQ-5 聚焦复核 | 完成 | `reviews/TQ5_POST_RUN_FOCUSED_REVIEW_v1.md` + `TQ5_POST_RUN_RECOMPUTE_v1.json`；非独立复核声明 |
| S5 交付 | 完成 | 本文件、`CONTRIBUTION_RULING.md`、`PAPER_E_ADDENDUM_DRAFT.md` |

## 预算与真实运行

| panel | run_id | 计划/尝试 | 重试 | settled token | 首请求 | 末响应 | 时长 |
|---|---|---:|---:|---:|---|---|---:|
| TQ-4 | `20261016T082849Z_430d927a` | 36/36 | 0 | 40,205 | 16:29:02 | 16:32:16 | 194s |
| TQ-5 | `20261017T072340Z_5d8942bd` | 36/36 | 0 | 44,867 | 15:23:54 | 15:27:10 | 196s |
| 合计 | 两 run 独立配额 | 72/80 上限 | 0/8 | 85,072/800,000 | - | - | 均单次 <90min |

- TQ-5 使用 TQ-5 自身 36/40 attempt、0/4 retry、44,867/400,000 token；TQ-4 未用额度没有转移。
- chain master 维持同一总账，共 72 reserve / 72 settle；TQ-4 原 72 行前缀未改。`tokens_unsettled` 是旧字段名，本报告均显式写 settled token。
- 新增付费实验 API 为 USD 0；研发对话成本单独存在，不冒称零 token/零成本。

## TQ-4 S3 收口

- 全 run 合法输出 35/36；B 有效决策 15/16（Part1 4/4、Part2 11/12），HTTP 200 不等于输出有效。
- 矩阵解析失败显示 `invalid`，`ledger_state=done` 不是模型决策；TQ-4 新分析目录保留原 run 不动。
- 点检为 14/14（含 `material_pin_check_full`）；时间口径为 16:29:02 / 194 秒。
- N1 仅支持“参考匹配与核验存在语义分歧”；C 决策为 alarm，但 `contradiction_points=[]` 且 reason 尾部有接受措辞，单列内部不一致。
- Q03-C3/C4 保留原构造标签和原结果，但运算方向有语义歧义，语义资格 `NOT_ESTABLISHED`，不统计为已证实共同漏检。
- TQ-4 config 运行时快照缺失。当前文件 mtime 在运行窗口内，不能继续声称只在运行后改了 `scoring_dir`；旧 `RUN_META` 哈希不修改，不生成假配置，不重跑。
- 原“84 文件双端核对”没有专用历史收据，已撤回为历史断言；本地 84/84 manifest 与当前文件复核保留。

## TQ-5 结果

- 12 个 actor 输出均可解析；冻结数值评分 MATCH 7/12、NO_MATCH 5/12；证据定位 legal 11/12。
- B: accept10 / alarm1 / abstain1。C: accept9 / invalid3。C-T06/C-T07 为 prose+embedded JSON，C-T10 为 2048-token 截断；均不提取 prose 判决、不重试。
- 机器 NO_MATCH 不直接等于模型错误：T01 是括号负号解析限制；T07 参考用 affiliate-sales 行充当 total-sales 分母，语义比较 `UNSCORABLE`；T08 保留“all years”范围参考不确定性；T10/T12 是未指定精度与冻结容差冲突，均不得归类为已证实错误，状态为 `UNSCORABLE_FOR_PROVEN_ERROR`。
- 引用支持性仍 `NOT_ASSESSED`。TQ-5 仅支持 table-disjoint 开发性表述，不支持 report-level independent、training-unseen 或 header-drift 因果。
- 原 analyzer 的 `part1.summary.label` 误复用 TQ-4 文案；`reviews/TQ5_RESULTS_CORRECTED_v1.json` 仅修正标签并保留源哈希，结果值不变。

## 复核范围

- 已交付且不再重复等待：TQ-4 运行独立复核 `loopc_tq4run_review`；TQ-5 预运行独立复核 `loopc_tq5_prereview`。
- 本轮新增为 Loop D 聚焦确定性复算，不冒称独立复核。覆盖 83/83 run 文件、8/8 snapshot 文件、RUN_META、账本/预算、评分/合法性、决策、prompt 隔离。
- 复算实跑通过 run_manifest、execution_snapshot、run_meta、budget_and_ledger、outputs、prompt_isolation、原标签保真和修正版结果值不变检查；修正版另行落盘。

## 同步与保全

- 已定向镜像两套复核脚本/JSON/MD 与当时 `CHAIN_RETURN.md` 到 GB10，双端哈希一致。
- TQ-5 snapshot 已镜像到 GB10，manifest 哈希双端为 `a9c1c79e...`；远端定点测试 4/4、材料 pin 49/49、36 步 plan 通过。
- TQ-5 GB10 run 已镜像到本地；raw/prompts/ledger/run outputs 不推 Git。主账本为字节前缀追加镜像，不覆盖 TQ-4 旧记录。
- 未覆盖冻结稿、旧参考、旧实验、TQ-4 原始 run 或 `RUN_META`。
- 仓库 `docs_lint` 当前仍为 FAIL，唯一失败是既有 skill 分发漂移 2/99（`subagent-fanout`、`inquiry-methods`），另有 20 条既有警告；本任务未改技能库。项目约定提到的 `vibe-coding-quality-gate` 与 `generate-commit` 已从仓库移除，故采用现有回归、快照测试、复算门、`git diff --check`、pre-commit hooks 与逐路径提交替代。

## 可支持与不可支持

- 可支持：两个受控开发面板的真实执行记录、机器评分/合法性/决策分布、格式与语义边界、不可变快照工程机制。
- 不可支持：C 优于 B、普遍共同盲点、有效错误率、人工科学 gold、官方参考绝对错误、actor 绝对正确、引用支持性已验证、确认性或可外推结论。
- 裁决：`NO_PROMOTION`。仅保留方法/局限增补草稿，不改冻结 Paper E，不启动第三轮。
