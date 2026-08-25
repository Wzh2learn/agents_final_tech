# 判定一页纸 v3 — 2026-08-26 晨（自动汇编 2026-08-26 01:02, 规则机械裁定版）

> 用法: 每项 = 数据 + 选项 + 推荐, 圈选即可。工件路径全部可点开复核。
> blocked_questions.md 摘要: # blocked_questions.md（夜间队列歧义/缺前置登记, 2026-08-25 建）

> 规则: 歧义/缺前置 → 登记一行（时点/问题/缺什么/跳项去向）, 不停车; 白天判定一页纸时统一过目。

（今夜暂无 — 截至 00:50 各 W 前置齐备）

## ① 超时 (a) 45→60-75s 是否还需要
**数据**:
- 段 3429（侧车修复后, 含池病污染段）: 761 尝试 / 62 完成 = 8.1%（**池病灶污染不作数**, 归因见 2026-08-24_segment_d_q06_attribution.md）
- 3929 后干净段（池修复后）: 261 尝试 / 8 完成 = 3.1%（样本=Loop B canary 题型, 代表性限 canary）
- 门禁工件: gate 判定 GATE_PASS（3 次运行, 12min 闲置 q06 命中 @0.7889 + warn 219/fallback 0）
- 每日 eval（最新重跑）: 16/16 确定性; E2 复测: steps p50=4 wall p50=49092ms; 近失代理(step3+4 截断占比, E3)=39%
```
# B4 checkpoint 20260826_0102

## agent 路两列口径（判定主口径; route 字段记最终路径, 尝试=完成+超时回落）
- agent 尝试总数 (attempted): 261
- agent 完成数 (无回落): 8
- 回落率: 96.9%  (= 1 - 完成/尝试)
  - 超时回落 (latency>=45000ms): 253
  - 快速回落 (<45000ms, sidecar 不可用等, 不计入尝试): 0

## 全量分布
- segment: line 3930 .. 4191 (n=262)
- 最终路径分布: direct=253 (其中回落 253), agent=8
- status: {'ok': 262}
- latency (rows >=100ms): p50=49164ms p95=61015ms n=261
- suspect test/cache rows (<100ms, 已排除出统计): 1
  - line 4150 2026-08-25T23:30:53 route=direct lat=22ms fell=False

Judgment rule (user approval 08-20 #3): 回落率 >60% -> 第一怀疑 content=null; 查无解释报用户拍板。

report written: /home/testuser/wzh/projects/agents_final_tech/logs/graph/b4_checkpoint_20260826_0102.md

```
**选项**: A 维持 45s | B 抬 60s | C 抬 75s | D 不动超时, 只走结构性根治（减 step + context 瘦身）
**推荐**: D-不动超时, 只走结构性根治（规则 A CLOSED, 诊断=E3/E2）

## ② T1 减 step 杠杆重评（W4 复测）
**数据**: 今晚 steps p50=4 mean=4.67 wall p50=49092ms（n=13）; 对照 T1 Arm A 49.6s/steps p50=4 mean=4.4; 健康代 steps p50=3
**选项**: A 重开减 step 杠杆 A/B（M3 终答瘦身优先） | B 维持 T1 还原判定, 结构性减 step 照原计划
**推荐**: T1 还原判定维持（steps 未回落, 病灶非 T1 基线主因, 按原路线图走结构性减 step）

## ③ FK 边界窗口提案
**数据**: FK 竞争根因 = cleanup_sessions 水位闸 MAX_SESSIONS=50 偶删在途会话（08:14 新增 1 条级边角）; 修复草稿已就绪（docs/experiments/2026-08-25_fk_watermark_fix_draft.md, a/b 菜单 + diff + 测试清单 + 回滚口径）
**选项**: A 与下个 :5050 窗口合并激活（推荐） | B 单独开窗 | C 缓办
**推荐**: A（草稿就绪, 合并零额外成本）

## ④ 积压亮点（各一行: 为何未动 + 解锁条件）
- dify 5 份甲方规则 docx 挖掘（08-12 起）: 未动=等甲方首轮反馈定优先级; 解锁=甲方反馈到达或用户直接批
- 任务 2 改版设计稿（08-11 起）: 未动=待用户决策备忘录 D 系列圈选; 解锁=圈选后入代码窗
- NLPCC 2026 workshop 核实: 未动=需人工查官网窗口; 解锁=用户核实或授权代查

## ⑤ 夜间执行链回顾（证据索引）
- W1 门禁: GATE_PASS（pool_fix_verify_20260825.md）
- W2 复验: 同文件 00:40 段（Loop B 周期 + canary 复跑 + 归因计数）
- W3 每日 eval: EVAL_PASS（w3_daily_eval_20260825.md）
- W4 step 复测: w4_step_retest_20260825.md + w4_step_stats.json
- W5 PSO 落点②: bank=19 题, QA mutants=7, 全保持最小预算=B=4（2026-08-25_pso_question_set_v0.md + pso_question_set_v0.json）
- Loop B 夜间周期: -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json
[2026-08-26 00:51:44] REPORT: overall=FAIL -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json

## 规则机械裁定（预提交规则, 零圈选; 08-26 v3）
- 规则 0（样本闸）: 干净段尝试 261 条 → 过闸, 结论有效（已按规则 0 裁定）
- 规则 A（timeout）: 干净段完成率 3.1% → <10%: 不抬超时, timeout (a) CLOSED, 走结构性诊断 (E3/E2)（已按规则 A 裁定）
- 规则 B（T1）: 复测 steps p50=4 → ≥4: T1 结论维持, 原杠杆队列不变（已按规则 B 裁定）
- 规则 C（FK 窗口）: FK 水位闸修复 = 单件 :5050 窗（M1_B4_LOG_PATH/PG 根治已在位）, 时机等用户批, 不催（已按规则 C 裁定; 窗口卡草稿见附录）
- 规则 D（PSO）: 首批数据落盘 → 登记 + 续跑第二批（已按规则 D 裁定）
- 规则 E（积压）: dify 挖掘 / 任务 2 改版稿 / NLPCC 核实 维持挂起, 无新解锁理由（已按规则 E 裁定）
- 规则 F（本卡预批）: 今夜不开 :5050 重启窗（交付日上午卫生优先, GUC+pre_ping 兜底在位）; FK 修复 = 待批窗口卡（已按规则 F 裁定）

## 挂起项（规则外, 只建议不裁定）
1. F-J3 孤儿轨迹治理（两案共同上游根因）: 提案 docs/experiments/2026-08-26_fj3_orphan_governance_proposal.md, 推荐序 b→a→d→c, 等批
2. 减 step 组合拳（context 瘦身 + M4）: E3 结论 = 单杠杆不够, 组合预期 20-25s 进预算, 等拍板序
3. FK 窗口时机: 草稿就绪, 与规则 F 互锁, 等用户一字"批"

## 红线核对
:8004/:8006 配置零改动 ✓（夜间仅 :5050 预批路径）| 专利文档未碰 ✓ | API key/HF token 零打印 ✓ | 不对外发送 ✓ | 甲方数据零进入 ✓（PSO 用公开样本+合成 mutant）
