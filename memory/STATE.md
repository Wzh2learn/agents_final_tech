# memory/STATE.md — 当前快照（覆写式）
快照: 2026-08-05 | 写入: Loop D（交付链激活专项 S1-S5 完成）

## 本轮产出（交付链激活，commit 06623d3）
- S1 MCP 启动修复 PASS: 3 个 start_*.sh + run_opencode_gb10.sh 改 venv-first（conda 留 fallback）; smoke 3/3 过; vision 实测走 :8004 mmproj（M1_VLM_ENDPOINT=:8004，5.7s 出 markdown 表）; :8007 保持停摆
- S2 OpenCode 运行时 PASS: 二进制 1.18.3; 单轮 QA 7.9s; stability 20/20 all_passed; 挂起根因 = opencode run 等 stdin EOF，非交互调用必须 </dev/null
- S3 多 agent e2e（证据: docs/experiments/2026-08-05_opencode_e2e.md）:
  - opencode.json 修复: m1-extraction/evidence-verifier/m2-qa mode subagent→all; tabular steps 2→4; m2-qa 首查逐字用用户完整问题
  - M1 链 PASS: m1-extraction 47.4s（6 样本 100% 解析）+ evidence-verifier 31.2s verdict PASS
  - M2 Q1 PASS（带引用，与 :5050/api/m2/ask 交叉一致）; Q2 PARTIAL（诚实拒答，未编造）
  - tabular-runner PASS: tabpfn v2 1.685s
  - 关键发现: SILICONFLOW_API_KEY 缺失 → vector+BM25 系统级降级，:5050 与 MCP 检索均走 fallback+本地 bge-reranker（0.989 是 rerank 分）; 探针确认 MCP≡API，Q2 差距在查询措辞+35B 提取能力
  - stdout 污染修复: config_loader/bm25_retriever print→stderr（此前污染 MCP JSON-RPC 流）
- S4 skill 层 PASS: opencode.json 加 skills.paths=["skills"] + permission.skill=allow; 新增 skills/graph-loop-rules/SKILL.md; opencode 枚举出 13 个 skill（含 jinrong-docs-sync、graph-loop-rules）
- S5 决策文档 docs/25_交付架构决策.md: 路线 A（FastAPI 网关）vs 路线 B（OpenCode 原生入口），推荐先 A 后 B，待用户/甲方拍板，未实施

## 系统状态
- git: 本机 ≡ GB10 ≡ origin @ 06623d3（三方对齐）
- pytest: 227 passed / 13 skipped（commit 后远端复跑全绿）
- 服务: :8004 up（Qwen3.6-35B-A3B + mmproj）; :8007 down（预期）; :5050 up 未动（甲方演示随时可用）; docker zhikuncode+pgvector; tmux coding-jinrong/graph-loop-b/graph-loop-d
- 红线: 冻结节点未触碰; API key 未触碰; 72B 未加载; 未对外发送; Loop B 未扰动

## 下一步
- 等人决策①: SILICONFLOW_API_KEY 是否恢复（决定检索能否回到 vector+BM25；红线约束我们不碰 key）
- 等人决策②: docs/25 路线 A/B 拍板（页面后端切 OpenCode 链）
- 甲方交付仍待: 审阅 docs/23 + 发送版 docx（路由见 docs/24）
- 遗留线索唯一台账: memory/THREADS.md
