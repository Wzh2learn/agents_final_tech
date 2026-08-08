# memory/THREADS.md — 未决线索

## 技术未决（来自 blocked_questions.md 现存条目）

### Phase 1 数据抽取 (2026-08-01 19:45) — RESOLVED 带遗留
- 问题: /api/m2/compare/positions 对 jiaxing 返回空; PGVector metadata product_name 与查询不匹配。
- 状态: 2026-08-03 23:35 双根因已修 (服务进程缺 PGDATABASE_URL + 表类型判断改用 table_name+matched_schema 联合); positions 0→2, 24 tests passed。
- 遗留: 110/137 chunk 的 product_name 为空或正则碎片 (OCR 样本), 记录不修。
- 下一步: 若跨文档对比出现实质错漏, 再重做 ingest metadata 注入。

### OCR meta-query (2026-08-03 23:36) — RESOLVED (2026-08-05, Loop A)
- 问题: "哪个样本通过 OCR 解析了交易对账单" 被 scenario1 caitong HTML 特别提示样板 chunk 抢占排序 (0.4385)。
- 状态: **已修, QA 15/15=100%**。根因三层: 样板 chunk 含"交易对账单"字面量 (内容碰撞) + BM25 stub 未实现 (混合检索退化纯向量) + 正确证据 chunk (ocr_table_1:r0, dist 0.4420 ~第35名) 被 top_k 候选池截断。修法: 137 chunks 非破坏性 cmetadata 标记 doc_type (email_notice=15/ocr_table=11/parse_meta=17/reconcile=17/header_meta=15/statement=62, 工具 scripts/m1_rag_tag_doctype.py 幂等) + smart_retrieve 对含 "ocr" 查询补一路 doc_type=ocr_table 过滤召回 + 重排 (ocr_table schema 命中 x1.35 / 其余 x1.15 / email_notice x0.70)。未 --reset、未删灌 chunk、未重启 :5050。
- 遗留: :5050 重启后 curl 复验 (Loop D 择窗); BM25 stub 未实现为既有系统问题, 记录不修; coord_table 未纳入 ocr_table 语义 (见交付说明 §6)。详见 logs/graph/loop_a_ocr_metaquery_result.md。

## 其他技术线索

- Schema 口径 (2026-08-09 P1): 冻结运行时 schema (~/wzh/m1_samples, 07-30 版) 已落后 config/m1_table_schema.json (嘉合/卢样本 synonyms 演进)。CLI 与 :5050 已统一走 resolve_schema_path() (config/ 优先)。是否把运行时副本同步到 config 版 = 待 Loop D 决策 (需刷新 frozen_hashes.txt manifest)。
- HTML 邮件链路 (2026-08-09 P1): 匹配步已复活 (scripts/m1_html_email_parse.py), 但 .msg -> HTML -> 表格的提取步脚本未入库 (仅存产物 html_extracted/*_tables.json); 重提取需重写 (4.1 一并)。

- VLM :8007 (Qwen3-VL-8B-Instruct GGUF): **VERIFIED-CLOSED** (2026-08-08) — hf-mirror 已同步官方 GGUF 仓库, Q4_K_M 5.0GB + mmproj-Q8_0 752MB 下载成功, llama.cpp 2.16 llama-server 起 :8007 一次点亮; NCAMC 截图手测输出合法 markdown 表格 (首调 119s); parser 重跑 engine=vlm-8007 (trafax/wavefax 走通), 但传真样本命中率与 vision-8004 持平 (trafax 2/4;8/11;4/11, wavefax 4/7), 单文件 OCR 延迟 3-8min (vision-8004 ~30s) → 默认关闭, :8007 已 kill。重启方法: llama-server -m ~/wzh/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf --mmproj .../mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf --port 8007 --alias Qwen3-VL-8B-Instruct -ngl 99 -c 8192, parser _try_vlm_table 自动接入 (M1_VLM_TIMEOUT 建议 ≥240)。优化候选: 送 VLM 前图片降采样至 ≤1600px (vision tokens -75%)。
- MCP server x3: **RESOLVED** (2026-08-05 S1) — start 脚本改 venv-first + conda fallback, smoke 3/3 过, opencode.json 注册并随 agent 链跑通; vision 走 :8004 mmproj (:8007 停摆)。
- OpenCode 多 agent (docs/21 §1.4): 显式指令链已端到端验证 (2026-08-05 S3: M1 链 PASS + M2 Q1 PASS 带引用 + tabular PASS, 见 docs/experiments/2026-08-05_opencode_e2e.md); 中性 prompt 自动委派已验证 CLOSED (2026-08-09: 默认 build agent 不委派专职 agent, 但直接调 jinrong-rag MCP 检索作答, 掩码保留正确; 结论: 无需显式 --agent 也能走 MCP, 但查询策略不受 m2-qa 契约约束, 生产路径仍应显式指定 agent 或走 :5050 适配层)。
- Qoder CLI (2026-07-29 侦察): BLOCKED-auth, 等用户注册并提供 PAT 后再做 Phase 2 连通性实测。
- ZhikunCode 重建 (2026-08-03): 官方 Dockerfile pip 直连 pypi.org 极慢, 需临时 aliyun 镜像源 (已还原) 或向上游提 PR。
- codex CLI 对 qwen3.8-max 报 "model metadata not found" 警告: 无功能影响, 记录不修 (2026-08-03)。
- .msg→htmlBody 预处理仍是临时脚本未入库; parse_html 已入库覆盖解析环节 (T3 遗留)。
- embedding 本地切换: **RESOLVED** (2026-08-05, 用户拍板不恢复 SILICONFLOW key): .env 加 LOCAL_EMBEDDING_MODEL_PATH=qwen3-embedding-0.6b + DEVICE=cpu, 同模型 drop-in 无需 re-ingest。MCP 链实测生效 (knowledge_search vector=3); :5050 已重启载入 (重启验证见 dispatch_log 2026-08-05)。**口径更正**: "RAG QA 14/15" 从来不是降级态成绩 — QA 脚本 (m1_rag_qa.py) 经 setdefault 从未降级; 曾降级的仅 :5050/MCP 端点进程 (缺 env 走 fallback)。14/15 唯一失败 = OCR meta-query 内容碰撞 (email_caitong.html 含"交易对账单"字样), 已派 Loop A 正式任务修 (禁 --reset)。

### scenario1 gap 台账（2026-08-04 审计定基线，漂移校准）
- NCAMC 垂直布局: **CLOSED** — pymupdf 坐标重建, 0→1 表 75% 命中 (b927efe; 见 docs/21 执行结果节)
- 华泰/TraFax OCR 纯文本: **CLOSED** — OCR prompt 增强 markdown 表格输出, 华泰 0→1 (35.7%) / TraFax 0→3 (9ea3754)
- email body: **CLOSED (有界)** — HTML body 提取, 3 封 0→9 表 (国金 70% / 财通 42% / 南华初值 24%)
- 南华 HTML: **遗留 (低优先)** — T3 已提升 24%→65.7%, parse_html(bs4) 入 PARSERS + synonyms 扩展 (html_table_4 88.9%), 不再恋战
- OCR meta-query: **RESOLVED** (2026-08-05 Loop A) — 15/15=100%, doc_type 标记 + smart_retrieve 过滤召回/重排 (见本文件上条)
## 甲方侧待确认

- 跨期对比: 需甲方提供多期对账单数据才能解锁 (现仅单期/单文档内对比)。
- email body 格式: 已解决 (有界) — HTML body 路径已验证 (3 封邮件 0→9 表), 仅在甲方要求时扩展。
- M2 正式业务指标: 阻塞于甲方批准的 label-to-source 映射与人工标注 (AGENTS.md 架构边界)。
- 部署加固: M1_API_TOKEN/M1_ADMIN_TOKEN 启用、systemd 进程守护、Prometheus 接入, 待甲方运维确认。

### A2 灰度审计闭环项（COMPLETE — c5a8ecf 交付, Loop C 复核 ACCEPTED, CONDITIONAL 解除 2026-08-07）
- ① F1 (MEDIUM): chat_persistence PG I/O 在全局锁内且 psycopg 无超时 → 加 connect_timeout + 查询级超时 (先例 memory_saver.py:60), 或移出锁; 不修须入账 known_risk
- ② F2: compare-intent 绕过补接线级回归测试 (route=on + 对比类问题 → 走直连且 ask_via_opencode 未被调用)
- ③ F3/F4: trust_env=False 断言守卫 + sources:[] 显式拒绝透传测试 + echo 负例 + strip sample_id 尾部 `.`
- 体量预计 <30min, 完成后 Loop C 复核转 ACCEPTED; 不阻塞当前灰度 (route=on 继续)。报告: docs/experiments/2026-08-06_audit_loop_c_flash_fixes.md
- F5 known_risk (2026-08-06 裁定不修, 用户确认): async 端点 /api/m2/ask 同步调用 adapter/直连 LLM → 阻塞事件循环最坏 51s(env)/133s(default), 病态清理级联 +500s; workers=2 仅部分缓解。既有模式非回归, 归入 B 阶段 (网关/原生入口改造, docs/25 路线 A/B) 处理。

### 2026-08-07 differential 审计待办（源: docs/experiments/2026-08-06_differential_phase3_to_head.md, 33 项 0 CRITICAL/1 HIGH/8 MEDIUM）
- E1 (HIGH): **RESOLVED** (2026-08-07 00:26) — 生产口径复验 rerank=True 下 RAG QA 15/15 通过; rescore 被 rerank 架空不影响 QA 结果, docs/23 15/15 两口径均成立。
- E4 (MEDIUM, 一行修): m1_rag_ingest.py:341 传 document="" 使 email_notice 标记词检查恒 False; email_* 样本一旦进入 ingest 即标签漂移。
- P1/P2/P3 (随手修级): shell 误映射 / proxy debug 日志截断 / stdio hygiene 补齐 (报告处置序节)。
- E7 (记录漂移更正): commit 9f3e655 message 声称 16 测试, 实测 15 — 审计抓出, 台账更正。
- T1 INFO 残留: 会话 delete/list 端点断言缺口; opencode.json skill:allow 全局继承 (F6 后续可加 "skill": "deny")。
- 运维注意: :5050 需重启一次才能载入 c5a8ecf 的 PG 超时加固 (最近重启 22:45 早于该 commit); 重启窗口须用户批准。

### TODO: jinrong-rag MCP 接入 Loop C (Claude Code) — 已评估不实施 (2026-08-06 T3.2)
- 价值: Loop C 审计时可直接查 m1_parsed_statements 核验 RAG/QA 类声明 (如答案溯源正确性), 不必绕 curl :5050 或手跑脚本。
- 接线方案 (实施时用): `claude mcp add jinrong-rag -s user -- bash ~/wzh/projects/agents_final_tech/scripts/start_mcp_server.sh`; start 脚本已 venv-first + 自载 .env (PGDATABASE_URL/embedding), 配置侧无需放任何 env/密钥; 备选 .mcp.json (project scope, 不 commit)。
- 前提/风险: Claude Code 对 MCP tool 首次调用要权限确认 (skip-permissions dispatch 下自动过, 交互模式需 permissions allowlist); 多一个 PG + 本地 embedding (CPU) 消费方, 负载可忽略; 审计独立性略降 (判定方可触被测数据源) — 保持 "MCP 只取抽查证据, 判定仍以独立复算为准" 纪律。
- 触发条件: Loop C 审计开始频繁需要核验 RAG 答案时, 或 B 阶段 (docs/25 路线 B) OpenCode 原生入口落地后。
- 2026-08-07 用户批复: 维持观望, 不启动。
### Agent 面对的 CLI 表面盘点 (2026-08-06 T3.3, 仅清单, 动手前过用户)
| 位置 | 现状 (prompt 内联) | 建议 |
|---|---|---|
| opencode.json m1-extraction.prompt | 内联绝对路径长命令: {项目venv}/python scripts/m1_statement_parser.py --samples-dir ~/wzh/m1_samples --json /tmp/opencode/m1_extract.json --compact-summary /tmp/opencode/m1_compact_summary.json 2>&1 \| tail -20 | 封装 scripts/opencode_m1_extract.sh (venv 探测 + 固定输出路径 + tail 内置), prompt 只留一行入口 |
| opencode.json evidence-verifier.prompt | cat /tmp/opencode/m1_compact_summary.json (一次) | 已最小化, 不动 |
| opencode.json m2-qa.prompt | 无 CLI, 纯 MCP 调用 (jinrong-rag_knowledge_search) | 不动 |
| opencode.json tabular-researcher/runner | prompt 描述"对显式提供的数值行做有界实验", 未发现内联命令 | 下轮复核确认 |
- 收益: prompt 缩短 (省 token + 减漂移)、脚本入口可独立 smoke test、路径/参数变更只改脚本不改 prompt。
- 风险: 封装后 agent 对参数的临场调适能力下降 (如换样本目录) — 脚本留 --samples-dir 透传参数即可。
- ripgrep 缺失 (GB10): skill-map 无法运行 (硬依赖 rg); 08-08 尝试下载 GitHub release aarch64 静态包失败。处置: 记录不阻塞, 三端 skill 一致性由 skill-doctor + sync 清单人工核验覆盖; 有内网镜像或用户提供 rg 二进制时再装。
