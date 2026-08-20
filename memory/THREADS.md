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

- VLM :8007 (Qwen3-VL-8B-Instruct GGUF): **VERIFIED-CLOSED** (2026-08-08) — hf-mirror 已同步官方 GGUF 仓库, Q4_K_M 5.0GB + mmproj-Q8_0 752MB 下载成功, llama.cpp 2.16 llama-server 起 :8007 一次点亮; NCAMC 截图手测输出合法 markdown 表格 (首调 119s); parser 重跑 engine=vlm-8007 (trafax/wavefax 走通), 但传真样本命中率与 vision-8004 持平 (trafax 2/4;8/11;4/11, wavefax 4/7), 单文件 OCR 延迟 3-8min (vision-8004 ~30s) → 默认关闭, :8007 已 kill。重启方法: llama-server -m ~/wzh/models/gguf/qwen3-vl-8b/Qwen3VL-8B-Instruct-Q4_K_M.gguf --mmproj .../mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf --port 8007 --alias Qwen3-VL-8B-Instruct -ngl 99 -c 8192, parser _try_vlm_table 自动接入 (M1_VLM_TIMEOUT 建议 ≥240)。降采样已实验完毕 (见下 4.2, M1_VLM_MAX_PX=1600 默认): 延迟达标但 TraFax 命中率劣化, 代码保留为复用资产。
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
- **遗留①**: ~~schema「交易对账单」表缺 分红方式 标准字段~~ **RESOLVED (2026-08-12 T4①)**: 交易对账单+证券持仓明细 新增 分红方式/可用份额 两标准字段 (m1-gap-triage SOP: 诊断→补字段→回归门禁→报 delta); 嘉合×8 87.5→100、TraFax 表3 81.8→100、NCAMC 75→87.5、nanhua 75→87.5, 基线 rebuild 后门禁 15 pass/0 warn; 附带修复嘉合默认路 3.3-9s LLM 兜底延迟 (根因=基金份额/可用份额 双列争用 持仓数量 单槽位) → 63ms。详见 docs/experiments/2026-08-12_client_experience_audit.md §三。
- **遗留②**: admin token **fail-open 仍为 B 阶段延期项** — 本次 apply 即在无 M1_ADMIN_TOKEN 下执行, 风险已知 (与 knowledge 写端点无 token 同源, 台账不重复开条目)。
- **决策入账**: 延迟修复 a(warm-up ask)+b(禁 thinking) 已批, 等 :5050 重启窗口一并载入; 任务二「先 B 后 A」已批, 代码启动等 docs/23 发送; docs/28 顺序 #2→#1→#4; docx+视频预审 PASS, 等用户人工复审 docs/23 后亲发甲方。
- **口径提醒**: 已决 — 表下加注(定稿后 WaveFax 100 以实况为准) + docx 重生成, 504810c 定稿, 双方不再改/不再重生成, 用户终读后亲发。

## 2026-08-12 发送前自审计专项 (T1-T4) 入账
- **T1 甲方体验审计**: 15 步全过 / 0 console 错误 / 无演示前必修项; 口头解释 4 条 (QA 20-25s=route 回落 / thinking 提示 / 持仓对比(未知)=掩码样本如实呈现 / OCR 冷热口径) + 可接受 3 条 (下载文件名 F8 / 开关无 toast / hold 不显示按设计)。报告 docs/experiments/2026-08-12_client_experience_audit.md。
- **T2 声明复测漂移案例** (docs/23 冻结不改文, 只入账): ① "非扫描 <2.1s" 默认路实测 3.3-9s ✗ → 根因定位后 T4① 当晚修复复测 63ms ✅ RESOLVED; ② "OCR 16-71s" 复测 536ms = .ocr_cache 内容哈希磁盘缓存 (冷启 08-09 证据 9.6-22.9s), 漂移方向更快, 口头解释级不修。教训: 声明数字必须标注口径 (路径/冷热/题集), 复测时口径不一致即记漂移。
- **T2 16/16 生产口径**: deterministic eval 打 :5050 → 16/16 PASS (题集含对抗题; 感知延迟 20-30s 为 route=on 回落, 正确性不受影响)。
- **T3 Loop C 差分审计 (5535bdf..504810c) = CONDITIONAL**: 报告 docs/experiments/2026-08-12_audit_loop_c_differential.md。FC-1 (MEDIUM, diff 引入: 资产账号 下 交易账号 同义词与 交易账号 字段表内碰撞) **当晚已修** (删同义词 + 门禁复验); FC-4 fail-open auth 复评 **HIGH 暴露** (0.0.0.0 + 无 token 写操作已实发生, B 阶段最高优先, token 落地前不扩大暴露面; .env.example 已补 M1_API_TOKEN 条目); FC-5 async 端点同步调用复评 HIGH-可用性 (route=on 在跑, 匿名低成本 DoS 面, B 阶段网关化处理); FC-3 (LOW): 多表 100.0 基线进入零容差粒度区, OCR 容差仍是唯一缓冲, 门禁健壮性改进入下迭代; 范围外观察: 冻结清单表述应统一为 scripts/graph/frozen_hashes.txt (任务书"docs/m1_schema/frozen_hashes"与实物不符, 文档引用时注意)。
- **T4① 附带修复 (自学习写入器 bug)**: scripts/m1_statement_parser.py `_append_schema_suggestions` 重写文件时只写 {suggestions}, 丢失 applied/rejected 审计区 (T2 复测默认路实跑于 00:00:56 触发) → 修复为保留原有顶层键; 丢失区段已从 HEAD 恢复; 2 条陈旧建议 (可用份额→持仓数量 / 交易费用→财汇局征费, 均已被存量或新字段覆盖) 移入 rejected 防碰撞复发。
- **T4② eval 接线**: m2_eval_number_faithfulness.py 失败计退出码 (原恒 0), run_eval.sh 增步 [3/4] 数值忠实度 + 退出码联动 + summary 段落。
- **遗留 (小)**: scripts/t1_client_experience_audit.py 上传步等待条件命中过早 (03/04 ms 无效, 已用 API curl 补偿), 下次维护窗修; FC-3 门禁健壮性; 审计建议"token 落地时同步收紧 CORS_ORIGINS" (随 FC-4 处理)。

## 2026-08-12 docs/23 解冻重写（用户授权覆盖 504810c 冻结约定）
- 用户终审结论: 旧版不达交付标准 → 授权解冻重写。新结构: 30s 执行摘要(头部仅 4 数字: 嘉合100% / 35.7→100% / 16-16带溯源 / 电子件毫秒级) / 场景化能力 / 递进故事 / 诚实限制 / 需要您支持; 口径演化(14/15→16/16, OCR 冷热)移脚注; 去 23_ 编号与待审阅元行; 附录 B 业务化; 附录 C 话术拆至 docs/experiments/2026-08-12_demo_talk_track.md。
- 截图 08-12 重拍 10 张 (docs/experiments/2026-08-12_docs23_screenshots/, 含建议映射面板 6 候选实拍); 08-04 目录转历史留档。
- **新发送版 docx md5 冻结: bc3785cb4237dcda316120251fab8472** (封面含呈报/汇报方行+10图内嵌+页码, 12 页; 图7 单独占页放大, 8/9 放大) — 等用户终审; 终审通过前双方不再改/不再重生成。旧 504810c / 141b092b 冻结约定作废。打磨五处: ①封面署名+呈报行 ②图7 独占页放大 ③TraFax(逐表命中率) ④页码 ⑤支持清单项目符号+附录B全量。

## 2026-08-12 仓库精简收尾入账（主线程清扫）
- **精简落地**: c4f6a5a (git mv 归档 18 实验记录 + 16 一次性脚本 + README_Codex 历史快照, 零 rm 可逆); 主线程执行沙箱拦截的删除: sessions.db / scripts tmp_*.py×7 / 工作区 PNG×6 / tmpclaude-cwd×2 / _staging_task2 / D:\tmp_doc23_pages×2 — 全部先移备份 D:\AIRcommend\JinRongAgents\_cleanup_backup_20260812 (45 文件) 再清源; _staging_task2 删前核验内容已在库 (设计文档=docs/27@8e5fd92, html/png=experiments/2026-08-11_m1m2_redesign 在库, 仅 _shot.py 一次性); pytest 325 passed/13 skipped 零回归; 冻结 docx bc3785cb 复验未动。
- **机会项（等拍板）**: 本机 agents_final_tech/dify/ (gitignored, GB10 无此目录) 存 5 份甲方规则 docx（电子对账规则0108 / 估值数据催收规则 / 完整性监控与一键估值规则 / 管理人估值进度查询规则 / 自定义对账规则）+ 5 份 Dify workflow yml — 七月 Dify 原型遗留, 正是 docs/23"需要您支持"所列字段规则素材; 建议走 Q2 同款确定性流程挖 schema synonyms, 批准前先不动。
- **待审（低优先）**: 本机 agents_final_tech/image/.env/ 7 张时间戳 PNG (~2026-02, gitignored), 旧时代遗留, 下轮 neat 判定去留。
- **禁动确认**: 本机工作区 3 个 .bundle (tat-dqa×2 + joint-m1-m2-plan) 为相关工作唯一载体, GB10 无 tat-dqa 仓库, 不得删除。
- **check[4] 本机 FAIL 定性 (辅助线复核更正)**: 根因非缺 skill 目录 (本机 ~/.codex/skills 37 目录 / ~/.claude/skills 均在), 而是本机 CRLF checkout 使 sync_skills.sh 行尾带 \r, WSL bash 执行 `set -o pipefail\r` 即错 exit 2 (git ls-files --eol = i/lf w/crlf 为证); 属环境差异非真漂移, 结论维持 docs_lint 以 GB10 为准 (0 fail/0 warn); 本机如需跑: `bash <(sed 's/\r$//' scripts/graph/sync_skills.sh) --check`, 不强制。


## 2026-08-12 "已发送"信号 → S1/S2 执行入账
- **docs/23 已发送甲方**（用户亲发, 2026-08-12）; **B4 观察时钟启动**: 目标 ≥100 asks / ≥3 天; 仪表 = /api/m2/ask JSONL (logs/graph/b4_ask_log.jsonl: ts/route/latency_ms/sources_count/fell_back/status) + status.sh B4 段; eval 套件每天经 :5050 生产端点跑一遍积累真实样本; 数字不许造。
- **S2 重启载入** (窗口 23:24-23:41): 延迟 a(sidecar warm-up ask; 首版用"就绪确认"题不触发检索→MCP 冷启动未预热, 修正 d8504fb 为真实检索题, 冷路 45s 预付) + b(FORMAT_HINT /no_think, 契约 C-1) + Q2 别名链 + 批 A 端点加固 + vision MCP allowed_roots=/home/testuser/wzh/m1_samples(opencode.json mcp env); B4 仪表 + status.sh(Q4 L1) 同窗载入 (cab17b9)。
- **六步验证**: ①health/full healthy(137/local)✓ ②parse 冒烟 sample_20260506_233222LU.pdf 3 表(OCR+LLM 路 16.4s)✓ ③QA×2 正确带 sources(含 OCR meta-query 命中)✓ ④compare 嘉兴民安短名 2 持仓✓ ⑤route=on✓ ⑥agent 路 warm 实测: **最佳 13.5s 成功(单检索题), 3/4 次尝试 >18s 回落**——目标 <18s 部分达成, 如实记账。
- **延迟实测台账**: a+b 后 agent 路 1 成 3 落; 回落与多轮检索耗时 + :8004 slot 争用(与 Loop B 23:38 循环时间窗重叠)疑似相关, 根因诊断入 A2 稳态化遗留; 直连路 warm 2.7-3s, 重启后首请求冷加载 ~17-20s(embedding 懒加载, B4 验收口径: 热身或从 p95 排除)。
- **回滚演练**: kill→health200(route=off) 实测 **10s** (B4 ≤30s 达标, 前次实测 23s); route=off 直连验证正常; 甲方临时演示第一动作 = M2_OPENCODE_ROUTE=off 重启(10s)。
- **B4 数据卫生**: pytest m2 端点测试会写 latency_ms=0 的 mock 条目进 B4 日志, 统计时过滤 latency_ms=0。


## 2026-08-13 S3 队列收口入账（发送后队列 ①-⑤ 全部完成）
- **S3① G12 数值核验产品化**: 原型核心抽入 src/biz/number_grounding.py (行为逐字一致) + eval 脚本改 import + 6 单测; NF 复跑 0/9 与基线一致 (bda88f4)。
- **S3② dify 5 docx synonyms 挖掘**: scripts/mine_dify_rule_terms.py (确定性无 LLM, 可复用); 5 docx 性质判定 = 估值工作流业务规则(非字段映射表); covered=4/candidates 28(真实 3)/unknown 978; 补词 3 (交易日→交易日期 / 下层基金净值→基金净值 / 手续费支出→手续费, 均证券持仓明细, 碰撞检查过); 门禁 15 pass; **诚实 delta=0** (语料无新词, 为未来估值表类文档强化) (6dd189b)。
- **S3③ G6 检索透明面板**: top_k 选择器(3/5/8/10) + sources score/field/text 优雅降级(agent 路无 score 不再显示 undefined) + meta 显示 route(直连/验证链路); 纯前端零 API 改动, 既有选择器未动 (61d2fd2)。
- **S3④ Docling ARM64 探针**: 独立 venv 零编译安装 (torch 2.13 aarch64 wheel, 模型走 hf-mirror, HF 直连超时); **GPU 路 triton gcc JIT 失败 (与 Qwen3-VL safetensors 同类故障)**; CPU 路: NCAMC 垂直行提取优于坐标重建(完整 1×8 数据行) / TraFax 表数同基线但退化表 / 嘉合弱于确定性 parser; 定位 = 离线 second-opinion 候选, 不入热路径 (f86a876)。
- **S3⑤ :8005 judge 分流**: M2_JUDGE_ENDPOINT/MODEL flag 原生在位(默认 :8004); :8005 Qwen3-14B 交叉一致性 **63/64 = 98.4%** 平均差 0.03 (唯一分歧 adv_multiturn citation A=5/B=3); crosscheck 脚本入库; :8005 可作 eval judge 分流端点给 :8004 腾 slot (ceec4ab)。
- **B4 观察进行中**: asks 积累见 status.sh (测试 mock 条目 latency_ms=0 统计时过滤)。

## 2026-08-13 凌晨 科研线与守备强化队列 (R1/R2/R3) 入账
- **R1 Loop B 强化 COMPLETE** (e508a5c): STEP5 QA 金丝雀 4 题 (adv_ocr_meta/adv_refusal/q06_minan_cash_balance/adv_cross_doc, m2_eval_deterministic.py 新增 --only/--timeout, 报告→logs/graph/eval/m2_canary_report.json) + STEP6 三方 git 对齐 (网络不可达=SKIP 不 FAIL) + STEP7 docs_lint; env flags LOOP_B_CANARY/GIT_ALIGN/DOCS_LINT/CANARY_IDS/CANARY_TIMEOUT 增量, 默认行为不变; write_report.py 扩展兼容 SKIP(-1); **FAIL 翻转才写 dispatch** (状态文件 logs/graph/loop_b_last_status, 首跑=init 不写); 破坏验收过 (INDEX 死链注入→翻转 PASS→FAIL→恢复→FAIL→PASS 双 entry); pytest 336/13 skipped。
- **R1 事故记录**: 旧 graph-loop-b daemon (07-31 起运行) 08-13 01:00 发现停摆 (死因不明, 00:47 侦察尚活); 重建 tmux + --daemon, 首周期 PASS (01:02:23, head=e508a5c)。
- **R2① zhikuncode 探针结论**: Docker 确认 (Spring Boot JDK21 + python-service sidecar, healthy, :8090→8080; "依赖安装"仅指本地构建镜像时); 仓库已 bind-mount /app/workspace; BYOK 现指云端 Token Plan; **:8100 仅 /responses 线 (responses2chat), zhikuncode 走 Chat Completions → 直切 :8100 不可用**, 价值低, 维持云配置; 顺带: MCP zhipu-websearch 每 30s 重连失败 (无害噪音)。
- **R2② OpenAI4S 探针结论**: PKU-YuanGroup/OpenAI4S (MIT, Code-as-Action 科研 agent, 纯 stdlib 核心) **最小循环验证通过**: ~/wzh/research/openai4s_probe + 独立 venv ~/wzh/venvs/openai4s_probe; BYOK 直连 Token Plan 上游 (OPENAI4S_CHATGPT_BASE_URL; :8100 因 /responses-only 不可用); `openai4s run` 输出结构化结果 + kernel 验证 + metrics (RUN_EXIT=0); serve Web UI :8760 未启动; **未接生产**, 可作 docs/30 科研线执行器。
- **R3 学术 skill 审计安装 COMPLETE**: zLanqing/codex-claude-academic-skills (MIT) GB10 克隆 ~/wzh/research/academic_skills_audit (本机 clone 被沙箱拦截, 转 GB10 成功); 审计 = 3 顶层 skill (research-writing/office-academic/scientific-toolkit 含 21 子技能), frontmatter 规范, 无恶意模式; **唯一 caveat**: literature-review 子技能含 `curl|bash` 第三方安装引用 (parallel.ai), 未经审阅勿执行。安装 = repo skills/ + sync_skills.sh A 列表 + AGENTS.md 注册表 (A 配属 科研线) + 本机 Loop D; sync --check PASS 21/21。
- **R3 docs/30 入账**: docs/30_科研线规划.md (VGMC 验证门控记忆固化) 登记 INDEX 状态=活跃; M0 文献调研任务卡已附文末 (只读 2h 隔离执行), 待用户排期。

## 2026-08-13 早 T1/T3 收尾小队列入账
- **T1 schema_suggestions 脏改动入账** (0d938d7): 自学习闭环 08-12 23:33 批次 (walkthrough 上传 tmp2s004xv5.pdf) 7 条新建议 + 权益登记日 count 1→2; **产品份额①→持仓数量(high) 列下轮 apply 候选** (走既有 SOP: 回归门禁 + delta 报告, 等明确窗口, 本次不 apply); tmp2s004xv5.pdf 定性 = 场景 A walkthrough 上传临时件 (时间戳落在 23:24-23:41 重启+walkthrough 窗口), 磁盘搜索 (/tmp + 项目目录) 未见残留, 无需清理动作。
- **T3 B4 分布记账** (辅助线 08-13 08:27 实测): asks=120 (agent=15 / fallback=92 / error=0) — route=on 下 **77% 流量经 18s 超时回落走直连**, "快与准菜单"的准路径当前被超时吞掉大半。定性: ① 作为 **A2 遗留 (:8004 slot 争用/延迟方差) 的量化证据**, 修复优先级随甲方反馈定; ② **B4 时钟口径确认**: ≥100 asks 数量维度已达标, 继续等 ≥3 天, 达标判定 = 两条件同时满足; ③ 该分布同时是 docs/30 B 模块 (记忆感知路由) 的实证动机 — 引用不重复复述 (台账唯一存放规则)。

## 2026-08-13 夜 T2 M0 文献调研结论入账
- **M0 差异化判定 = 差异化成立（附条件）**: 报告 docs/experiments/2026-08-13_m0_literature_survey.md。精读/补扫 5 篇可核验文献（RecMem ACL26 Findings = 最近邻但只解"何时固化"且记忆仍 NL / Q-Evolve 进化权重不进化记忆工件 / Evo-Memory 与 MemoryAgentBench 为基准类可借鉴评估方法 / self-evolving coding agents 综述 §3.2 确认记忆自进化全线 NL 轨迹形态且明言需 validation+rollback）。VGMC 三要素组合（可执行规则工件 + 回归验证门 + LLM 介入衰减）未见覆盖。
- **重要发现（检索可靠性）→ C1 更正 VERIFIED（08-13 夜）**: CAIS 2026 与 STATE-Bench 经直连 URL 复验存在——CAIS: "Learning from Supervision with Semantic and Episodic Memory"（Megagon Labs, episodic critique→semantic guidance 管线坐实）@ caisconf.org/program/2026/papers; STATE-Bench: Microsoft Open Source Blog 2026-05-19（开源 450+ 任务 agent-memory 基准）。初判"疑似检索幻觉"系 **M0 渠道覆盖缺口**（文献 API 不索引 ACM 会议页/工业博客）, 非幻觉。渠道规则 + 元洞察（验证门需多渠道化, 与 VGMC 主题同构, 可入论文 motivation）入 M0 报告 §六; docs/30 两锚点恢复必引。
- **可吸收**: Evo-Memory 流式评估协议→实验 3; MemoryAgentBench 四能力→评测对照; 综述分类学→相关工作定位; 真实门控数据 (apply 5/reject 14/hold 6) 为稀缺实证资产。
- **NLPCC/CCIR 截稿日未获得**（DNS/502/JS 渲染全挡）, 入 blocked_questions 待人工浏览器查。
- 约束遵守: parallel.ai curl|bash 引用全程未执行; 物料在 ~/wzh/research/m0_lit/（GB10 本地不入 git）。

- **运维 (08-13 夜, C2 更正)**: GB10→GitHub SSH publickey 拒绝 = **GitHub 侧瞬时故障, 已自愈** — 辅助线实测 ssh -T git@github.com 认证成功 (Hi Wzh2learn!) + ls-remote SSH 路正常 + key 文件在位; 同时段 HTTPS 500 瞬断 x2 为旁证。主路径恢复 **GB10 直推**（C1/C2 收口实测确认）; "GB10 commit → 本机代推"保留为兜底预案; 用户侧 GitHub key 检查降级为可选。

## 2026-08-14 导师包终审入账
- **导师版 docx 重冻结**: 5707fcea397c384d21e35ba72023cee0（R1 口径修正后重生成; 旧版 3d80d27 内 docx hash 作废）。修正内容: 图 1' 看点补"冷态首请求 20.5s / 热态复测 2.7s（战绩表口径）" + shots_meta 04/05 note 更正 + 附录 B 故障表补双端口占用行（R4 实测 exit 1 不静默）。
- **导师版 docx 重冻结（二次，08-14）**: 567c7fe732b8b2993396c6cc2d32a172（Loop C 发送前终审 R2 FAIL 后换图重生成；5707fcea 作废）。修正: 图 1 改解析完成态+选择器位置改输入行右侧；图 2/3 改直连路+sources 展开态（旧图为 agent 路拒答误拍）；图 7 元素级截图无裁切；图 9 拒答完成态并改指 08-13 目录。误拍根因: 旧截图脚本等待条件对整 chatlog 全局匹配且无 sources 非空重试，重拍脚本 /tmp/reshoot_fix.py 已修。待 Loop C 复验。
- **导师版 docx 重冻结（三次，08-14）**: bd3daed4948af81cb5dcea5ef2814882（Loop C 复验残差 2 处改图注后重生成；567c7fe7 作废）。修正: 图 1 图注选择器改互指图 1'/图 9；图 5 图注未映射列改互指图 1/图 4；图 2 看点补冷态说明；shots_meta 01/07 note 同步。待 Loop C 三验。
- **导师版 docx 重冻结（四次，08-14 受众分离）**: d31fe5c3f49f81202a9a03f08c9983ed（build_doc31_docx.py 加 --audience 开关，advisor 默认裁附录 A/B；bd3daed4 作废）。md 保持全量源；清单入审查报告受众分离轮。
- **导师版 docx 重冻结（五次，08-15 视频 v2 轮）**: ab2fed4310487d5f4136f6546780d057（d31fe5c3 作废）。配套: 视频 v2 demo_v2.mp4 3:48（V1-V7 全消解: 开场解析态/等待段倍速+字幕/横幅数字对齐/透明面板+建议面板新分段/结束卡）；D1 H1 导师版；D2 §3.7 按 v2 重写；D3 §6 视频条同步；D4 战绩表 pytest 口径注（334/15 无 PG 环境，PG 依赖 2 项随环境翻转）。
- **导师版 docx 重冻结（六次，08-16 微修轮）**: 929a8c65fbdea1bd672f5d8d5ea1fd16（ab2fed43 作废）。配套交付行改 demo_v2.mp4；扫描全 0 + 第 2 页目检过。视频治理: cards/ 入库，segs//work//demo_v2.mp4 入 .gitignore。视频取回: scp jinrong-dev:~/wzh/projects/agents_final_tech/docs/experiments/2026-08-15_demo_video_v2/demo_v2.mp4（+ 同目录 steps.md）。
- **治理规则（08-16）**: STATE 覆写绑定收口 commit——每次收口 commit 必须同步覆写 memory/STATE.md 至当前 HEAD，杜绝 HEAD 漂移（起因: STATE 曾停 299f77d 三轮）。
- **R3 附录 A 实测**: 五条 scp 临时目录逐条跑通（23 文件 6.33MB, 未覆盖已取回文件）。
- Loop C 独立复审进行中, 报告 docs/experiments/2026-08-13_advisor_package_review.md。

## 2026-08-16 模型升级专项 (Qwen3.8-27B + vLLM) — P2 完成, 闸门触发, 待用户拍板 (A/B 路线)
- P0 完成: :8004/:8005 完整 llama-server cmdline 已录 (回滚依据, 见 dispatch_log 08-15/16 + DECISIONS.md 模型卡); 内存 121GB 统一内存 / 磁盘 2.8T 空闲; :8006/:8007 空闲。
- P1 资产落盘: Qwen/Qwen3.8-27B-FP8 (29GB, 66 shards) → ~/wzh/models/hf/Qwen3.8-27B-FP8 (hf-mirror, 独立 dl_venv); 镜像 timothystewart6/vllm-gb10:v0.27.1-gb10.1 (vLLM 0.27.2.dev0+20260815, 22.1GB, dockerproxy.net; daocloud 白名单拒绝/1ms.run 大层卡死为过程事实)。
- **关键实测 (GB10 统一内存)**: ① CUDA mem_get_info 不计 page cache — 模型+镜像下载后 CUDA free 仅 15.6GB, vLLM init 即 cudaErrorMemoryAllocation; 无 sudo 不能 drop_caches, 用 CPU 分配压力法回收干净缓存 (scripts/gb10_reclaim_page_cache.sh, 15.6→38GB), 生产栈实测无感 (:5050 healthy / :8004 200)。② 回收后 GMEM=0.30 启动成功 (0.27 差 0.44GiB 失败); --max-num-seqs ≤78 (Mamba 状态块约束)。③ 思考控制实证: enable_thinking=false 零推理; reasoning_effort 合法集 xhigh(默认)/medium/low (prompt 引导式非硬上限); thinking_budget 模板不支持传入被忽略; "high" 非法→400; vLLM 0.27 reasoning 存 message.reasoning。
- P2 基准 (全实测, 报告 logs/graph/eval/model_probe_*.json @GB10): 三档矩阵 A_off p50=10.31s/p95=15.76s (49 tok), B_effort_low p50=23.82s, C_effort_xhigh p50=60.60s (431 tok); 确定性 16/16 PASS (旧栈对照 16/16, 1.3-1.9s/题); 并发 3 流 makespan 70.6s vs 串行 207.1s 但单请求劣化 7x (带宽受限); judge 交叉评 5.0×4 (基线 4.94), 自评 5.0×4; 视觉转写质量平手但候选 72-76s vs 旧栈 mmproj 29-31s。NF 未对候选重跑 (脚本锁 :5050, 红线不重启), 留 P3。
- **闸门判定: 质量 GO + 快路 FAIL (A_off p50 10.31s > 8s) → 不全量替换**。切换菜单 = 路线 A 双模型分工 (推荐先行) vs 路线 B Qwen3.8-35B-A3B MoE 探针, 见 docs/32 §2.4, **待用户拍板**。
- 状态: 探针 :8006 保持运行 (tmux vllserve), 拍板前不动生产。旧 GGUF+llama-server 保留 48h (至 08-17 18:00)。附注: P2 视觉对照占用 :8004 期间 (18:16) Loop B qa_canary 一次超时 FAIL, 属探针负载扰动, 非代码回归, 观察下轮翻转。

## [2026-08-16 22:20] PG 连接泄漏: Loop B 周期跑遗留 idle 连接打满 max_connections=100 (known_risk)
- 现象: NF 候选侧首跑全程 "too many clients already" (结果无效已重跑); pg_stat_activity 95 idle/100, 最老 1d21h, 增长速率 ~30min/个, last_q 含 chat_sessions 心跳与 ROLLBACK, 判定 Loop B 周期跑每轮漏 1 连接。
- 临时处置: pg_terminate_backend 清 >60min idle (95→20), :5050 health 全程 healthy 无感。
- 根治选项 (待窗口): a) Loop B 脚本补连接关闭 (Loop B 本体不扰, 需用户批) b) PG 设 idle_session_timeout (需 PG 重启窗口) c) max_connections 调大 (同需重启)。
- 状态: OPEN (B 阶段候选); 再现特征: NF/eval 报 too many clients → 先查 pg_stat_activity。

## [2026-08-16 22:30] S2 台账同步 (模型升级后半场)
- NF 候选侧遗余项: 已执行 (S1 参数化后首跑, 结果见 dispatch_log 与 logs/graph/eval/number_faithfulness_report_candidate_8006.json)。
- 48h 回滚窗口: 旧栈 (GGUF+llama-server) 保留至 **2026-08-17 18:00**, 窗口内回滚 <2min (DECISIONS 08-16 模型卡 SOP); S4 接线在窗口内完成。
- 路线 B 门槛: Qwen3.8-35B-A3B 权重两通道未发布 (08-16 22:00 实测, 证据链见 docs/32 §2.4); routeb-watch 自动探测下载中; S3 顺延, blocked_questions 有同步条目。
- PG 泄漏处置见本日 22:20 条目 (known_risk, B 阶段候选)。

## [2026-08-16 23:35] S4 双模型接线完成 + OPENCODE_ASK_TIMEOUT 重议待拍板
- 接线: gb10v provider (经 :8008 注入代理 → :8006) 承载 m2-qa + evidence-verifier; judge → :8006; A3B 守快路+视觉+M1 热路径。详见 DECISIONS 当日条目与 docs/32 §4 S4 执行记录。
- agent 路实测: 首轮 ~30s / 热态 72s / >120s 超时, 18s 预算全回落 → 用户可见行为不变 (零回归)。
- 重议需要: :5050 重启窗口 (OPENCODE_ASK_TIMEOUT 模块级读取) + M2 菜单项 (skill 预载/降轮次/档位感知超时) 组合。等用户拍板, 与 48h 旧栈窗口 (08-17 18:00) 时序上互不阻塞。
- B4 台账切换点: 2026-08-16 ~23:35 双模型接线 (ask 结构化日志按 timestamp 分段; 接线不改变回落行为, 计数连续累计)。

## [2026-08-17 00:30] 红线修订 + T1 决策入账 (Route B CLOSED / :8004 定型 / 演示 UI 追认)
- 红线修订三条落 DECISIONS [2026-08-17]: 72B 硬禁 → 模型准入预算门; 模型退位政策 (权重默认保留, 删必先记台账); M1 热路径模型锁定 :8004 A3B, :8006 仅 M2 验证链/judge/深度问答。
- Route B → **CLOSED**: Qwen3.8-35B-A3B 无官方开源权重 (用户人工查证 + 辅助线 HF 枚举双坐实); routeb-watch tmux 退役, 探测脚本入库 scripts/routeb_watch.sh, 日志 ~/wzh/routeb_watch.log 留 GB10; 重开前提 = 官方权重发布。
- :8004 A3B 快路+视觉长期驻守; DECISIONS 08-16 模型卡"GGUF 保留至 08-17 18:00"条款已标注作废。
- 演示 UI (chips ×11 + 规则 modal) 追认为范围内工作, 不扩展任务二改版。

## [2026-08-17 00:35] T2 辅助 Qwen 退位: :8005 Qwen3-14B 停服
- 依赖盘点: .env/src/opencode.json 零引用 (judge 已于 S4 切 :8006); 仅治理脚本/文档引用, 已更新: graph_orchestrator.sh (8004/8006 http_code 检查) / loop_d_monitor.sh (:8006 vLLM + :8005 RETIRED 行) / loop_a_exec_constraints.md / loop_c_audit_prompt.md; status.sh 端口表保留 (快照如实反映 down); loop_b MODEL_AUX_PORT 由 T5 升级为期望关闭态。
- 停服: kill llama-server pid 2645844 (LM Studio 后端, -c 32768 -ngl 20); 端口关闭确认, 无自动拉起 (无 LM Studio daemon)。
- 权重保留 (退位政策): /home/testuser/wzh/models/gguf/qwen3-14b/Qwen3-14B-Q4_K_M.gguf; 磁盘 2.8T 空闲, 不删。
- 端口快照: :5050=200 :4096=200 :8004=404 :8005=000000 :8006=404 :8008=404 :8100=404 (8005 关闭为预期)

## [2026-08-17 00:45] T3 重启窗口执行: 超时 18→45 落地 + 真实承载 PASS + compaction 缺陷处置
- 重启 :5050 (12s UP, 周期 29s): OPENCODE_ASK_TIMEOUT=45 进程 env 生效坐实; 六步验证全过 (health/full 137/local/healthy / parse 冒烟 6ms 确定性 / QA 2 条 / compare 嘉兴民安 2 持仓 / route=on)。
- 真实承载验收: OCR meta-query 经 agent 路完成 route=agent fell_back=false latency=30040ms (b4_ask_log 08-17 00:13:13); 同批第 2 问 47s 超时→回落直连正常 (最坏 UX 封顶成立)。
- **新发现缺陷 (已修)**: agent 路返回 opencode compaction 摘要消息被 adapter 透传为 answer (info blob 垃圾答案) → src/biz/opencode_adapter.py 加 compaction guard (遇压缩摘要即回落直连), 随本轮重启载入。深层问题 (throwaway session 为何触发 compaction, 疑与 27B context 预算/skill 加载相关) 记为观察项, 甲方反馈期不动。
- QA 口径: OCR meta-query 走 agent 路时 sources_count=0 (compaction 案例), 修复后复验见下。

## [2026-08-17 00:40] T5 Loop B 升级完成 (授权例外) + 破坏演练通过
- 三项: STEP 8 双模型拓扑断言 (:8004 health + :8006/:8008 model ID qwen38-27b-fp8 + :8005 期望 down) / STEP 9 B4 agent 完成率看门狗 (窗口 30 asks 计数制: agent_clean==0 且 fell_back>=25 报警; 低流量不误报; route 主动 off 时 fell_back=false 亦不误报) / LOOP_B_PYTEST=0 演练跳过 flag (增量, 默认行为不变)。
- 首周期实战抓 2 缺陷即修: ① 拓扑检查 curl -w 与 || echo 双拼 → "000000" 误判 ② canary 客户端超时 45s < 新最坏情况 (45s 回落等待 + 直连) → CANARY_TIMEOUT 默认 45→75, CANARY_BUDGET 240→360。
- 验收: 完整周期无误报 PASS (00:34, 含 pytest 336/13 + docs_lint 0/0); 破坏演练 kill :8008 → FAIL 报警 + flip 记录 → 恢复 → PASS (flip 机制 4 条记录)。
- write_report.py 报告 JSON 增 model_topology / agent_watchdog 两项 (向后兼容旧 5/8 参数调用)。

## [2026-08-17 23:25] P0-1 三层根因修复 + 真实承载验收 PASS
- 修复链: opencode.json gb10v 显式 limit (32768/4096, 消 compaction) → vLLM parser hermes→qwen3_xml (工具调用可解析) → --enable-prefix-caching (warm 47s→30-34s)。细节入 DECISIONS 当日条目 + SOP FM6/FM7。
- 验收: 生产 :5050 两次 agent 路真实完成 (23:15:04 30.2s / 23:20:49 33.7s, route=agent fell_back=false sources=1)。compaction guard 保留 (行为正确)。
- 边界: OCR meta-query 三轮题型 warm ~48-50s 超 45s 门回落 (题型相关完成率分层, 如实记账)。
- B4 流量标注: 本轮验收+演练在 b4_ask_log 增 ~14 条, 其中 8 条 fallback 为 P1-2 故意破坏演练流量 (题面"演练问题/演练补问"), 统计时按题面可过滤。

## [2026-08-17 23:25] P0-2/P1-1 Loop B daemon 重载 + T5 措辞更正
- 根因: bash --daemon 启动时脚本整体载入内存; 08-13 01:00 启动的 daemon 一直跑 T5 升级前旧脚本——旧 STEP 3 查 :8005 健康 (已退位) → api_anchors FAIL 自 00:48 持续 ~22h 无人接; 旧脚本 8 参调新 write_report.py → STEP 8/9 恒 SKIP (看门狗等于没装)。
- 修复: kill 旧 daemon (pid 1661919) → graph-loop-b pane 重启 --daemon; 新周期 STEP 8/9 出判定, :8005 退位断言 (响应即 FAIL) 生效。
- **T5 措辞更正**: 台账 08-17 00:40 "验收: 完整周期无误报 PASS" 实为新脚本前台运行结果; daemon 当时从未重载, 其后 22h 静默 FAIL。
- **治理规则**: Loop 脚本升级必须重启 daemon 载入新版; 验收以 verify-report 中对应 STEP 实际出现判定为准, 前台运行 PASS 不替代 daemon 载入。

## [2026-08-17 23:25] P1-2 回归演练 PASS (组合故障复现)
- 复现本次事故组合: kill :8008 proxy + 连续 fallback → 升级后 Loop B 双报警: STEP 8 FAIL (:8008 missing qwen38-27b-fp8) + STEP 9 FAIL (0 agent completions / ≥5 fallbacks); 恢复 proxy + 1 条 agent 完成 → overall PASS + flip 自动入账。本次被漏 22h 的组合故障模式现有哨兵覆盖。

## [2026-08-17 23:25] 回滚 31s 口径备案 (B4 闸门 ≤30s 边界案例)
- T3 回滚演练实测 31s = 含 8s 保守等待 (health 稳定观察窗); 紧等待口径收敛 ~23s (08-09 首测)。闸门 ≤30s 在保守口径下超限 1s, 记为边界案例; 后续演练注明口径。

[08-18 20:24] TODO(科研, 待批): per-case evidence card 立项 — K1.5 对照文档 §6.4: checkpoint report+judge report+B4 日志合成结构化卡片+leaderboard, 现有原料齐全, 低成本高价值增量
  → [08-19 CLOSED, 批复 ⑤]: 批准并**并入评测协议 v1 产出**（不单独立项）; scripts/eval_evidence_cards.py 随 v1 交付; 演示冻结窗内不碰前端（UI 展示层另行排期）
[08-18 20:24] TODO(科研, 待批): '金融文档领域首个 evaluation harness' 主张 targeted 检索验证 — 论文 B 投稿前必须定稿措辞(首个 vs 引入范式)
  → [08-19 CLOSED, 批复 ④]: 措辞定稿降级为"引入范式"（docs/33 §2.1 差异化第 3 条已改）; related work 补 FORCE-Bench（arXiv 2607.19409, Microsoft, 企业金融 agent 评测 harness; 对照口径=它评 agent QA 工作流 / 我们评解析管线+schema 漂移+勾稽+自学习闭环; 引用细节以 github.com/microsoft/FinanceBenchmark README 为准, 其 ~300 问与 arXiv 摘要 251 不一致已记录）
[08-19 00:42] 批复 ③ 入账: PSO 落点实现缓办 — 缓至 v1 + evidence card 交付之后, 且需与导师对齐专利申请时间表再定优先级; docs/33 §8 第 5 行已标 ⏸
[08-19 00:42] 批复 ⑥ 入账: 投稿节点定稿 — NLPCC 2026 已于 06-20 截稿、CCIR 2026 已开会 → 论文 A/B 节点改 NLPCC 2027 / CCIR 2027, 中间产出 arXiv 预印本占位; NLPCC 2026 workshop 窗口用户人工核实中（台账保持 pending 至核实回话）

[08-19 03:15] 治理决策项(待拍板): kiosk 播放持续写 config/schema_suggestions.json 计数 → Loop B STEP 4 脏文件报警周期性复发(本轮 00:01/00:34 即此因, 4fc251c 入账清除后 kiosk 又会写脏)。候选: a) Loop B STEP 4 对该文件 count-only 变更白名单(小改+演练) b) 定时入账清扫(治标) c) kiosk 停播(演示已结束, 但 B4 样本积累仍在用)。拍板前维持现状, 报警出现即按先例 commit 入账。
  → [08-19 20:05 CLOSED, 用户拍板选 a]: STEP4 白名单落地 25d2bec — 只豁免 config/schema_suggestions.json(运行时状态文件, 自学习闭环合法写入目标), 其余脏文件照常计数报警; 豁免清单写入脚本注释。不停 kiosk、不搞定时清扫; kiosk 建议计数继续观察, 单晚增量 41 条可接受(面板演示素材), 过大再议。daemon 已重启载入新版(治理规则), 首轮 20:04:53 验证 dirty_files=1 whitelisted=1 格式生效。
  [08-19 20:05 根因更正]: 本条原归因"STEP 4 脏文件报警"**有误** — 代码核查证实 STEP 4 只记数不判 FAIL(13:53 FAIL 与 14:26 PASS 同为 dirty_files=2 即反证); 00:01/00:34 两次 FAIL 实为 STEP 5 canary 在 judge --runs3 重负载窗口的超时误报(既有已知模式)。STATE.md 对应行同步更正。
[08-19 20:10] 新台账: Loop B canary 间歇 FAIL = kiosk wavefax 重传 ingest 竞态（证据链: ① 18:51 起 STEP 5 持续 3/4, 失败题恒为 adv_ocr_meta, 直连答案错引嘉合 PDF 而非 sample_20260506 ② 19:35 手动复现同题 PASS(50.9s, 答案与 sources 全对) ③ loop_demo.py L33 每轮 demo 循环重传 wavefax.pdf 触发重解析 ④ embeddings=137 未涨, 排除累积, 属瞬时竞态窗）。处置: 不停 kiosk(用户决定), 该模式记为已知干扰源; 后续若 canary FAIL 与 kiosk 上传窗口时间相关即按此归因, 不升级为服务退化; 根治候选(演示后议): ingest 原子化/去重幂等, 或 kiosk 上传段加节流。

## [2026-08-19 23:xx] DSpark 批复批量入账 (用户)
- ① GO 流程: :8006 基线矩阵回填 + Track C 审计 → 切换窗口申请(用户另行给窗); 回滚预案 = 原参数重起现容器(--rm, 启动命令已入 SOP), 切换前后各留一份 docker inspect 存档
- ② 思考档位 xhigh 起步不降档: medium 无质量数据, 降档 = 无依据质量回归; 切换后 B4 跑 2-3 天 + 同步补 medium 档 16 题矩阵, 数据说话再议
- ③ content=null 偶发 (xhigh 多轮 adv_multiturn 第二轮) = **已知边界**入台账: 切换后 B4 回落率 watchdog 的首要怀疑对象; 回落率异常即回滚
- ④ num_speculative_tokens=5 A/B → 切换后优化台账 (现 k=7 第 6/7 位接受率 14.3%/5.7% 近乎白算)
- ⑤ Route S 解除阻塞 + 归因更正: token 一直在 GB10 (~/.cache/huggingface/token, whoami wpxxqzh111, 有效至 2026-09-11); 原归因"GB10 无 HF token"有误 — 实为查找路径遗漏 (recipe 仓库在 GitHub 不在 HF: github.com/hasso5703/dgx-spark-qwen38)。**红线: token 只引用路径, 任何场合不打印值, 不入 git**。对照臂恢复执行, 时序不阻塞 Route V 切换
- ⑥ 生产 ask 46-48s 与 B4 交叉核对结论: **回落常态非退化** — timeout=45 era (08-19 01:00 起 n=791): agent-complete n=124 p50 37.8s (p95 44.6, max 45.2 贴门) / fallback n=509 p50 49.7s (=45s 超时+直连 ~5s) / pure-direct p50 23ms; 预算内完成率 ~20% (124/633) 即 DSpark 加速的直接动机; 停机窗口 (21:10-22:48) kiosk 全回落 46-55s 为 :8006 down 预期副作用
- ⑦ 镜像口径: 探针与生产同一镜像 dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1 — tag 为 recipe 版本, 内含 vLLM 0.27.2.dev0+g6e448d0ea.d20260815; 切换不换镜像 (详见探针报告)

## [2026-08-20 00:15] DSpark :8006 切换窗口执行 — 4 连败回滚, 生产已恢复
- 窗口 23:28-00:13: kiosk 暂停(本机 PID 158600 killed)→恢复(00:13, 新 PID 143516); B4 前置标记 2304 行 @23:28 — **窗口内无切换点, B4 统计连续不分段**
- DSpark 规格启动 4 连败, 同一根因: **KV 预算不足** (maxlen 32768 需 4.6 GiB; 实测可用逐次恶化 2.57→3.09→1.86→0.56 GiB; profiling peak 31.26 GiB vs 原配置 ~27.9)
- 根因链: ① Route S 下载 (sglang 镜像 3 次尝试 + HF 24GB NVFP4) 灌入 ~28-30GB page cache, CUDA mem_get_info 不计为可用 (reclaim 脚本注释同款机制); ② reclaim 35G×5 次上限只能到 ~50 GiB CUDA free (探针成功窗口为 69.46 GiB 干净 free); ③ DSpark drafter 2.53G + spec graph/activation 增量 ~3.4G 把 KV 挤过红线。下载停止后第 4 次尝试仍败 → page cache 残留层需比 reclaim 更强的驱逐手段 (无 sudo, 无法 drop_caches)
- 已执行对策(均不足): reclaim SOP ×5 / 下载暂停后重试 / 第 4 次在全部下载结束后启动
- 回滚: 原参数重起 00:12 READY → health/full 全绿 (137/local/healthy/llm_8004 ok/m2_rag ok) + :8006 快问正常 (冷态 26.9s, thinking off reasoning=null 生效); inspect 存档 dsaprk_switch_inspect_before_8006.json (切换前); 回滚后未做 after 存档 (容器=原配置, 与 22:06 恢复态一致)
- **重试菜单 (入台账等用户拍板)**: ① 干净窗口重试 — 切换前 24h 无大下载 + 多次 reclaim + 单次启动 (探针先例: 69.46G free 时全规格成功); ② MAXLEN=16384 (KV 需 ~2.3G 可容; 任务卡明示退路; 代价: agent 路 15-19k 长 prompt 截断风险, 需先评估 opencode 实际 context 分布); ③ GMEM 抬升 (SOP 明禁"只许调低不许调高", 需用户特批 + 内存算术); ④ 维持 Route V 探针结论 (GO 数据有效) 待条件成熟再切
- Route S 下载状态: HF 双权重 **DONE** (NVFP4@52d1adc / DSpark drafter@923ed3a, 坐实 ~/.cache/huggingface/hub); sglang 镜像 docker pull 3 次失败 (unexpected EOF + 502 Bad Gateway, dockerproxy 通道不稳), 重试缓至下次窗口合并

## [2026-08-20 21:14] DSpark 重试批复 + 专利 P3 批复入账 (用户)
### DSpark
- ① **选方案 1 干净窗口重试** (明晚 08-21 候选), 加两道闸 (已入 SOP FM8 + §0): a) 切换窗 = **纯窗口**, 禁止任何 download/pull — 大 I/O page cache 污染 GB10 内存预算 (CUDA 不计 page cache 为可用) 教训入 SOP; b) **预检闸**: reclaim 后 CUDA free ≥60 GiB 才许启动, 不达标当晚放弃, 杜绝连败
- ② 方案 2 (MAXLEN=16384) 为后备: 先量 opencode 实际 context 分布 (sidecar transcript / B4 token 数), **p99>16k 则放弃该退路** — 待执行
- ③ 方案 3 (GMEM 抬升) **不批** — SOP 红线 (只许调低不许调高), 探针已证 0.30 够用
- ④ **时序教训入账**: 上轮批复允许"下载与切换同窗"为失误, 此后切换窗 = 纯窗口, 任何大 I/O 提前完成或推后
- ⑤ **23:57/58 B4 悬案已查清**: 实为 23:56-23:58 共 4 条 (此前目测 2 条为少计), 全部是 **Loop B STEP 5 QA canary 哨兵** (23:52 周期跑到 STEP 5): q06_minan_cash_balance 23:56:13 / adv_ocr_meta 23:57:01 / adv_cross_doc 23:57:52 / adv_refusal 23:58:38, 与 CANARY_IDS 四项逐一吻合 (app.log Query 行 + loop_b_verify.sh L46 互证); **非 kiosk 残留非浏览器残留页**, kiosk 暂停有效; 后续切换窗内 canary 照常跑 (属预期治理流量), 如需静默可临时 LOOP_B_CANARY=0 (本轮不动 Loop B)
### 专利专项
- P1/P2 质量确认; **P3 启动**: 权 10 措辞差异化锚定"**确定性规则工件 + 回归验证门**", 防 Mem0/Letta 类通用记忆框架在先技术 (已写入 P2 权 10 锚定注记); 实施例三供数等 K7 (切换后第一周, 与 DSpark 重试互不阻塞); 发明人与时间表用户与导师确认后回

## [2026-08-20 21:50] opencode context 分布测量定论 → 方案 2 (MAXLEN=16384) 作废
- 触发: 批复② "先量 opencode 实际 context 分布, p99>16k 则放弃该退路" (DSpark 重试后备评估)
- 数据 (三源交叉, 全部生产真实流量, 数字未修饰):
  ① vLLM :8006 /metrics (08-20 00:12 回滚重启起 21.2h, n=1920): ≤1k 581 (30.3%) / 10k–20k 1213 (63.2%) / >20k 126 (6.6%); 平均 prompt 11,719; 累计秩计算 p95/p99 均 >20k
  ② opencode.log 同窗: 2337 stream 调用 (m2-qa 1757 + title 580) / 586 会话 / message=failed 556; ≤1k 桶与 title 调用 1:1 吻合; 417 次调用未达 vLLM (超时早杀)
  ③ 历史错误: 07-28 evidence-verifier 26,090 tokens vs 16,384 上限硬失败; 07-16 build 8,675 vs 8,192 硬失败; DB 残留旧时代样本 (thinking off) build max 19.1k
- **判定: p99 > 16k (实为 >20k) → 方案 2 正式作废**, 记 SOP FM9; [08-20 00:15] 重试菜单 ② 与批复 21:14 ② "待执行"  hereby CLOSED
- 附带观察 (记账不行动): a) message=failed 556 ≈ 每会话 1 次失败, 与 fallback kill 模式一致 (B4 回落主导的旁证), 非新问题; b) 现时代会话被 adapter ask 后删除, DB 不留 27B 时代样本, 分布测量以 metrics 直方图为准
- DSpark 重试 (08-21 晚候选) KV 防线确认 (08-20 辅助线更正): **预检闸 ≥60G 为唯一防线** — KV 需求由 maxlen×seqs 决定, 降 k 省不了 GiB 级缺口; 不过闸或启动再败即当晚放弃; k=7→5 A/B 定位更正为延迟/接受率优化项 (切换成功后与 medium 矩阵同批); MAXLEN 缩减不再列入菜单
## [2026-08-20 22:35] 辅助线抽验更正入账 (两项)
- 抽验结论: 三方 d778521 实测对齐; 分布结论 live 复验稳健 (n=1964, >20k 6.57%, p95/p99>20k 复算成立); Loop B 双周期 PASS; FM9/台账/dispatch 落位确认
- ① **pytest_latest.txt 工件陈旧** (内容为 18 passed 子集) → 本轮起每次收口将 GB10 全量 pytest 结果重定向入 logs/graph/pytest_latest.txt (GB10 本地工件, 不入 git, 与 benchmark_run.log 同级); 本轮已执行
- ② **k=7→5 定位更正**: 是延迟/接受率优化项, **非 KV 救援项** — 4.6 GiB KV 需求由 maxlen×max_num_seqs 决定, 降 k 省不了 GiB 级缺口; 重试窗唯一防线 = 60G 预检闸, 不过闸或启动再败即当晚放弃; k=5 A/B 留作切换成功后与 medium 矩阵同批跑。本日 THREADS/SOP FM9/STATE 中"KV 杠杆序"误述已同批更正
## [2026-08-20 22:35] DSpark :8006 切换窗口 (08-20 夜, 用户批准) — 预检闸未过, 当晚放弃, 原配置已恢复
- 窗口 22:16-22:35: kiosk 暂停 (本机 PID 143516/150708 killed, :5051 释放) → B4 前置标记 3064 行 → 切换前 inspect 存档 → docker stop (--rm 移除) → reclaim (buff/cache 降至 22G) → **预检闸: CUDA free 52.08 GiB < 60 GiB → 当晚放弃 (批复规则: 不二次尝试, 不恋战)**
- 恢复: 原参数重起 (/tmp/rollback_launch.sh) 22:23 启动 → 22:32 READY (编译缓存热; 权重 66 分片 @2.3s/片 + profiling) → 验证全过: /v1/models qwen38-27b-fp8 maxlen 32768 无 spec / health/full 全绿 (137/local/healthy) / canary adv_ocr_meta PASS (B4 22:34:41 direct fell_back=true 45162ms = 45s 超时+直连, 当前常态模式) / inspect 存档配对 (before 17797B / after-rollback 17796B, 均 0 处 speculative-config)
- kiosk 恢复 (PID 159568 controller + 159996 loop_demo, :5051 OK); B4 窗口间隙 3064→3065 (仅 canary 1 条, kiosk 零流量, 暂停有效); **无切换点, B4 统计连续不分段**
- Loop B: 22:15 周期 PASS (恰在停止前); 窗口内无周期触发, 无翻转; ~22:45 周期复验恢复态
- **开放问题 (明日评估, 今晚不擅动)**: 52.08 vs 探针成功窗 69.46 GiB 缺口 ~17G — reclaim 已执行, 候选方向: 更强驱逐手段 (无 sudo 无法 drop_caches) / 窗口内暂停非必要内存消费者 (zhikuncode docker 等, 需用户批准) / 实测各组件常驻内存定位占用源
- 存档路径 (GB10 本地, 不入 git): logs/graph/eval/dspark_switch_inspect_before_8006_0821.json + dsark_switch_inspect_after_rollback_8006_0821.json; 启动日志 /tmp/rollback_0821.log
- 重试: 等用户下一次窗口指令; 闸规则不变 (纯窗口 + reclaim 后 ≥60G + 单发起动 + 不达标即弃)
## [2026-08-21 00:00] DSpark 切换窗口 v2/v3 全程 — v3 成功, DSpark 在生产
### v2 (~22:5x): 闸过启动败 + 回滚两败 (当晚放弃)
- drop_caches 首次实战: buff/cache 24→2G, CUDA free 76.05G ≥60G 闸通过 (sudoers.d 窄授权生效)
- DSpark 启动败: KV 3.08 vs 需 4.6 GiB (GMEM 0.30 预算结构性不足 + padding 25% 浪费)
- 回滚两败 (2.13/2.47 vs 2.3): 权重加载吃回 MemFree → vLLM 预算截断 (#48140 机制) → **drop_caches 每次启动前必须重做**
- 误判更正入账: :5050 uvicorn workers (2104425/2104426) 永不杀; zhikuncode 220MiB 非嫌疑
### v3 (23:2x-23:5x): 批准参数变更 GMEM 0.34 + kv-cache-memory 6.0G 钉死 → 成功
- 首启失败 = 脚本编辑丢行续反斜杠, speculative_config=None 静默原配置运行; /metrics spec 计数器为 0 暴露 (追加验证①立功); 修复重起 23:41:20 → READY 23:48:08
- 引擎核验: SpeculativeConfig(dspark, /models/drafter, k=7) + trust_remote_code=True + reserved 6.0G KV (skipped profiling) + KV 42,711 tokens
- 验证组全过: health/full (137/local) / parse 冒烟 65ms / QA canary 2/2 (回落 direct 答案正确) / compare 嘉兴民安 2 持仓 / route=on timeout=45 / spec 计数器随请求增长 (drafts 117)
- **生产接受率 1.26 tokens/round vs 探针 3.31** (逐位 51/34/19/10/7/3/2%) — 探针高估生产收益, 如实入账
- **agent 路完成切换点以来 0 次** (B4 权威, 全 fell_back); eval 中间行 route=agent 标签 (35850/38677ms) 与 B4/报告 JSON 矛盾, 以 B4 为准, 异常记账待审
- B4 分段: 窗口开始 3081 → 切换点 **3092**; kiosk 恢复 (PID 23036/151364)
- 存档: inspect before_8006_0821v2 (0 spec) / after_dspark_8006_0821v3 (4 spec) 配对; 实验文档 docs/experiments/2026-08-20_dspark_switch_windows_v2v3.md; SOP FM8 对策③ + FM10
### 长期台账
- vLLM 版本升级评估: #46932 / #49760 / #48140 三项 issue 入账, 今晚不动版本
- 待审: ask 自然语言日期对比产品解析错配 (嘉兴民安→复熙, 规则路径与切换无关)
- 观察: agent 路完成率以 B4 数日数据为准 (watchdog 守护); k=5 A/B + medium 16 题矩阵仍排切换稳定后
[08-21 01:30] #NIGHT-LOOP-CLOSEOUT ① P4 专利完整修订版待用户终审 (docs/experiments/2026-08-21_patent_full_revised.md, 权 7-12 + 权 10 双锚定 + PSO 实测回填) ② B4 污染修复: M1_B4_LOG_PATH env 覆盖 + conftest 隔离 (生产行为不变无需重启); 24h checkpoint cron 一次性 23:50 (跑完人工删除); 真实 agent 完成维持 0, 接受率 1.33 ③ PSO 落点①v0: 分离度 +14.06%, research/pso/ 独立 venv ④ docs/33 §8 状态对齐
[08-21 01:45] #N3 C3 4B 探针 NO-GO(off 14/16, xhigh 13/16): 4B 思考负增益 + q08 在 4B 双档全过(小模型非必败)入账; :8007 已停; 报告 2026-08-21_small_model_matrix_c3.md
