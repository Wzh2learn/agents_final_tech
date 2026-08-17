# memory/STATE.md
更新: 2026-08-17 23:30（P0 修复专项收口: agent 路三层根因修复 + Loop B daemon 重载）

## 模式
守护模式。P0-1/P0-2/P1-1/P1-2 全闭环: agent 验证链路恢复真实承载 (验收两次 route=agent fell_back=false, 30.2s/33.7s)。拓扑定型不变: :8004 A3B 快路+视觉长期驻守; :8006 27B 仅 M2 验证链/judge/深度问答; :8005 退位; Route B CLOSED。等: ① 甲方首轮反馈 ② 导师反馈。缓至甲方反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。夜间不自行开新战线。

## Git
- HEAD: 4607bf2 → +本收口 commit (hash 见 dispatch_log 收口行)
- 三方对齐: GB10 commit → GitHub (直推, SSH 已复通) → 本机 merge
- 冻结工件未动: 甲方版 docx bc3785cb / 导师版 docx 929a8c65; 冻结节点 5 件 hash 全 OK

## 本轮战绩（P0 修复专项, 辅助线核验驱动）
- P0-1 三层根因修复 (agent 路 116/116 全回落 → 恢复承载):
  1. opencode 对无 limit 自定义模型默认 max_tokens=32000 > vLLM max-model-len 32768 → 400 → compaction 循环; 修: opencode.json gb10v 显式 limit {context:32768, output:4096}
  2. Qwen3.8 工具调用 XML 格式, hermes parser 不识别 (tool_calls=null, 答案被吞); 修: --tool-call-parser qwen3_xml (SOP FM6)
  3. vllm-gb10 构建 APC 默认关闭 (prefix_cache_queries=0), 逐轮全量 prefill → warm 45-85s; 修: --enable-prefix-caching (SOP FM7), warm 47s→30-34s
  - compaction guard 保留 (行为正确, "误杀"初判反转); 验收: :5050 真实承载 23:15:04 30.2s sources=1 / 23:20:49 33.7s sources=1
  - 边界如实: OCR meta-query 三轮题型 warm ~48-50s 超 45s 门回落 (题型分层完成率, 归 M2 菜单待拍板)
- P0-2/P1-1 Loop B daemon 重载: 旧 daemon (08-13 启动) 跑升级前脚本 → :8005 检查 FAIL 22h 无人接 + STEP 8/9 恒 SKIP; 重载后全 STEP 出判定, :8005 退位断言生效。T5 措辞更正 + 治理规则 (升级必重启 daemon, 以 verify-report STEP 出现为准)。
- P1-2 回归演练 PASS: 复现本次组合 (kill :8008 + 6 fallbacks) → STEP 8+9 双报警 → 恢复 → PASS + flip 入账。
- DECISIONS 治理新规 ×3 (自定义模型显式 limit / qwen3_xml parser / APC 强制开) + S4 条目 48h 条款矛盾清理; 回滚 31s 口径备案 (含 8s 保守等待, ≤30s 闸门边界案例)。

## 服务
- :5050 UP (route=on, OPENCODE_ASK_TIMEOUT=45, provider=local, embeddings=137; tmux coding-jinrong; 本轮未重启)
- :8004 A3B UP (快路+视觉); :8006 vLLM 27B UP (tmux vllserve, qwen3_xml + APC + limit 口径); :8008 thinking proxy UP (tmux thinking-proxy, 演练后重建); :8005 DOWN (退位); :8100 UP; :4096 sidecar UP (重载, gb10v limit 生效); :15432 PG UP
- tmux: coding-jinrong / graph-loop-b (禁杀) / opencode-serve / vllserve / thinking-proxy
- Loop B: 9 步升级版 daemon 已重载 (23:05), STEP 8/9 判定恢复; P1-2 演练 flip 记录入账
- known risk: PG idle 连接泄漏 ~1/h (清理 one-liner 在 THREADS); OCR 三轮题 45s 门贴边超 (菜单待拍板)

## 质量基线
- pytest 336 passed / 13 skipped (本轮未动 src/ 代码, 以 Loop B 周期复跑为准); docs_lint 0/0; 冻结节点 5 件全 OK
- eval v2: 确定性 16/16 / NF 0/9 / judge 5.0×4 @:8006
- B4: 累计 1092 asks; 切换点 (08-16 23:35) 后 162 条: agent clean 9 (含 4 条 compaction 期垃圾, sources=0) / fallback 148 / direct 5; 修复后新增真实完成 2 条 (30.2s/33.7s); 回滚实测 31s (保守口径)

## 下一步（等甲方/导师/用户）
1. 甲方首轮反馈 → 缓办清单 + agent 路完成率优化 (OCR 三轮题降轮次或抬超时, 归 M2 菜单拍板)
2. 导师反馈 → docs/31/视频微调或科研线推进 (NLPCC/CCIR 截稿日 pending 人工查)
3. 演示"准"路建议用两轮题型 (新鲜会话 ~30-34s 在 45s 门内)
4. 菜单待拍板 (存量): Docling NCAMC / OpenAI4S 科研线接入 / docs/28 #2→#1→#4 / M2 延迟菜单 (skill 预载/降轮次/档位感知超时)
5. apply 候选等窗口: 累计净值 + 产品份额① (SOP: 回归门禁 + delta)
