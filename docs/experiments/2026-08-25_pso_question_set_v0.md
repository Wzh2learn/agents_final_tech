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
