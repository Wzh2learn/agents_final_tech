# memory/THREADS.md — 未决线索

## 技术未决（来自 blocked_questions.md 现存条目）

### Phase 1 数据抽取 (2026-08-01 19:45) — RESOLVED 带遗留
- 问题: /api/m2/compare/positions 对 jiaxing 返回空; PGVector metadata product_name 与查询不匹配。
- 状态: 2026-08-03 23:35 双根因已修 (服务进程缺 PGDATABASE_URL + 表类型判断改用 table_name+matched_schema 联合); positions 0→2, 24 tests passed。
- 遗留: 110/137 chunk 的 product_name 为空或正则碎片 (OCR 样本), 记录不修。
- 下一步: 若跨文档对比出现实质错漏, 再重做 ingest metadata 注入。

### OCR meta-query (2026-08-03 23:36) — ACCEPTED
- 问题: "哪个样本通过 OCR 解析了交易对账单" 被 scenario1 caitong HTML chunk 抢占排序 (0.4385)。
- 状态: OCR 溯源元数据已入库 (解析引擎=vision-8004) 但查询词"交易对账单"主导排序; 14/15=93% 高于 80% gate, 接受。
- 下一步(暂不做): ingest 时给解析元数据 chunk 加 "OCR=是" 字面量; 注意 --reset 重灌会丢 scenario1 chunk (ingest 只扫顶层目录)。

## 其他技术线索

- VLM 恢复条件 (2026-08-03 关闭): 待国内镜像同步 Qwen3-VL-8B-Instruct GGUF, 下载 Q4_K_M + mmproj-Q8_0 后用 LM Studio llama-server 起 :8007; _try_vlm_table 集成代码已就位。
- MCP server x3: **RESOLVED** (2026-08-05 S1) — start 脚本改 venv-first + conda fallback, smoke 3/3 过, opencode.json 注册并随 agent 链跑通; vision 走 :8004 mmproj (:8007 停摆)。
- OpenCode 多 agent (docs/21 §1.4): 显式指令链已端到端验证 (2026-08-05 S3: M1 链 PASS + M2 Q1 PASS 带引用 + tabular PASS, 见 docs/experiments/2026-08-05_opencode_e2e.md); 中性 prompt 自动委派仍未验证。
- Qoder CLI (2026-07-29 侦察): BLOCKED-auth, 等用户注册并提供 PAT 后再做 Phase 2 连通性实测。
- ZhikunCode 重建 (2026-08-03): 官方 Dockerfile pip 直连 pypi.org 极慢, 需临时 aliyun 镜像源 (已还原) 或向上游提 PR。
- codex CLI 对 qwen3.8-max 报 "model metadata not found" 警告: 无功能影响, 记录不修 (2026-08-03)。
- .msg→htmlBody 预处理仍是临时脚本未入库; parse_html 已入库覆盖解析环节 (T3 遗留)。
- SILICONFLOW_API_KEY 缺失 (2026-08-05 S3 发现, 等人决策): key 不在 :5050 environ/.env/仓库 → vector+BM25 系统级降级, :5050 与 MCP 检索均走 fallback+本地 bge-reranker (RAG QA 14/15 为降级态成绩); 恢复与否由用户定, agent 红线不碰 key。

### scenario1 gap 台账（2026-08-04 审计定基线，漂移校准）
- NCAMC 垂直布局: **CLOSED** — pymupdf 坐标重建, 0→1 表 75% 命中 (b927efe; 见 docs/21 执行结果节)
- 华泰/TraFax OCR 纯文本: **CLOSED** — OCR prompt 增强 markdown 表格输出, 华泰 0→1 (35.7%) / TraFax 0→3 (9ea3754)
- email body: **CLOSED (有界)** — HTML body 提取, 3 封 0→9 表 (国金 70% / 财通 42% / 南华初值 24%)
- 南华 HTML: **遗留 (低优先)** — T3 已提升 24%→65.7%, parse_html(bs4) 入 PARSERS + synonyms 扩展 (html_table_4 88.9%), 不再恋战
- OCR meta-query: **ACCEPTED** — 14/15=93% 高于 80% gate (见本文件上条)
## 甲方侧待确认

- 跨期对比: 需甲方提供多期对账单数据才能解锁 (现仅单期/单文档内对比)。
- email body 格式: 已解决 (有界) — HTML body 路径已验证 (3 封邮件 0→9 表), 仅在甲方要求时扩展。
- M2 正式业务指标: 阻塞于甲方批准的 label-to-source 映射与人工标注 (AGENTS.md 架构边界)。
- 部署加固: M1_API_TOKEN/M1_ADMIN_TOKEN 启用、systemd 进程守护、Prometheus 接入, 待甲方运维确认。
