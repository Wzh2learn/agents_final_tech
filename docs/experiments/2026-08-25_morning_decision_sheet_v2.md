# 判定一页纸 v2 (2026-08-25, E6 回填版)

状态: 待圈选 | 更新: 2026-08-25 | 取代: 2026-08-25_morning_decision_sheet.md 的门禁状态段与规则评估层 (v1 因晨间序列卡零执行而欠账, 本版补齐)

## 0. 门禁状态更正 (E1b)

v1 一页纸写 gate=UNKNOWN/0 次运行——**更正为 PASS**:
- 工件: logs/graph/eval/pool_fix_verify_20260825.md GATE_PASS 段, 00:28 判定, 共 3 次运行 (00:16 首轮 + 复验)
- dispatch #POOL-GATE-PASS (08-25 00:28) 在案
- v1 误报根因（钉死）: gate 脚本 `head -c 400` 字节截断切断多字节字符（工件 position 657 实测 invalid continuation byte, "资产市"后一字符被腰斩）, assemble_morning.py 的 rd() 吞掉严格 read_text 的 UnicodeDecodeError 返回空串 → gate=UNKNOWN。修: rd() errors="replace" + gate 判定用 dispatch_log（#POOL-GATE-PASS）做兜底源 + 截断字符安全化（iconv -c）; 回归用例 = 今晚 PASS（verdict=GATE_PASS runs=3）
- 门禁后事实: 病灶零复发 (23:54 分段点后 IdleSessionTimeout 0 / 检索失败 0 / 兜底 0 / dispose 救援 0)

## 1. 圈选表 (5 数字)

| # | 指标 | 数值 | 出处 |
|---|------|------|------|
| 1 | 门禁结果 | PASS @00:28, 3 次运行, rearm=0 | pool_fix_verify 工件 + #POOL-GATE-PASS |
| 2 | 3929 后干净段完成率 | 59 尝试 / 2 完成 = 3.4% (样本构成: canary 为主, 见规则 0 注记) | b4_checkpoint.py 段 3929→3988 |
| 3 | 超时近失占比 | 非"近失": 45s 截断时 step1 在途 26/59 (44%), 每 step 位 p50=30-34s, 全程放大 | 2026-08-25_e3_step_duration_diagnosis.md |
| 4 | eval vs 基线 | 确定性 16/16 + NF 0/9 零漂移; **judge 腿全超时 (n_unusable=16, 四维 avg=None), judge 对比缺失** (见 §8 更正) | eval_summary + m2_judge_report |
| 5 | step 复测三点对比 | 今晚 49.09s·p50=4 / T1 Arm A 49.6s·p50=4 / 健康代 7-15s/step·p50=3 | e2_step_retest_20260825.md |

## 2. 规则 0 (样本闸)

干净段 (3929 起) n=59 ≥ 40, **过样本闸**。注记: 样本以 Loop B canary 题型为主 (kiosk 已关闭), 完成率结论代表性限 canary 题型; eval/手工段样本另计。

## 3. 规则 A (timeout) — 不触发, 超时 (a) CLOSED

- 数据: 干净段完成率 3.4% < 10%, 且超时近失不占主导 (E3: 45s 截断时 44% 仍在 step1, 每 step 位 p50=30-34s = prefill/context 27k 膨胀下的全程放大, 不是"差一步")
- 预提交规则判定: <10% 或近失不占主导 → 不抬超时, 出系统诊断方案
- **结论: 超时 (a) 45→60-75s CLOSED 入账; 诊断已执行 = E3 逐步耗时诊断** (菜单已出不动手)
- 注: v1 一页纸原推荐 (不抬超时, 走诊断) 与预提交规则同向, 本条只是补记依据

## 4. 规则 B (T1 减 step 重评) — 不触发, T1 结论维持

- E2 补跑 (13 题经 :5050 agent 路, 22:34-22:46): 13/13 PASS, wall p50=49.09s / mean=49.2s, **steps p50=4 / mean=4.67** (分布 4×8 / 5×3 / 9×1, join 12/13, canary 混入 4 行已注)
- 判据: steps p50 ≤3.5 → 判污染重开; **≥4 → T1 维持**。实测 p50=4 → **T1 基线未被池病污染** (T1 Arm A 49.6s/p50=4 在干净环境复现), 原杠杆队列不变
- 三点对比: 今晚实测 49.09s·p50=4 ≈ T1 Arm A 49.6s·p50=4 >> 健康代 7-15s/step·p50=3 → 延迟病灶仍在 (E3 定位: prefill/context 膨胀), 与池修复无关

## 5. 规则 C (FK 窗口)

FK 竞争修复 + PG 池泄漏根治 + M1_B4_LOG_PATH 已于 08-23 一窗全激活完成; 剩 **FK 水位线边角** (08-25 08:14 新增 1 条: cleanup_sessions MAX_SESSIONS=50 边界 session=51 偶删在途) 为单件窗, 草稿在案 (2026-08-25_fk_watermark_fix_draft.md), **时机等用户另行批, 不催**。

## 6. 规则 D (PSO) — blocked (E4 补跑中止, 根因坐实)

E4 22:47 补跑: 启动闸全过 (无回滚 / E2 DONE / :8006 200 / Loop B 空闲), 但判别力套件 exit=1 中止 (#E4-PSO-ABORT):
- 根因: W3 judge 工件 logs/graph/eval/m2_judge_report.json (01:51) 四维 avg=None/n=0, n_unusable=16——judge 调用 (:8006/v1/chat/completions) **全 16 条 TimeoutError**; eval_checkpoint_aggregate.py L67 `_judge_avg` 对 avg=None 无防护 → 崩溃
- 修复候选 (待明日窗口): ① `_judge_avg` None 安全化 (缺失→跳过该叶并注记, 不计 0) ② judge 腿单独重跑出可用 Z 基线 ③ judge 超时原因排查 (01:51 收尾段 :8006 负载 / 客户端超时配置)
- PSO 落点② 维持 blocked, 无首批数据; 明日重跑前置 = 上述①②

## 7. 规则 E (积压)

维持挂起不开新战线: dify 5 份甲方规则 docx 挖掘 / 任务 2 改版设计稿 / NLPCC workshop 核实 / image/.env 旧 PNG 去留 / admin token fail-open 收口时机。无新解锁理由。

## 8. 更正记录 (本轮回填中发现)

- W3 "eval 16/16/0/5.0 零漂移" 口径收窄: 确定性 16/16 + NF 0/9 部分属实; **judge 腿全超时, "5.0 对照"无数据支撑**, 今后引用 W3 质量点只引确定性+NF。
- 门禁状态: UNKNOWN → PASS (§0)。

## 附: E5 Loop B 反复归因行

18:44 FAIL = STEP 9 agent_watchdog (last 30 asks: 0 completions, ≥25 fallbacks)——设计内信号, 对照 08-23 23:51 先例属 canary 抖动类; 19:17/19:51 延续, 20:24 翻回 PASS, 22:05 九项全绿。只分类不动手。
