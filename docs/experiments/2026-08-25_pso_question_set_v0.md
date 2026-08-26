# W5 PSO 落点② — ABORT 2026-08-25 02:00:01

原因: W4 未完成 (状态: SKIPPED)

## 08-25 22:47 E4 补跑 — ABORT（根因坐实, #E4-PSO-ABORT）

- 启动闸全过: 无回滚 / E2 DONE / :8006 health 200 / Loop B 空闲（E1a 有界等待语义）
- 中止点: 判别力套件 `scripts/eval_checkpoint_discrimination.py` exit=1——W3 judge 工件 `logs/graph/eval/m2_judge_report.json`（01:51）四维 avg=None/n=0, n_unusable=16（judge 调用 :8006/v1/chat/completions 全 16 条 TimeoutError）, `eval_checkpoint_aggregate.py` L67 `_judge_avg` 对 avg=None 无防护 → TypeError 崩溃
- 连带更正: W3 "judge 5.0 零漂移"口径不成立（确定性+NF 部分仍属实）
- 修复候选（待明日窗口）: ① `_judge_avg` None 安全化（缺失→跳过该叶并注记） ② judge 腿单独重跑出可用 Z 基线 ③ judge 超时原因排查（01:51 收尾段 :8006 负载/客户端超时配置）
- 规则 D: PSO 落点② 维持 blocked（无首批数据）; 明日重跑前置 = ①②

## 08-26 凌晨重跑（夜间冲刺 Phase 3, 规则 D 复活）

状态: 完成 | 时点: 2026-08-26 00:56 | 口径: 纯工件计算（零网络/零 :8006 ask）, 消费 08-26 00:44 重跑的 m2_deterministic_report + 08-19 checkpoint_discrimination_report

- bank=19 题（16 确定性 + NF/judge/canary 代表）, QA mutants=7（M2-M8; M1/M9 解析树 mutant 为工件级, 文档化排除）
- 结果: B=8 全保持 keep_rate=1.0; **最小全保持预算 B=4**（patent 实施例 5.3.1 口径 lam2=0.3, 30 粒子×50 轮, 0.06s）
- 信号头牌: q01/q04/q05（各覆盖 6 mutant, 五叶全占）→ 题集裁剪时最后删
- 与 08-25 ABORT 两次对照: 本次前置（判别力套件工件）在位, 一次过; 前两次根因（W3 judge 全超时链）已由 F-J1/F-J2 修复
- 续跑计划: 第二批 = 判别力套件新鲜重跑后复算（规则 D 裁定: 登记+续跑）

## 08-26 第二批复算（续跑计划兑现, 规则 D）

状态: 完成 | 时点: 2026-08-26 22:36 | 口径: 纯工件计算（零网络/零 :8006）

- 前置: 判别力套件新鲜重跑（22:35, 9/9 PASS exit=0, 消费 08-26 00:45-01:00 重跑工件; judge 系 mutant 反映新数: M5 −5.9 / M6 −7.0 / M8 −4.9,−5.0,−5.0）; 08-19 原报告归档为 `checkpoint_discrimination_report_20260819.json`（不覆盖）
- 脚本增强: `pso_question_set_search.py` 加 `--disc` / `--out` 参数（默认行为不变, 解除硬编码单数据源）
- 产出: `logs/graph/eval/pso_question_set_v0_batch2.json`
- **delta 对首批: 零漂移**——bank=19 / mutants=7（M2-M8）/ 各 B（4/6/8/10/12）keep_rate=1.0、fitness、PSO 子集、greedy 对照、逐题信号排名逐项一致; 最小全保持预算仍 **B=4**; 信号头牌仍 q01/q04/q05（各覆盖 6 mutant）
- 解读: keep_rate 依赖 mutant 目标叶集合而非 delta 幅度, judge 工件刷新（5.0→4.94 系）不改变目标集合 → 题集裁剪结论对 judge 重跑**不变**; 若后续出现目标集合级变化（新增/删除叶）, 需再次复算
- 运行 0.06s（30 粒子×50 轮, seed 20260825 确定性）
