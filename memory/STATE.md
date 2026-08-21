# memory/STATE.md
更新: 2026-08-22 01:50（夜间 graph engineering loop 收口: 拍板 a/A 入账, T1-T4 落地, 纯台账+模板+脚本只读增强, 零运行时配置变更）

## 模式
守护模式。本轮: 漂移修正扫荡（thinking-OFF 口径更正入账）+ 任务卡/验收清单模板固化 + status.sh 增强 + A→B→C 前置清单。
等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 用户专利终审 + 导师时间表（专利件冻结, 用户亲发）③ kiosk A1 方案窗口
已关闭: L1 基线口径（拍板=a）/ L3 路径选择（拍板=A）/ D3 k=5 随 DSpark 退出作废 / cron 24h 条目已删

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮资产: T1 口径更正 7 处 + 拍板章节 / T2 templates/ 两模板 / T3 status.sh+b4_checkpoint.py / T4 docs/29 附录 / STATE+dispatch

## 拍板入账（用户 2026-08-22 凌晨）
- **拍板一 · L1 口径=a**: 生产 m2-qa thinking 实际 OFF（L2 证据链）→ "xhigh 轨迹超预算"归因作废, 正解 = 串行多步（p50=3/p95=5/max=15）× 每步 7-15s; 08-19 "xhigh 起步"批复标"前提失效, 待 L1 矩阵复测"（不撤销不涂改, 数据裁定）。L1 更名 **thinking 档位裁定矩阵**: off 现状有生产数据不重跑, 只补 medium/xhigh 两腿（各 16 确定性 + NF + judge 四维 + 端到端延迟与 thinking token 分布）; 显式注入 reasoning_effort 走探针, 跑完还原, 生产默认口径不动（还原写入验收清单）
- **拍板二 · L3 路径=A**: 等 timothystewart6 新 tag, 不自建。探针默认排 L1 基线之后（前置: L1 基线完成 / pull 避大 I/O 与矩阵同夜 / :8007 既有协议 / GO-NO-GO 报用户后才许申请生产窗口）; **08-29 checkpoint**: 仍无 tag → 路径 B 再评估报告（不自动启建）; 新 tag ~800 commit 跨度, 等价性三连 + GB10 启动 SOP 重标定为探针必跑项; 盯梢命令维持 ledger 现状
- **杠杆序重排**（docs/32 §6 备忘录）: 准路主导项 = step 数 → "减 step（3→2 省 1/3）+ 终结孤儿续跑"升为根治第一梯队; thinking 档位降为质量维度而非延迟救星; 只记账不动手, 实施排矩阵之后

## 本轮战绩（T1-T4）
- T1 修正清单: THREADS 3 处加注 + 拍板章节 / DECISIONS 1 处加注 / d2 报告 §4 更正注 / dflash 备忘 §6 更正注 / drafter ledger L3 拍板 A 章 / docs/32 头部+§3 注+§6 备忘录 / GB10 b4_checkpoint_20260821_2322.md 加注
- T2: templates/task_card_template.md（七节, **前提假设清单必填**——thinking-OFF 教训: 每张卡先答"假设了什么, 一分钟怎么证伪"）+ templates/acceptance_checklist_template.md（声明→验证命令→实测值三列, 范例二: c9b2b07 / f8898c9）
- T3: b4_checkpoint.py 抽 compute()+pct()（main 输出逐字不变）; status.sh 端口补 8006/8007/8008 + Loop B 补 loop_b.log 最近 PASS 行 + B4 两列口径实时输出（回滚点 3295 起 + 全量）
- T4: docs/29 附录 A→B→C 前置清单 8 项（现状/差距, 只列不实施）+ 头部状态同步（L1 补全/L2 落地）
- 教训入账: 声称的决策状态与运行实况脱节一周无人发现——T1 即偿还; 模板"前提假设清单"为机制化防复发

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, 不重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :8100 UP; :15432 PG UP
- Loop B 30min 周期: agent_watchdog ALARM = **设计内信号**（agent 完成未恢复前预期持续, 记台账不当事故）
- kiosk 播放中; B4: 回滚点 3294（08-21 23:51）; 分段: DSpark era 3093-3287 / 验证期 3288-3294 / 回滚后自 3295

## 质量基线
- eval: 确定性 16/16 + NF 0/9 + judge 四维 5.0
- pytest: 379 passed / 13 skipped（08-22 收口全量重跑, 167s, logs/graph/pytest_latest.txt）
- docs_lint: GB10 为准

## 下一步
1. 08-23/24 错峰: **thinking 档位裁定矩阵** medium/xhigh 两腿（拍板 a 口径; 探针注入, 生产不动, 跑完还原 = 验收项）
2. 矩阵解读框架 = L2 定论（step 数主导）: go = 质量不降且延迟实质改善; no-go = 数据入账转 step 削减杠杆
3. L3: 盯 timothystewart6 新 tag; **08-29 checkpoint** 无 tag → 路径 B 再评估报告
4. 杠杆序（记账, 矩阵后实施）: 减 step（3→2）+ 孤儿终结 > context 瘦身（残差 8-10k 为靶）> thinking 档位（质量维度）
5. 缓办: 甲方反馈 → B4 分布分析; kiosk A1 窗口; 专利终审用户亲发; C4 VL-8B; K3 批跑; NLPCC 核实
