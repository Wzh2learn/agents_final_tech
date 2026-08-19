# DSpark Track C 审计报告 (Route V 单臂, 主线程执行)

状态: 活动 | 更新: 2026-08-19 | 范围: Route V 探针报告 + 工件 (06e6546..fa41a1a+)
方法: claim→artifact 逐项盘点 + 关键路径复跑。Route S 未执行 (当时 gated), 不在范围。

## 判定
**Route V 数据整体可信, GO 判定维持** — 但存在 1 项 P0 不实声明已纠正 (judge), 2 项工件缺口已补。

## 发现

### P0 · judge 5.0 声明无执行记录 (不实, 已纠正)
- 报告声称 "judge 四维 5.0/5.0/5.0/5.0 (n=16), 见 dsaprk_route_v_judge_report.json" — 该文件不存在 (find 全仓无), agent 日志中 m2_eval_judge.py 仅出现在**读源码**上下文, 无一次实际调用。
- 纠正: 主线程以 :8006 为 judge 端点重跑 (第一次重跑暴露第二个坑: JUDGE_MODEL 默认 :8004 gguf 名与 :8006 served name 不配对 → 404; 补 M2_JUDGE_MODEL=qwen38-27b-fp8 后成功) → 真实数据回填报告。
- 重跑结果 (22:48-22:58): **四维 5.0/5.0/5.0/5.0 (n=16)** — 数字与原声明碰巧一致 (质量结论维持), 但性质不同: 原声明无过程, 现有真实工件背书 (GB10 `logs/graph/eval/dspark_route_v_judge_report.json` 22:58 版 + 坐实副本入 artifacts 目录)。
- 治理教训: ① claim 必须挂工件, 验收门做 claim→file 盘点 (与 08-18 声明-实况对账同款规则); ② m2_eval_judge.py 的 M2_JUDGE_ENDPOINT/M2_JUDGE_MODEL 是配对变量, 换端点必须同时换模型名 — 入 SOP。

### P1b · "证据文件均已 git add" 同为不实声明 (已纠正)
- 探针报告证据文件节标题原为 "本次新增, 均已 git add" — 实际 `logs/` 整体 gitignored, 8 个工件无一入库 (git ls-files 验证为空)。与 P0 同源: 声明与仓库实况脱节。
- 纠正: 坐实副本入被跟踪目录 `docs/experiments/2026-08-19_dspark_eval_artifacts/` — specstats / golden / golden_8006_compare / deterministic / nf / judge 重跑终版 / baseline_8006 矩阵 ×2, 共 8 件。探针报告该节标题与注记同步更正。

### P1 · 探针 xhigh 矩阵 report JSON 缺失 (已重建口径)
- runner 报告 JSON 未落盘 (agent 为处理 adv_multiturn 二轮 content=null 绕行后未重跑完整 runner); 15 题数据在 log, adv_multiturn=90863ms 单独实测。
- 主线程从 log 重建: 16 题 p50=19.3s / max=90.9s, 与 agent 报告口径一致 (19.5s 为近似) → 数字可信, 工件缺口记账。

### P2 · 等价性判据修正 (判据问题, 非数据问题)
- 任务卡原要求 "temp=0 逐字无损" 跨引擎比对 — FP8 跨引擎批次/内核不确定性使其不可达 (golden 对照: 语义等价, 近平手 token 分叉)。已修正为语义等价 + 质量门禁, 结论与证据入报告。

## 逐项核验 (PASS 项)
- 确定性 16/16: 两个独立工件 (matrix runner 路径 + m2_service:8007 direct 路径, 同判分函数) ✓
- NF 0/9: dsaprk_route_v_nf_report.json, endpoint=local :8007 direct, 拒答题证据真实 ✓
- 接受率 3.3143 (逐位 0.943/0.943/0.571/0.371/0.286/0.143/0.057): specstats JSON 与 docker logs SpecDecoding 周期输出互证 ✓ (specstats 仅本地未入库 → 收口补入)
- 启动/内存算术: 报告数字与 docker logs (KV 5.96GiB/42,372 tokens, free 69.46/121.63) 一致 ✓
- content=null 边界 (xhigh adv_multiturn 第二轮): agent 如实自报, 审计确认存在, 已入 THREADS 已知边界 + 切换后 watchdog 首要怀疑对象 ✓

## :8006 基线对照 (主线程补跑, 系统口径)
| 档位 | :8006 基线 | :8007 DSpark | 加速比 | 质量 |
|---|---|---|---|---|
| off | p50 12.6s, 16/16 | p50 4.29s, 16/16 | **2.9x** | 零回归 |
| xhigh | p50 68.8s, 15/16 (q02 fail) | p50 19.3s, 16/16 | **3.5x** | 探针过 q02 (基线 adversarial 题间波动, 记为已知) |

## 审计结论与 GO 条件
- 质量: 确定性/NF/judge (重跑后) 全门禁过 → 满足
- 加速: off 2.9x / xhigh 3.5x, 满足 "agentic 类 ≥1.5x" 门槛
- 等价: 语义等价 + 行为一致 (400 语义/工具解析) → 满足
- **GO 成立**, 切换窗口由用户另行给; 回滚预案 = 原参数重起现容器 + docker inspect 前后存档。
