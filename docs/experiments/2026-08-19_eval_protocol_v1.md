# 评测协议 v1 — 判别力 + judge ensemble + evidence card 交付报告

> 状态: 活跃 | 更新: 2026-08-19 | 类型: v1 批复 ①⑤ 交付（增量/基线零漂移/冻版前后对照）
> 依据: 用户六项批复（08-19 00:29）①评测协议 v1 解冻 GO ⑤evidence card 并入 v1；K2 v0（9befc93）、K1 技巧清单 T2/T3/T10/T11
> 工件: logs/graph/eval/{checkpoint_discrimination_report, evidence_cards, m2_judge_report_k1, m2_judge_report_k3}.json（GB10, gitignored）

## 1 交付物清单（全部增量新增, 冻结零触碰）

| 资产 | 说明 |
|---|---|
| scripts/m2_eval_judge.py `--runs k` | K1 T2 ensemble: 每题 k 次打分取均值+std+逐次留档; T10 unusable 显式计数; T3 rubric 版本 v_k1 预注册元数据（只进报告, 不改 prompt 文本）; k=1 默认=历史行为零漂移 |
| scripts/eval_checkpoint_discrimination.py | 判别力测试床: 9 个确定性 mutant（契约失败/judge 降分/回归 FAIL/NF fail/工件缺失/灾难态）+ control 零漂移校验; 判据=目标叶降 >=2 分 + 非目标叶零移动 + graded 叶方向判据 |
| scripts/eval_evidence_cards.py | 批复 ⑤: 确定性报告+judge+NF 合成 per-case 证据卡 + leaderboard（A/B/C 分级） |
| scripts/run_eval.sh | [5/5] evidence cards 步骤（非阻塞）+ JUDGE_RUNS env 透传（默认 1 零漂移） |
| tests/test_eval_{judge_runs,checkpoint_discrimination,evidence_cards}.py | 27 新测试 |

## 2 冻版前后对照（批复 ① 验收项, GB10 活工件实测）

v1 聚合 vs K2 v0 冻版数字（2026-08-18_checkpoint_protocol_v0.md §2）:

| 项 | v0 冻版 | v1 复算 | 判定 |
|---|---|---|---|
| parse/qa Root Score | 10.0 / 10.0 | 10.0 / 10.0 | 零漂移 |
| 20 叶子 | 全 10.0 | 全 10.0 | 零漂移 |
| SR k=5/7/8 | 全 1.0 | 全 1.0 | 零漂移 |
| STABLE | True/True | True/True | 零漂移 |
| degraded | [] | [] | 零漂移 |

judge k=1 新鲜复跑（08-19 01:15, :8006 qwen38-27b-fp8）对 08-16 基线: 四维均 5.0, 16/16 逐题一致 → 跨日零漂移。

## 3 判别力结果（9/9 PASS, GB10 活工件）

| mutant | 目标叶 delta | 结论 |
|---|---|---|
| M1 两行 FAIL | doc.ok -10 / reconcile -10（hinge）; table.regression -1.7 / hit_rate -0.8（graded 方向过） | PASS |
| M2 exact_numeric 全失败 | -10.0 | PASS |
| M3 source_required 全失败 | -10.0 | PASS |
| M4 refusal_expected 全失败 | -10.0 | PASS |
| M5 faithfulness 5.0->2.0 | -6.0 | PASS |
| M6 citation 5.0->1.5 | -7.0 | PASS |
| M7 NF 3 条未落地 | -3.3 | PASS |
| M8 judge 工件缺失 | 三叶 -5.0（missing_score 降级路径） | PASS |
| M9 全部行 FAIL（灾难态） | doc.ok/regression/reconcile -10, hit_rate -4.6 | PASS |

**标定洞察（PSO/权重搜索输入）**：
1. rate 叶（row_pass_rate / hit_rate_achievement）是分级敏感——降幅 = 失败占比, 大基数下小回归只降 <2 分; hinge 叶（overall_status_binary / reconcile_derived）二值敏感。两类叶子在权重搜索中应区别对待。
2. hit_rate_achievement 即使灾难态（M9 全 FAIL）也只降 -4.6——diffs 按条数计罚而 expected pairs 基数大, 该叶对表级灾难钝感, v2 应改按行加权计罚（PSO 适应度设计注意点）。
3. k=5/7/8 阈值在全 10 基线上无区分度（v0 已自陈）, 判别力证据现由 mutant 套件承载, 阈值搜索等缺陷样本积累后再做。

## 4 judge --runs k A/B（K1 T2, :8006, 08-19 凌晨错峰）

| 口径 | 四维均分 | unusable | 耗时 | 结论 |
|---|---|---|---|---|
| k=1 | 5.0×4（16/16 逐题 5） | 0 | 9m09s | 与 08-16 基线逐题一致 |
| k=3 | 5.0×4（均值口径） | 0 | 27m31s | 64/64 cell std=0, 逐次 spread=0, 与 k=1 差 0/64 |

**如实口径**：满分基线上 ensemble 无可观测收益（天花板效应）——本 A/B 验证的是机制正确性（均值/方差/留档/失败计数全链路工作）与同进程 temp=0 稳定性, 不证明跨进程可复现（K1 T4）, 也不证明非满分判分下的漂移抑制。非满分判分样本来源 = 小模型矩阵候选答案（批复 ②, 进行中）——届时刻表才有判别空间。运行期决策: 生产 eval 维持 k=1（成本口径）, JUDGE_RUNS=3 作为争议复核开关文档化。

## 5 evidence card（批复 ⑤）

GB10 活工件合成: n=16, A=16 / B=0 / C=0（全契约过 + judge 全 5）, leaderboard 入 logs/graph/eval/evidence_cards_leaderboard.md。卡片含: 契约逐项 pass+证据 / judge 四维分+理由 / NF / route+延迟 / 检查点叶子映射。用途: 论文 B 附录追溯 + Loop C 审计原料 + 甲方问答质量台账。

## 6 pytest 口径更正（对账审计沉淀）

GB10 全库（HEAD f8f0a07）: **379 passed / 13 skipped / 0 failed**。13 skip 全部为 08-10 起的 conftest 显式策略（legacy chat/KB e2e、DB fixture、HMM 配置、websocket 异步 fixture）, 非环境抖动。08-18 台账"364 passed/1 skipped"与 conftest 政策不符（13 项 legacy skip 该次未生效, 口径异常）, 以本报告口径为准, STATE 同步更正。

## 7 运行期事件记录

- 08-19 00:01/00:34 Loop B overall FAIL = STEP 4 git 脏文件检测（GB10 本地 schema_suggestions 计数+dispatch_log）, 非服务退化; 两文件随 4fc251c 入账后报警源清除。
- 01:55 临时暂停本机演示 kiosk（loop_demo.py/demo_controller.py）: 凌晨持续 ask 与 judge A/B 争用 :8006 slot, B4 日志出现 105s/47s fallback 污染样本; B4 >=100 ask 目标不受影响; 收口前恢复。

## 8 待办（不入本轮）

- 判别力套件挂 run_eval.sh --full 可选档（现独立脚本, 手动跑）
- 阈值/权重搜索（PSO, 批复 ③ 缓办, 依赖缺陷样本积累 + 导师专利时间表）
- 跨进程 judge 一致性复验（换 GPU/进程后, K1 T4）
