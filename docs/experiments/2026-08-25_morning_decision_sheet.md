# 判定一页纸 — 2026-08-25 晨（夜间队列自动汇编 2026-08-25 03:50）

> 用法: 每项 = 数据 + 选项 + 推荐, 圈选即可。工件路径全部可点开复核。
> blocked_questions.md 摘要: # blocked_questions.md（夜间队列歧义/缺前置登记, 2026-08-25 建）

> 规则: 歧义/缺前置 → 登记一行（时点/问题/缺什么/跳项去向）, 不停车; 白天判定一页纸时统一过目。

（今夜暂无 — 截至 00:50 各 W 前置齐备）

## ① 超时 (a) 45→60-75s 是否还需要
**数据**:
- 段 3429 预注册判据: 491 尝试/53 完成 = 10.8%（**注: 段 D 池病灶污染不作数**, 归因见 2026-08-24_segment_d_q06_attribution.md）
- 3929 后干净段（池修复后）: 59 尝试 / 2 完成 = 3.4%（样本=Loop B canary 题型, 代表性限 canary）
- 门禁工件: gate 判定 UNKNOWN（0 次运行, 12min 闲置 q06 命中 3508.55@0.7889 + 零新警告）
- W3 每日 eval: EVAL_PASS（基线 16/16/0/5.0）; W4 复测: steps p50=None wall p50=Nonems
```
# B4 checkpoint 20260825_0350

## agent 路两列口径（判定主口径; route 字段记最终路径, 尝试=完成+超时回落）
- agent 尝试总数 (attempted): 59
- agent 完成数 (无回落): 2
- 回落率: 96.6%  (= 1 - 完成/尝试)
  - 超时回落 (latency>=45000ms): 57
  - 快速回落 (<45000ms, sidecar 不可用等, 不计入尝试): 0

## 全量分布
- segment: line 3930 .. 3988 (n=59)
- 最终路径分布: direct=57 (其中回落 57), agent=2
- status: {'ok': 59}
- latency (rows >=100ms): p50=49148ms p95=61135ms n=59
- suspect test/cache rows (<100ms, 已排除出统计): 0

Judgment rule (user approval 08-20 #3): 回落率 >60% -> 第一怀疑 content=null; 查无解释报用户拍板。

report written: /home/testuser/wzh/projects/agents_final_tech/logs/graph/b4_checkpoint_20260825_0350.md

```
**选项**: A 维持 45s | B 抬 60s | C 抬 75s | D 不动超时, 只走结构性根治（减 step + context 瘦身）
**推荐**: C-抬 75s 或先做结构性根治（完成率 <5%, 抬超时收益存疑, 优先减 step/瘦身）

## ② T1 减 step 杠杆重评（W4 复测）
**数据**: 今晚 steps p50=None mean=None wall p50=Nonems（n=None）; 对照 T1 Arm A 49.6s/steps p50=4 mean=4.4; 健康代 steps p50=3
**选项**: A 重开减 step 杠杆 A/B（M3 终答瘦身优先） | B 维持 T1 还原判定, 结构性减 step 照原计划
**推荐**: 数据缺失, 人工判

## ③ FK 边界窗口提案
**数据**: FK 竞争根因 = cleanup_sessions 水位闸 MAX_SESSIONS=50 偶删在途会话（08:14 新增 1 条级边角）; 修复草稿已就绪（docs/experiments/2026-08-25_fk_watermark_fix_draft.md, a/b 菜单 + diff + 测试清单 + 回滚口径）
**选项**: A 与下个 :5050 窗口合并激活（推荐） | B 单独开窗 | C 缓办
**推荐**: A（草稿就绪, 合并零额外成本）

## ④ 积压亮点（各一行: 为何未动 + 解锁条件）
- dify 5 份甲方规则 docx 挖掘（08-12 起）: 未动=等甲方首轮反馈定优先级; 解锁=甲方反馈到达或用户直接批
- 任务 2 改版设计稿（08-11 起）: 未动=待用户决策备忘录 D 系列圈选; 解锁=圈选后入代码窗
- NLPCC 2026 workshop 核实: 未动=需人工查官网窗口; 解锁=用户核实或授权代查

## ⑤ 夜间执行链回顾（证据索引）
- W1 门禁: UNKNOWN（pool_fix_verify_20260825.md）
- W2 复验: 同文件 00:40 段（Loop B 周期 + canary 复跑 + 归因计数）
- W3 每日 eval: EVAL_PASS（w3_daily_eval_20260825.md）
- W4 step 复测: w4_step_retest_20260825.md + w4_step_stats.json
- W5 PSO 落点②: (PSO 未跑/未完成)（2026-08-25_pso_question_set_v0.md + pso_question_set_v0.json）
- Loop B 夜间周期: -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json
[2026-08-25 03:39:07] REPORT: overall=FAIL -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json

## 红线核对
:8004/:8006 配置零改动 ✓（夜间仅 :5050 预批路径）| 专利文档未碰 ✓ | API key/HF token 零打印 ✓ | 不对外发送 ✓ | 甲方数据零进入 ✓（PSO 用公开样本+合成 mutant）
