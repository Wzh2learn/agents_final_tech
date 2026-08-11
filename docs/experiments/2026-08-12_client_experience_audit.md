# 甲方发送前自体验审计 + docs/23 声明复测 (T1+T2)

> 日期: 2026-08-12 | 执行: Loop D 主线程 (playwright 自动走查 15 步 + curl 活系统复测)
> 范围: :5050/m1 全表面 + docs/23 关键数字声明逐条复测
> 红线遵守: 未重启 :5050 / 未改前端 / T1 只发现不修复 / docs/23 冻结不改文(漂移只入账上报)
> 原始数据: [audit_raw.json](2026-08-12_client_experience_audit/audit_raw.json) (15 步耗时 + console_errors=0)
> 走查脚本: scripts/t1_client_experience_audit.py (已入库, 可复跑)

---

## 一、T1 甲方视角体验审计

**总览**: 15 步全过 / 0 控制台错误 / 0 按钮无响应 / 0 面板空白。

### 演示前必修
**无。**

### 口头解释 (演示话术需覆盖)
| # | 现象 | 证据 | 建议话术 |
|---|---|---|---|
| 1 | M2 问答每轮 ~20-25s | step 10-13: 20.9/21.4/25.2/22.0s | route=on 时先走多 agent 验证链路, 18s 未回即自动回落直连出答; 答案与直连一致。正式演示可切直连 (~2s), 修复 a+b 落地后恢复"快与准菜单" (见 2026-08-11_agent_latency_diagnosis.md) |
| 2 | 等待期显示 "thinking..." | step 09-13 tail | 正常状态提示, 非卡死; 回落机制保证最终出答 |
| 3 | 持仓对比出现 "(未知)/-" | step 14: 博时新策略混合A 2 条持仓名称为 (未知) | 该样本原始数据即掩码/缺名称字段, 系统如实呈现缺省而非编造; 真实客户数据不会有此占位 |
| 4 | OCR 样本解析延迟口径 | 复测 536ms (缓存) vs 08-09 冷启 9.6-22.9s | 首次解析走视觉模型看图识字 (全本地推理), 同一文件内容哈希命中本地缓存后秒级; docs/23 "16-71s" 为早期冷启动实测区间 |

### 可接受 (样式/体验小疵, 不阻塞)
- Download M2 文件名含临时名 (`tmpveipzmga.txt_m2_payload.json`) — F8 已知样式项, 台账在案
- 精确解析开关切换后 notice='' 无 toast — 开关即时生效, UI 静默
- 建议映射面板 pending=0 — walkthrough 后无待审建议; 6 条 hold 态按设计不显示 (hold=留待人工拍板)
- 首屏/空态文案完备 (step 01/15): "输入问题开始对话，支持多轮追问。"

### 脚本测量瑕疵 (已补偿, 不影响结论)
03/04 上传步的等待条件命中过早 (tableCount 初值 '-'), ms=21/14 无效 → 以 API curl 复测补偿: 嘉合 PDF 63ms, TXT 16ms。审计脚本等待条件留待下次维护窗修正。

---

## 二、T2 docs/23 声明复测表

| 声明 | 复测方法/结果 | 结论 | 处置 |
|---|---|---|---|
| embeddings=137 | /api/health/full → 137, provider=local | ✅ 一致 | - |
| 非 OCR 延迟 <2.1s | 精确路 73ms ✓; **默认路 3.3-9s ✗ 漂移** | ⚠️→✅ | 根因=嘉合 基金份额/可用份额 双列争用同一标准字段 → 默认路每跑触发 LLM 兜底。T4① 当晚修复 (新增 可用份额 标准字段) → 63ms 复测通过 |
| 嘉合解析 50-60ms | 精确路 73ms / API 63ms | ✅ 同量级成立 | - |
| OCR 16-71s 区间 | 当晚复测 536ms = .ocr_cache 内容哈希磁盘缓存 (m1_statement_parser.py:534-577); 08-09 冷启证据 9.6-22.9s | ⚠️ 口径说明 | 不清生产缓存; 漂移方向为更快, 列口头解释 |
| 简称匹配 | compare/positions "嘉兴民安"→2 条持仓 ✓; QA 简称问 "嘉兴民安的总资产"→ 4013****.83 带出处 ✓ | ✅ 一致 | - |
| QA 15/15 生产口径 | scripts/m2_eval_deterministic.py 打 :5050 生产端点 → **16/16 PASS** (题集已扩至 16, 含对抗题; 直连判定口径) | ✅ 成立 | 感知 20-30s/题为 route=on 回落延迟, 答案正确性不受影响 |
| TraFax 两轮口径 | 一轮 [50/81.8/63.6] / 当前 [50/81.8/81.8], 辅助线已抽验自洽 | ✅ 一致 | - |

**漂移处置**: docs/23 已冻结不改文; 两条漂移按规则入 memory/THREADS.md 台账并随本报告上报。其中"默认路延迟"一项当晚即由 T4① 修复并复测通过, 台账标 RESOLVED。

---

## 三、关联闭环 (同晚 T3/T4)

- **T3 Loop C 差分审计** (5535bdf..504810c): 判定 CONDITIONAL — 见 [2026-08-12_audit_loop_c_differential.md](2026-08-12_audit_loop_c_differential.md)。FC-1 (diff 引入同义词碰撞, MEDIUM) 当晚已修; FC-4 fail-open auth / FC-5 async 阻塞复评为 HIGH 存量, 台账延期项不变。
- **T4① schema 沉淀**: 交易对账单+证券持仓明细 新增 `分红方式`/`可用份额` 标准字段 (分红方式 原挂靠 摘要 同义词, 语义错位; 可用份额 原与 基金份额 争用 持仓数量 单槽位) → 嘉合×8 87.5→100、TraFax 表3 81.8→100、NCAMC 75→87.5、nanhua 75→87.5; 基线 --rebuild 后门禁 15 pass/0 warn/0 fail; 默认路延迟 3.3-9s→63ms。
- **T4① 附带修复**: 自学习写入器 `_append_schema_suggestions` 重写文件时丢失 applied/rejected 审计区 (本次 T2 复测实跑触发, 00:00:56) → 修复为保留原有顶层键, 并从 HEAD 恢复丢失区段; 2 条已被手工字段覆盖的陈旧建议 (可用份额→持仓数量 / 交易费用→财汇局征费) 移入 rejected 防 FC-1 式碰撞复发。
- **T4②**: m2_eval_number_faithfulness.py 失败计入退出码, 接入 run_eval.sh 第 [3/4] 步; .env.example 补 M1_API_TOKEN 条目 (审计 FC-4 条件 2)。

---

## 四、截图清单

| 文件 | 内容 |
|---|---|
| 2026-08-12_client_experience_audit/01_empty.png | 首屏空态 (三面板 + 引导文案) |
| 2026-08-12_client_experience_audit/02_sample.png | Sample 解析完成 (1 表, review=PASS) |
| 2026-08-12_client_experience_audit/06_sugg.png | 建议映射面板 (pending=0) |
| 2026-08-12_client_experience_audit/07_schema.png | 规则配置模态 (14 字段行) |
| 2026-08-12_client_experience_audit/13_qa.png | M2 问答多轮 (含简称/追问/溯源) |
| 2026-08-12_client_experience_audit/14_compare.png | 持仓对比 ((未知) 占位现象) |
