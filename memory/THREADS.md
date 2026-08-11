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
- 遗留: ~~:5050 重启后 curl 复验 (Loop D 择窗)~~ **CLOSED (2026-08-09)**: 重启后生产端复验 PASS (sources=3, TraFax+WaveFax 正确溯源, 08-09 两次复验); ~~BM25 stub 未实现~~ **CLOSED (2026-08-09)**: 真 BM25 已实现并 flag 化 (M2_ENABLE_BM25 默认 false, A/B 零增益决策不修); coord_table 未纳入 ocr_table 语义 (见交付说明 §6)。详见 logs/graph/loop_a_ocr_metaquery_result.md。

## 其他技术线索

- Schema 口径 (2026-08-09 P1): 冻结运行时 schema (~/wzh/m1_samples, 07-30 版) 已落后 config/m1_table_schema.json (嘉合/卢样本 synonyms 演进)。CLI 与 :5050 已统一走 resolve_schema_path() (config/ 优先)。是否把运行时副本同步到 config 版 = 待 Loop D 决策 (需刷新 frozen_hashes.txt manifest)。
- HTML 邮件链路 (2026-08-09 P1): 匹配步已复活 (scripts/m1_html_email_parse.py), 但 .msg -> HTML -> 表格的提取步脚本未入库 (仅存产物 html_extracted/*_tables.json); 重提取需重写 (4.1 一并)。

- VLM :8007 (Qwen3-VL-8B-Instruct GGUF): **VERIFIED-CLOSED** (2026-08-08) — hf-mirror 已同步官方 GGUF 仓库, Q4_K_M 5.0GB + mmproj-Q8_0 752MB 下载成功, llama.cpp 2.16 llama-server 起 :8007 一次点亮; NCAMC 截图手测输出合法 markdown 表格 (首调 119s); parser 重跑 engine=vlm-8007 (trafax/wavefax 走通), 但传真样本命中率与 vision-8004 持平 (trafax 2/4;8/11;4/11, wavefax 4/7), 单文件 OCR 延迟 3-8min (vision-8004 ~30s) → 默认关闭, :8007 已 kill。重启方法: llama-server -m ~/wzh/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf --mmproj .../mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf --port 8007 --alias Qwen3-VL-8B-Instruct -ngl 99 -c 8192, parser _try_vlm_table 自动接入 (M1_VLM_TIMEOUT 建议 ≥240)。优化候选: 送 VLM 前图片降采样至 ≤1600px (vision tokens -75%)。
- MCP server x3: **RESOLVED** (2026-08-05 S1) — start 脚本改 venv-first + conda fallback, smoke 3/3 过, opencode.json 注册并随 agent 链跑通; vision 走 :8004 mmproj (:8007 停摆)。
- OpenCode 多 agent (docs/21 §1.4): 显式指令链已端到端验证 (2026-08-05 S3: M1 链 PASS + M2 Q1 PASS 带引用 + tabular PASS, 见 docs/experiments/2026-08-05_opencode_e2e.md); 中性 prompt 自动委派已验证 CLOSED (2026-08-09: 默认 build agent 不委派专职 agent, 但直接调 jinrong-rag MCP 检索作答, 掩码保留正确; 结论: 无需显式 --agent 也能走 MCP, 但查询策略不受 m2-qa 契约约束, 生产路径仍应显式指定 agent 或走 :5050 适配层)。
- Qoder CLI (2026-07-29 侦察): BLOCKED-auth, 等用户注册并提供 PAT 后再做 Phase 2 连通性实测。
- ZhikunCode 重建 (2026-08-03): 官方 Dockerfile pip 直连 pypi.org 极慢, 需临时 aliyun 镜像源 (已还原) 或向上游提 PR。
- codex CLI 对 qwen3.8-max 报 "model metadata not found" 警告: 无功能影响, 记录不修 (2026-08-03)。
- ~~.msg→htmlBody 预处理仍是临时脚本未入库~~ **RESOLVED** (2026-08-09, c863235): scripts/preprocess_msg.py 已入库 + 8 单测; parse_html 覆盖解析环节。
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
- 运维注意: ~~:5050 需重启载入 c5a8ecf PG 超时加固~~ **CLOSED**: 08-07 起已载入; 2026-08-09 02:0x 再次重启载入 compare 模糊匹配 (24770c4) + M2_ENABLE_BM25 flag (13a37b8), 生产验证 PASS (嘉兴民安短名 0→2 持仓)。

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
- ~~ripgrep 缺失 (GB10)~~ **RESOLVED** (2026-08-10 核实): rg 15.1.0 已安装于 ~/bin/rg (bashrc 已含 PATH), skill-map 可运行; 陈旧条目本轮清除。

## 2026-08-09 Phase 4 结论入账
- **4.2 VLM 降采样实验 CLOSED**: _vlm_downsample(≤1600px, M1_VLM_MAX_PX) 解决延迟(华泰 22.9s/TraFax 10.3s/WaveFax 9.6s, 远优于 90s 门槛), 但 TraFax 命中率 [50,81.8,81.8]→[0,0,100] 显著劣化(8B Q4 对乱版传真输出退化 2x1 表) → :8007 维持 VERIFIED-CLOSED; 下采样代码保留(flag 化, 未来若换更强 VLM 可复用); 实验后 :8007 已 kill
- **4.6 BM25 决策不修**: 真 BM25 已实现(PG 全量取 137 chunks + rank_bm25 + /tmp 缓存)并 flag 化 M2_ENABLE_BM25(默认 false); A/B 16 题 hit@10 off=15/16 on=15/16, 排名零变化, improved=0 regressed=0 → 当前语料规模下无增益, 留 flag 备未来语料扩大; scripts/m2_bm25_ab.py + logs/graph/eval/bm25_ab_report.json 为证据资产

## 2026-08-10 文档刷新+双链路+视频+选择题专项 入账
- **T4 场景 A 最小闭环 CLOSED** (7b27d50): /m1 建议映射面板 — GET/apply/reject 三端点 + 回归门禁 (apply 后自动跑 scenario1 --quick, FAIL 自动回滚 schema 返 409) + 用户可改选目标字段 (retarget) + 10 tests (tests/test_m1_schema_suggestions.py)。UI: #suggBtn 徽章 + modal (high 置信默认勾选)。**注意**: 端点需 :5050 重启才生效, 重启窗口待用户批准。
- **场景 B (问答候选选择题) 设计入库、实现排期**: docs/26 §三 — 直连路 ~2h (候选收集 1h + 拼装 0.5h + 测试 0.5h), agent 路二期。触发条件: 场景 A 面板经甲方 walkthrough 认可后, 或甲方明确反馈"未找到"体验需升级。
- **T5 对账表 CLOSED**: docs/26 附录 — docs/23 话术/限制 9 条: 8 解决有证据 + 1 等甲方数据; 台账 10 条: 8 闭环 + 1 待决策 (schema 口径统一, 需刷 frozen_hashes manifest) + 1 等甲方输入 (Qoder PAT)。
- **hygiene** (02b768e): legacy test_e2e_browser 显式跳过 (:5000 旧 UI + headless=False, playwright 安装后被解锁致 2 fail); pytest 回 310 passed / 13 skipped / 0 failed。

## 2026-08-10 Loop C differential 审计入账 (a7f8282..HEAD, CONDITIONAL → 修复中)
- 报告: docs/experiments/2026-08-10_audit_loop_c_differential.md (0 CRITICAL / 1 HIGH / 6 MEDIUM)
- **已修 (批 A 395f85b)**: F1 冻结 schema 守卫(403) / F2 reject admin 门禁 / F3 OCR 门禁盲区提示 / F4 apply single-flight / F5 字节级备份回滚 / F10 CLI 无样本 --apply 需 --force / F11 退出码契约; +3 tests
- **已修 (批 B 7173dce)**: F18 docs/23 四处数字按工件校正 + docx 重生成; F19 附录 B 数据源/延迟区间/QA 口径; F13 judge 声明如实化; F14/F15 描述与 .env.example 登记
- **台账遗留**: F6 同(raw,table)多目标策略(当前重复数=0, 无实害); F7 M1_SCHEMA_SUGGESTIONS 双轨(CLI-only 用途, 文档注明即可); F8 上传临时文件名建议不可复验(UI 标注为后续); judge 结构性隔离(双 prompt, 后续项); F3 中期: OCR 来源建议 apply 前定向 before/after
- **F4 结构项**: async 端点同步阻塞又一新实例, 归 B 阶段(网关化)处理 — 既有 F5 known_risk 同源; 本轮已加 single-flight 缓解
- **待办**: :5050 重启载入批 A 端点加固 (等用户批窗口, 与 walkthrough 合并执行)

## 2026-08-11 agent 路延迟退化 — 根因定位（A/B 闭环, 修复待批）
- 排查方法: adapter 为 throwaway session（ask 完即删）, 旧 39/55s transcript 不可追溯; 改直连 sidecar 计量会话 + SQLite trace 取活证据。
- 基线（原配置, warm）: 31.5s = 轮1 12.0s（in 512 + cache.read 10454, out 459, tool=knowledge_search）+ 轮2 19.5s（out 1017）。**skill tool 从未被调用**（playbook 未加载）。
- 变体 A（摘 m2-qa「首答前加载 m2-rag-playbook」指令）: 冷 43.1s（轮1 prefill 37.3s = 10.9k skill 元数据上下文冷 prefill）/ 热 22.8s（out 903）。
- 根因分解: ① **~11k skill 元数据上下文冷 prefill ≈ 37s**（「冷 39s」真身, 每次 sidecar 重启后首问承担） ② **输出端 reasoning tokens ~1-1.5k ≈ 19-30s（warm）**（qwen3.6 thinking 默认开） ③ playbook 指令本身未执行但诱发额外推理（摘除 warm 31.5→22.8s）。
- 现状: warm 22.8s 仍 > OPENCODE_ASK_TIMEOUT=18 → route=on 当前多回落直连; 回落路 2-4s 正常, 演示以直连为主不受影响。
- 修复候选（待批, 未动手）: a) restart_opencode_sidecar.sh 加一次 warm-up ask 预热缓存（消 37s 冷启动, 最小改动） b) m2-qa 禁 thinking（adapter hint 或 provider 层, 需 :5050 重启窗口） c) skill 上下文瘦身（m2-qa 仅注册必需 skill）。测后配置已还原（opencode.json 无净变化）。

## 2026-08-11 任务2 M1/M2 页面改版设计稿（待拍板, 未动代码）
- docs/27_M1M2页面改版_两个设计方向.md + 草图 docs/experiments/2026-08-11_m1m2_redesign/{direction_a,direction_b}.html（浏览器直接打开）。
- A 三栏任务工作台（WorkBuddy 正传, 2.5-3 人天） vs B 流水线画布控制台（演进式, 1.5-2 人天）; 推荐先 B 后 A。
- 公共规范: 模式切换只读指示（/api/m2/ask 无每请求 route 覆盖, 诚实设计）/ 选择器保留映射表（record_demo_video + tests 命脉）/ m1v2 并行灰度 / 视频重录与 walkthrough 刷新预案。

## 2026-08-11 夜间 loop（行业对标 × 四维审计）入账
- docs/28 业界对标与优化菜单: 14 gap + Top5 菜单, 待用户拍板; 不擅自启动。
- eval 硬化资产: scripts/m2_eval_number_faithfulness.py（数值 claim 去 LLM 化核验, 掩码感知, 3 对抗题, FAIL=0）+ scripts/m2_eval_judge_consistency.py（judge 自一致性 STABLE）; 报告 logs/graph/eval/{number_faithfulness,judge_consistency}_report.json。
- eval 工具 bug 修正: 新脚本初版 chunk 键误用 text（真键 content）→ 修正; judge 本体无此 bug（基线不虚, 误判已撤回）。
- 后端小修: .env.example 补 OPENCODE_ASK_TIMEOUT/MAX_SESSIONS/SERVE_URL。
- 延迟诊断实验文档: docs/experiments/2026-08-11_agent_latency_diagnosis.md（修复菜单 a warm-up / b 禁 thinking / c skill 瘦身, 待拍板）。
- 菜单新增: bare except 收窄 x5 / knowledge 端点 metrics / eval pytest 原生化(G14) / judge 全 16 题一致性 / agent-vs-直连一致性检查(前置延迟修复) / parser 双引擎交叉。

## 2026-08-11 辅助线 walkthrough 验收入账（块 A）
- **验收结论**: 场景 A 建议映射面板 walkthrough 通过; apply 5 干净建议 / reject 14 / hold 6; WaveFax 85.7→**100** 入基线 (270c686, --rebuild + quick 门禁 12 pass/3 skip)。schema +5 近义词 (基金资产总额→资产总额类 / 交易账号→资产账号 等)。
- **遗留①**: schema「交易对账单」表缺 **分红方式** 标准字段 — 恒等映射建议被跳过, 后续补字段定义 (补后跑回归门禁再报 delta, 走 m1-gap-triage SOP)。
- **遗留②**: admin token **fail-open 仍为 B 阶段延期项** — 本次 apply 即在无 M1_ADMIN_TOKEN 下执行, 风险已知 (与 knowledge 写端点无 token 同源, 台账不重复开条目)。
- **决策入账**: 延迟修复 a(warm-up ask)+b(禁 thinking) 已批, 等 :5050 重启窗口一并载入; 任务二「先 B 后 A」已批, 代码启动等 docs/23 发送; docs/28 顺序 #2→#1→#4; docx+视频预审 PASS, 等用户人工复审 docs/23 后亲发甲方。
- **口径提醒**: docs/23/docx 仍为 85.7 预审版; 是否同步 100 并重生成 docx 由用户发送时定 (不在块 A 擅自改)。
