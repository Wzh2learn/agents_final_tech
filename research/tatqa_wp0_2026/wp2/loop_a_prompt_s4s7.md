# TAT-QA WP-2 采集与冻结（F2–F4 + S4→S7）— Loop A 执行卡

- task: `tatqa-wp2-s4s7-20261014`
- 授权: owner 2026-10-14 明示「按默认开跑」——P2/P3/P4 按下列默认值落档；**MODEL_GO 已授予**（仅限本卡与后续 S9 预算内）。
- 必读（按序）: docs/research/WP2_EXECUTION_RUNBOOK_v1.md §4–5；docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md（臂/调用计数/诚实规则）；docs/research/WP0_ACTOR_REVISION_FREEZE_PLAN_v1.md（F1–F5）；docs/research/WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_DRAFT_v1.md；research/tatqa_wp0_2026/wp1/{PREREG_DRAFT_SKELETON.md, adapter.py, checker_v2.py, provenance.py, implementation_contract.md}；docs/research/WP2_F5_ELIGIBILITY_DECISION_v1.md；docs/governance/2026-09-24_gb10_experiment_safety_gates.md；docs/governance/2026-09-07_execution_plane_boundary.md；docs/datasets/2026-10-05_qwen_model_metadata_v1.json 与两份 artifact validation receipts。
- 现行软件 pin: checker_v2.py = aeedf62b…（S0C 版）；adapter.py = dbb5b55b…；provenance.py = 75c3de…。一切以盘上现行字节为准重新求哈希。

## 授权默认值（照此执行，不再询问）
- **P2 feedback-right**（将 draft 的 Sec.6 五个空按此填成正式 v1）:
  1) 历史答案展示 = 只展示「实际执行过」的尝试字段（row / periods / delta_source / delta_target / unit）+ checker verdict；**gold 值永不展示**；
  2) 工具轨迹 = 参数 + 返回值，按 allow-list #2 全量展示；
  3) 修正展示 = 仅「已实际执行」的修正尝试及其工具轨迹（不做 before/after diff 呈现）；
  4) 留存/复用 = 供 WP-2 与学位论文记录；脱敏节选发布按 licence record 执行（发布动作另行授权）；
  5) attribution 文案 = 沿用 licence record 现有 derive-marking 句，不改文本。
  产出正式版 `docs/research/WP0_TATQA_FEEDBACK_RIGHT_CONTRACT_v1.md`（新文件；原 draft 原样保留，v1 头部注明取代关系）。
- **P3 actor** = Qwen3-8B `b968826d9c46dd6066d109eabc6255188de91218`（apache-2.0）；冻结设置: temp 0 / 单发 / max_out 512 / input cap 4096 / 经验块 600 / 无第三轮自动修复；不得改动任何设置（adapter 拒绝 per-item 泄漏）。
- **P4 预算/窗口** = 全流程 **≤300 次 actor 请求尝试、judge=0**；本卡 ≤40（S4+S5；含重试；传输重试 ≤4）；每调用记账（request id、tokens、exit、耗时）。

## 任务序列（S4→S7；**不得开始 S9**）
**F2–F4 actor 冻结**
- F2: 按 metadata 重新核 Qwen3-8B 工件哈希（只读）；F3: 记录设置 + 工具接口（adapter/checker 版本）+ 环境（python/torch/GPU）；F4: 产出 `research/tatqa_wp0_2026/wp2/ACTOR_FREEZE_RECEIPT.json`（revision、tokenizer、文件清单、设置、environment；任何字段后续改动=新收据）。
- 调用路径: 优先复用既有本地服务；无法复用时允许启动新 actor 服务（记录端口/参数/启动命令；遵守 safety gates 的显存/内存/进程门；**不得重启或扰动 :8004 judge 及其他生产服务**）。若无法在不违反安全门的前提下建立调用路径 → 停报 BLOCKED。
- 运行器: 编写薄 runner（读 adapter.build_prompt；两段调用: plan → 工具执行(calc) → consume result；逐 episode 记账落盘；无写回、无 per-item 设置）。
**S4 采集**: history 角色 4 origins / 8 episodes（2/origin；origin 盲 id；≤40 调用硬门内）。
**S5 开发段**: dev 角色 2 origins / 4 题；S 臂规则包锁死（静态 unit/period 规则，非反馈）；同样记账。
**S6 上下文**: 依 feedback 合同 v1 构建 E/C 块（真实执行 episodes）；**E/C token 差 ≤5%** 校验；盲 id；产出 E/C token-delta 收据、origin-disjointness 收据、near-duplicate isolation 收据。
**S7 冻结**: 组装 `research/tatqa_wp0_2026/wp2/PREREG_v1.md` + `PREREG_v1_RECEIPT.json`，全字段哈希 pin:
- protocol rev pin；**item/split freeze 收据**（引用 S1/S3/F5 收据 + **reserve 替换**：`tatqa_dace18a6…` → rank-23 `tatqa_cb626a5c…`，同哈希规则、收据留痕；pilot 8 / dev 2 / history 4 组成不变）；
- actor freeze；feedback 合同 v1；budget（300/0 judge）；analysis script（analyze_wp2.py）hash + bootstrap 方法与 seed（以 S10 骨架默认值为基线、现在冻结）；pilot 任务列表（16 题清单 + 顺序）；重复数=2 与顺序；checker_v2/adapter/provenance 哈希。
- skeleton 的 PENDING 字段在 **PREREG_v1** 中全部落值（原 skeleton 不动）。

## 停止点
- 泄漏/桥失败/预算超限/任何未授权调用（judge、外部网络、数据库）→ 立即停并报；
- S7 完成即停回报；**S9 pilot 需等 C 预检（S8）PASS 后另行派发**。

## 纪律
零 judge、零训练、零写回；不 git 操作；不改历史收据；每阶段落收据；结束写 `research/tatqa_wp0_2026/wp2/S4S7_EXECUTION_REPORT.md`。