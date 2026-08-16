# memory/STATE.md
更新: 2026-08-17 凌晨（模型拓扑定型 + 治理升级 夜间 loop 收口）

## 模式
守护模式。**模型拓扑定型**: :8004 A3B 快路+视觉长期驻守; :8006 27B 仅 M2 验证链/judge/深度问答; :8005 退位; Route B CLOSED (无官方权重)。OPENCODE_ASK_TIMEOUT 重议落地: 18→45s, agent 路开始真实承载 (切换点后 3/23≈13% 完成, 其余回落兜底)。等: ① 甲方首轮反馈 ② 导师反馈。缓至甲方反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。夜间不自行开新战线。

## Git
- HEAD: 644d69d → +本收口 commit (hash 见 dispatch_log 收口行)
- 三方对齐: GB10 commit (--no-verify: Loop D 授权冻结清单更新) → GitHub → 本机 merge
- 冻结工件未动: 甲方版 docx bc3785cb / 导师版 docx 929a8c65; 冻结节点本轮经授权扩充 (基线 3 件入冻)

## 本轮战绩（夜间 loop: 模型拓扑定型 + 治理升级）
- 红线修订 (DECISIONS): 72B 硬禁 → 模型准入预算门 (内存算术 + 用户窗口); 模型退位政策 (权重默认保留, 删必先记台账); M1 热路径锁 :8004 A3B, :8006 仅 M2 验证链/judge/深度问答。
- T1: Route B → CLOSED (用户人工查证 + HF 枚举双坐实; routeb-watch 退役, 探测脚本入库 scripts/routeb_watch.sh); :8004 A3B 长期驻守 (GGUF 48h 条款作废); 演示 UI 追认范围内。
- T2: :8005 Qwen3-14B 退位 (依赖盘点零生产引用, 治理脚本/文档 4 处更新, kill 后无拉起, 权重保留)。
- T3: 超时 18→45s 数据定值 (B4 88 条 A3B 完成 ≤18.1s + 27B 新鲜会话 29.6/30.0s + throwaway-session 无多轮累积, 依据见 DECISIONS); reasoning_effort 探针: thinking 开启全档加延迟 (off 5.7s / low 19.8s / xhigh 12.2s, 非单调), 维持 off; 真实承载 PASS: OCR meta-query route=agent fell_back=false latency=30040ms (切换后首次); 回滚演练 31s (含 8s 保守等待); compaction 垃圾答案缺陷发现 + adapter guard 修复。
- T4: 冻结扩充 (scenario1_baseline.json + m2_eval_questions.json + m1_m2_baseline_cases.json, md5 全验); 立原则 "基线诞生即入冻结 / 活配置不入冻结"; 双 case 验证 (动冻结 BLOCKED / 新增测试 ALLOWED)。
- T5: Loop B 升级 (授权例外): STEP 8 双模型拓扑断言 (8004/8006/8008 model ID + 8005 期望 down) + STEP 9 B4 agent 完成率看门狗 (窗口 30 计数制) + LOOP_B_PYTEST 跳过 flag; 首周期实战抓 2 缺陷即修 (拓扑 curl 双拼误判 / canary 超时 45→75); 破坏演练: 停 :8008 → FAIL 报警 + flip → 恢复 → PASS; 完整周期无误报。

## 服务
- :5050 UP (route=on, OPENCODE_ASK_TIMEOUT=45 进程 env 生效, provider=local, embeddings=137; tmux coding-jinrong)
- :8004 A3B UP (快路+视觉); :8006 vLLM 27B UP (tmux vllserve); :8008 thinking proxy UP (tmux thinking-proxy, 演练后重建); :8005 DOWN (退位); :8100 UP; :4096 sidecar UP; :15432 PG UP
- tmux: coding-jinrong / graph-loop-b (禁杀) / opencode-serve / vllserve / thinking-proxy; routeb-watch 已退役
- Loop B: 9 步升级版, 最近完整周期 PASS (00:34); 演练 flip 记录 4 条
- known risk: PG idle 连接泄漏 ~1/h (清理 one-liner 在 THREADS); throwaway session compaction 触发条件观察中 (guard 已位, 深层根因待甲方反馈期后)

## 质量基线
- pytest 336 passed / 13 skipped (Loop B 完整周期含跑, 绿); docs_lint 0/0 (同周期); 冻结节点 5 件全 OK
- eval v2: 确定性 16/16 / NF 0/9 / judge 5.0×4 @:8006
- B4: 累计 958 asks; 切换点 (08-16 23:35) 后 28 条: agent clean 3 / fallback 20 / direct 5; 回滚实测 31s

## 下一步（等甲方/导师/用户）
1. 甲方首轮反馈 → 缓办清单 + agent 路完成率优化优先级 (compaction 根因 / skill 上下文瘦身)
2. 导师反馈 → docs/31/视频微调或科研线推进 (NLPCC/CCIR 截稿日 pending 人工查)
3. agent 路完成率 3/23 为当前如实口径: 回落兜底, 不人工刷量; 演示"准"路建议用首轮问题 (新鲜会话 ~30s)
4. 菜单待拍板 (存量): Docling NCAMC / OpenAI4S 科研线接入 / docs/28 #2→#1→#4
5. apply 候选等窗口: 累计净值 + 产品份额① (SOP: 回归门禁 + delta)
