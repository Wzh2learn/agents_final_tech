# W5 PSO 落点② — ABORT 2026-08-25 02:00:01

原因: W4 未完成 (状态: SKIPPED)

## 08-25 22:47 E4 补跑 — ABORT（根因坐实, #E4-PSO-ABORT）

- 启动闸全过: 无回滚 / E2 DONE / :8006 health 200 / Loop B 空闲（E1a 有界等待语义）
- 中止点: 判别力套件 `scripts/eval_checkpoint_discrimination.py` exit=1——W3 judge 工件 `logs/graph/eval/m2_judge_report.json`（01:51）四维 avg=None/n=0, n_unusable=16（judge 调用 :8006/v1/chat/completions 全 16 条 TimeoutError）, `eval_checkpoint_aggregate.py` L67 `_judge_avg` 对 avg=None 无防护 → TypeError 崩溃
- 连带更正: W3 "judge 5.0 零漂移"口径不成立（确定性+NF 部分仍属实）
- 修复候选（待明日窗口）: ① `_judge_avg` None 安全化（缺失→跳过该叶并注记） ② judge 腿单独重跑出可用 Z 基线 ③ judge 超时原因排查（01:51 收尾段 :8006 负载/客户端超时配置）
- 规则 D: PSO 落点② 维持 blocked（无首批数据）; 明日重跑前置 = ①②
