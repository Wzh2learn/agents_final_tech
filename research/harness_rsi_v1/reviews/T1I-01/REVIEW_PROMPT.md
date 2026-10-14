# Loop C 独立评审任务 T1R-01：harness_rsi_v1 T1 事故案例整理包

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审：不修改任何仓库文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T2。全部输出只写 stdout。

## 背景
- R 线已获 owner 授权（至 M1）；协议已 FROZEN（`282f5213…`）；T0 已验收（T0R-01 ACCEPTED）。
- 执行者产出 T1 运行包：`research/harness_rsi_v1/runs/T1/20261014T132249Z_99f3bc6b/`（7 件：incidents.jsonl 16 例、coverage_matrix.json、source_groups.json、receipt.json、summary.md、events.jsonl、artifacts_manifest.json）。
- 你的职责：**事实核对每一条事故案例**（不是只看格式），判断该包是否可交 owner 验收；给出提案（ACCEPTED/REJECTED/PENDING_HUMAN_REVIEW）。registry/state 不由你写。

## 必读（只读）
`AGENTS.md`；`cards/T1.md`；`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`；`evaluation/reliability_spec.md`；`evaluation/split_registry.json`；上述 T1 包 7 件全文；被引用的关键证据文件（见下）。

## 必须独立复算与核对（记录命令与退出码；python3 可用；避免 find -exec 与 $(...)）
1. T1 六件产物 SHA-256/字节 vs artifacts_manifest；run 目录恰 7 件。
2. T1 卡 7 个输入 + STOP_S4/PREFLIGHT 两个 authority 引用存在且实算哈希 = receipt.input_bindings。
3. **逐条事实核对（核心）**：对 16 例，逐例核对 `source_refs` 路径存在，并抽查/全查 `observed_fact` 是否有该证据支撑。重点：
   - T1-INC-06：`S4C_ONLINE_QUALIFICATION_RECEIPT.json` 的 400 消息与 `INCIDENT_2`/`processor_interface_diagnosis_output.json` 是否确实支持"调用约定错配"表述；
   - T1-INC-03 / T1-INC-04：`S4B_STOP_RECEIPT.json` 的 probe_cap=4/3 与 raw 覆盖披露是否如述；
   - T1-INC-05：`INCIDENT_1_runner_import_failure.txt` 是否支持"零传输、修复一次"；
   - T1-INC-08：commit `7406b3c`、`fe7b87f` 是否存在且确为 force-add *.log 证据；
   - T1-INC-09：草案目录 `SUPERSEDED.md` 与 v2/清单补钉是否支持"C2 失配后补钉"叙述；
   - T1-INC-10：`authority_map.json`（现为 canonical 重钉后版本）与 `T0R-01`/`T1R-02` 是否支持"6/13 表示差异、无内容漂移"；
   - T1-INC-11/12/13 与 T1-CTRL-01/02：`reviews/T1R-01`、`memory/STATE.md`、`memory/THREADS.md`、`docs/INDEX.md` 是否支持其陈述（凡引用不足以支撑者，明确列为问题）。
   结论须给出：过度陈述/错误归因/引用不足 的清单（若有）。
4. A1/A2/A3：每例来源/适用范围/预期类别/族与合法对照是否齐全；同源不跨组（校验 7 个组与 16 例的成员关系，无双重归属）、无 sealed 标记、已公开复盘仅开发/校准；不复制私有正文（描述长度与中性度）；不重跑旧实验（零调用）。
5. 预算 B0：零编排调用；写入边界仅 runs/T1/<run_id>/；24/24/24 是否明确标注为"构建计划"而非现有数量。
6. 反证尝试：是否有越界写入、把工程失败当科学结果、引用不存在文件、把已复盘案例标封存等。

## 硬性约束
全程只读；不得创建/修改/删除任何文件；工作目录为仓库根；不 git 写；不联网；不调端点/服务/数据库；不进入 T2。

## 输出（仅 stdout；三块标记）
=== FILE: REVIEW.md ===
（Markdown：范围；逐项结果与命令；16 例事实核对表（结论=支撑/不足/过度陈述）；发现 Fx（严重度/证据）；FACT/INFERENCE/UNVERIFIED；未验证面；判定与理由）
=== FILE: review_receipt.json ===
（JSON：reviewer/runtime；reviewed_artifact_sha256（T1 七件 + T1 卡 + reliability_spec + authority_map 关键引用）；recomputed；checks；calls（自身会话 1；network/services/db 0；token UNRESOLVED）；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；reviewed_artifact_sha256；scope；justification；dissent）
=== END ===

重申：只写提案；registry/state 由收口者更新。