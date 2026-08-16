# memory/DECISIONS.md — 决策日志（只追加，不删改）

> 蒸馏自 logs/graph/dispatch_log.md、git log、docs/21、docs/22。格式: 日期 + 结论 + 理由。

## [2026-07-28] M2 检索默认采用 G 策略 (top_k=10 + bge-rerank → top-5)
结论: G 策略成为 M2 现役检索默认; 与已冻结的 TAT-DQA 研究线分开报告, 不得混报。
理由: 281089b 集成为默认并做 chunk 消融验证; AGENTS.md 明确两线口径独立。

## [2026-07-30] 不启动无监督整夜 Loop A; 甲方原始数据一律不入库
结论: Loop A 只做监督下的有界增量; 原始对账单与抽取 JSON 留 ~/wzh/, 仅脱敏汇总入库。
理由: docs/22 §5: 无人监督整夜写代码是 Graph Engineering 警告的反模式 (古德哈特+向上盲视); 客户数据红线。

## [2026-07-31] 影像件 OCR 纳入 M1 范围 (OCR 为主, mmproj 视觉为辅)
结论: Loop D 裁定 OCR 属 M1 任务范围, 派 Loop A 实现 image-only PDF/DOCX 的 OCR 回退。
理由: dispatch #1/#2: 3/5 真实样本 0 表, LU/xinhua 为纯影像件, 无 OCR 无法解析。

## [2026-07-31] AoE send 放弃, Loop A 任务改用 tmux 直启
结论: AoE session 模型与一次性 codex exec 不兼容; 改为 tmux new-session 直启, constraints+task 一起 pipe。
理由: dispatch 00:50: AoE send 对 codex exec 无效, respawn 会重跑原始命令; AGENTS.md 同录此注记。

## [2026-07-31] 立规: 禁止 amend 已验证 commit, 禁止 git add -A
结论: Loop B PASS 后不得 amend 该 commit; 只 add 自己修改的特定文件。
理由: dispatch 01:15/01:40: Loop C 第三次 amend 已验证 commit, git add -A 在 Loop A 运行期抢修改, 破坏验证闭环。

## [2026-07-31] PaddleOCR 放弃, vision-8004 定为永久 OCR 引擎
结论: PaddleOCR 在 GB10 ARM64 不可用; 解析器保留优雅降级 (_try_paddleocr 检测 env 不存在即交接 vision-8004)。
理由: dispatch #10: PaddlePaddle 3.2.2 aarch64 PIR 引擎模型加载 SIGSEGV; 已卸载清理, 调查报告 4a937fe。

## [2026-07-31] xinhua OCR chunks REVERT, 无金融结构样本不入库
结论: revert fcce4a4; ingest 增加"无金融结构即跳过"过滤 (531bcc0); xinhua 0 chunk 是正确行为, 线索 CLOSED。
理由: xinhua 实为操作流程文档, 强灌后 RAG QA 由 8/10 退化到 5/10 (BM25 搜索空间被污染); dispatch #12/#13。

## [2026-07-31] 72B 终判: 结构化抽取退化, 不适任 GB10 任何角色
结论: 72B 不常驻; 模型文件于 2026-08-01 02:10 删除, 释放 47GB。
理由: dispatch #15 (22:00): 3 查询全部退化输出, 比 35B 慢 14.1x, 占 46GB RAM; 35B+14B 架构维持最优。

## [2026-08-01] Ground truth 必须从原始文件独立复核, 禁止脱敏匹配自证
结论: boshi ground truth 按原始 PDF 修正 (cc6ad5b); 复核后字段正确率 21/21=100%。
理由: dispatch [19:12]: 脱敏掩盖循环论证 (错误基金名/代码产生相同 **** 模式), 2/3 样本干净, 1/3 中招。

## [2026-08-02] 三个 known gap 路径选定: 坐标重建 / OCR prompt 增强 / HTML body
结论: NCAMC 走 pymupdf 坐标重建 (路径 A, 弃规划的 VLM 路径 B); 华泰走 OCR prompt 增强+单空格宽松; email body 走 extract-msg htmlBody + BeautifulSoup (路径 D)。
理由: docs/21 §7: 三 gap 全部 SOLVED (NCAMC 0→1 表 75%, 华泰 0→1 表, email 0→9 表); VLM 被 Triton ARM64 阻塞, 坐标重建为替代方案。

## [2026-08-02] 嘉合新格式走 schema synonyms, 不做 parser 特判
结论: 表头适配优先补 config/m1_table_schema.json 同义词; 嘉合命中率 31.2%→93.8% (8 表)。
理由: de7336b 增 38 个 synonyms 达成; schema 是 ground truth 文件且已有自助 CRUD UI, 特判会破坏泛化。

## [2026-08-02] MCP env 修复与 OpenCode 启用暂缓 (决策点 D3=B, D4=B)
结论: 不修 3 个 MCP server 的 wzh_vllm conda env, 改用 Python 脚本直调模型; OpenCode 多 agent 启用推迟。
理由: docs/21 §3.3: MCP 依赖链太长 (conda env + PaddleOCR SIGSEGV + TabPFN env), gap 阶段投入产出比低。

## [2026-08-03] VLM(:8007/Triton/GGUF) 线彻底关闭
结论: Qwen3-VL-8B safetensors 被 Triton ARM64 JIT 阻塞, GGUF 国内不可得; 关闭此线, _try_vlm_table 代码保留作恢复路径。
理由: dispatch [04:35] eager/sdpa/TORCHDYNAMO_DISABLE 全失败; 22:50 T1 侦察: hf-mirror 302 海外 CDN ~1.5KB/s 断流, ModelScope 无仓库。
> SUPERSEDED 注 (2026-08-12 治理体检): "GGUF 不可得" 结论已被 2026-08-08 推翻并闭环 — hf-mirror 同步官方 GGUF 成功, :8007 一次点亮完成降采样实验; 终态 VERIFIED-CLOSED (命中率持平+延迟不达标), 见 memory/THREADS.md VLM 条。本条仅作历史轨迹保留。

## [2026-08-03] Loop A/C 模型路由收敛 qwen3.8-max
结论: Loop A (Codex CLI) 与 Loop C (Claude Code) 统一 qwen3.8-max; deepseek-v4-flash 试用结束; qwen3.8-max-preview 判不兼容 Claude Code。
理由: 22:28 双端验证通过 (codex exec / claude tool_use); preview 不跟随多步指令, 05:25 曾切回 deepseek-v4-flash-0731 (8e466ee 有其审计报告)。
> SUPERSEDED 注 (2026-08-12 治理体检): Loop A 部分被 [2026-08-06] 模型分工调整取代 (Loop A → deepseek-v4-flash-0731, 含回滚标准与派遣纪律); Loop C 全槽位 qwen3.8-max 仍有效。

## [2026-08-03] 遗留问题"记录不修"裁定
结论: OCR meta-query 接受 14/15=93% (高于 80% gate); 110/137 chunk product_name 元数据垃圾不修; .msg→htmlBody 预处理脚本暂不入库。
理由: T4 (23:36): 修复需 --reset 重灌 (会丢 scenario1 chunks) 或重做 ingest 注入, 风险>收益; 详见 blocked_questions.md。
> SUPERSEDED 注 (2026-08-12 治理体检): 部分取代 — OCR meta-query 08-05 已修 (15/15→08-09 扩库 16/16, THREADS OCR 条); .msg→htmlBody 08-09 已入库 (c863235 preprocess_msg.py); 仅 product_name 元数据 "记录不修" 仍有效。

## [2026-08-04] HANDOFF.md 冻结, 现状权威移交 memory/ 蒸馏层
结论: HANDOFF.md 冻结于 2026-08-03 快照不再更新; 现状快照一律写 memory/STATE.md; 阅读顺序 AGENTS.md → memory/STATE.md → docs/INDEX.md。
理由: Phase 2 整理专项 (a91ff74) INDEX.md 治理规则 2/4; Loop C M6 指出 memory/ 目录缺失, 本蒸馏补齐 DECISIONS/THREADS。

## [2026-08-04] Skill 武库: 仓库 skills/ 为唯一 source of truth
结论: 10 个 skill 入库 skills/, sync_skills.sh 幂等分发到 Loop A/C harness; 仅 Loop D 可安装新 skill, 弃用只标记不删除。
理由: dispatch 00:05 Phase 0 完成 (78ec44a/e86ff07); AGENTS.md 注册表 + 三层分发架构 + 治理规则四条。

## [2026-08-04] glm-5.2 × Codex CLI 端到端验证: PASS, 保留为备选模型
结论: 云端 glm-5.2 经 :8100 responses2chat 代理 (Token_Plan_Chat provider) 由 codex exec 端到端跑通 (exit=0, marker 命中, 连通性测试耗 14.5k tokens); 验证后配置逐字节回滚 qwen3.8-max 并复验 PASS。glm-5.2 保留为 Loop A 备选, 不作默认。
理由: thinking 常开消耗不可控, 与 2026-08-03 deepseek-v4-flash 裁定一致; codex 无 glm-5.2 metadata (fallback) 且代理 /v1/models 返回格式触发 models-manager 刷新错误, 均无功能影响, 记录不修。

## [2026-08-04] 记忆漂移案例: 已解决 3 gap 被误报挂起, THREADS 台账定基线
结论: Loop D 状态汇报将 NCAMC 垂直布局 / 华泰 OCR 纯文本 / email body 误报为"挂起 known_gap"; 实际 scenario1 已全部解决 (docs/21, 9ea3754: NCAMC pymupdf 坐标重建 0→1 表 75% b927efe, 华泰 markdown OCR prompt 0→1 / TraFax 0→3, email HTML 提取 3 封 0→9 表; nanhua 经 T3 再提升 24%→65.7%, parse_html 入库)。THREADS.md 补 scenario1 gap 台账。
理由: 蒸馏层未收录 gap 关闭信息, 新会话凭过时上下文口径即产生漂移——这正是记忆系统要防的场景; 今后 gap 状态变化必须同步更新 THREADS.md 台账。

## [2026-08-04] 夜间验收审计: CORE.md 基线漂移修复 + INDEX 重复登记 + 审计 prompt 端口残留
结论: 验收审计发现并修复 3 处漂移: ① CORE.md 质量基线仍将 NCAMC/华泰/email body 列为 known_gap（实际已 CLOSED，THREADS.md 已于 5545fde 校准）→ 改为实况; ② docs/INDEX.md 中 23/24 条目重复登记 4 次 → 去重; ③ scripts/graph/loop_c_audit_prompt.md 残留 :5000 端口 → 修正 :5050。
理由: 记忆系统要防的就是"台账类信息漂移"，本次为第二例（首例见 5545fde），校准依据同为 docs/21 执行结果节与 commit b927efe/9ea3754。

## [2026-08-05] embedding 切本地, 不恢复 SILICONFLOW_API_KEY
结论: .env 加 LOCAL_EMBEDDING_MODEL_PATH=~/wzh/models/hf/qwen3-embedding-0.6b + DEVICE=cpu; 同模型 drop-in, 存量 764 向量无需 re-ingest; MCP 链当日实测生效, :5050 重启后生效 (窗口需用户批准)。
理由: 用户决策"用本地的"; 实测 top-1 对齐全对 (0.564/0.587); CUDA 在 ARM64 不可用 (Triton gcc JIT 失败), CPU 226ms/2 条可接受。详见 docs/25 §4.0。

## [2026-08-05] 交付路线: A 保底 + B 目标, 先 A 后 B
结论: 路线 A (FastAPI 网关, 首灰端点 /api/m2/ask) 保底, 路线 B (OpenCode 原生入口) 为目标, A 稳后启动 B; A2 灰度开关须待 embedding 两步 (MCP + :5050 重启) 都落地再开。
理由: 用户拍板; 执行路径 A0-A3 / B0-B4 + B4 对等验收清单见 docs/25 §4。

## [2026-08-05] M1 解析热路径永远不走 agent
结论: /api/m1/parse-file 永远保持确定性进程内直调, 不接 agent 链; agent 只承接解释/复核/审计类增量能力。
理由: 用户明示指令; 解析是性能敏感确定性路径 (<2.1s), agent 链秒级延迟且引入不确定性。

## [2026-08-05] LoRA 微调不做, 重议需三条件同时满足
结论: 拒绝 LoRA; 仅当 ① 本地 embedding 稳定上线 ② 甲方标注数据成规模 ③ 存在 prompt/schema 手段修不掉的可度量失败 三条同时成立才重议。
理由: 用户决策; prompt+schema 扩展路线仍有空间 (嘉合 31.2%→93.8% 为例), 微调成本高且可控性差。

## [2026-08-05] 台账漂移案例 3: STATE.md 21:00 快照未随状态变化覆写（:5050 重启 / skill 注册误报未做）
结论: Loop C 审计发现 STATE.md 仍写 "m1-gap-triage 未注册未 sync 等用户审阅" 与 ":5050 up 未动（重启等用户批窗口）"，与事实不符（:5050 已于 23:09 重启载入本地 embedding、skill 已于 c5fd7c0 注册）。已覆写 STATE.md 闭环。补防漂移规则: STATE/THREADS 的 "已 X" 类断言必须以 dispatch_log 验证条目时间戳为准回写，写入前先对照。
理由: 第三例台账漂移（先例 5545fde/db6572b）；根因同前——快照型文档未在状态变化后复核，由审计层交叉核对 ps/dispatch 发现。

## [2026-08-06] 模型分工调整: Loop A → deepseek-v4-flash-0731, Loop D 子代理默认 flash (含回滚标准)
结论: Loop A (Codex CLI) 切换 deepseek-v4-flash-0731 (Token_Plan_Chat provider, 经 :8100 responses2chat 代理 v3.2; 备份 ~/.codex/config.toml.bak-20260806-flash); Loop D 子代理默认 flash (override 列表无则选最便宜可用并记录), 集成 review 与多模态仍用 qwen3.8-max; Claude Code 全槽位 (qwen3.8-max)、qwen_harness_tools.py (max-preview)、Loop D 主线程 (max)、reasoning effort xhigh 均不动。冒烟 PASS: codex exec 两数之和, 34s / 30.8K tokens (prompt 缓存 14.3K), exec_command 工具 round-trip 成立 (debug REQUEST 2 含完整 tool_calls + role=tool 历史), 最终响应 reasoning_tokens=0。
理由: 用户决策 (定价 ¥1/¥2/¥0.2 每 M); 模型 Chat-only 不支持 Responses API, 必须走代理。实测事实: 1M 上下文 / 393K 输出上限 / 纯文本; thinking 默认开启且先吃 completion 预算 (trivial prompt 16/17 token 为 reasoning; 探针 enable_thinking:false → completion=1/reasoning=0, 默认 → 47/44), token 估算须带推理开销。代理依赖: v3.2 (696dcbb/d0056a5/ad56ae2) 处理 codex 0.145.0 unified-exec exec_command/write_stdin ↔ chat function round-trip 与工具历史还原, 且强制 stream=False, 是本分工成立的前提; 代理回退 v2 及以下必失败。
回滚标准 (任一触发立即回滚, 无需确认): ① Loop A 连续两次任务失败 (空输出 / 工具调用循环 / 异常退出) ② 冻结节点异常 ③ 实测成本不降 (含 reasoning 开销后 ≥ max 同任务)。
回滚命令: sed -i 's/^model = "deepseek-v4-flash-0731"$/model = "qwen3.8-max"/; s/^model_provider = "Token_Plan_Chat"$/model_provider = "Token_Plan"/' ~/.codex/config.toml
派遣纪律: 即日起子代理默认 flash; 切换后首个 Loop A 正式任务完成时 Loop C 重点审计该 diff (用户明示)。
分工边界 (2026-08-07 用户补充): **flash = 代码执行/有界任务** (写码、修 bug、补测试、改配置, 目标明确 + 验收可机检); **长文读取/文档研读类子代理任务用 qwen3.8-max 或主线程直做**。依据: 2026-08-07 T2 文档审计事故 — 3 个 flash 级只读子代理在大范围读取任务上 1 个报错 (repetitive tool calls)、1 个输出复读退化、1 个跑偏, 全部由主线程重做; flash 在长上下文多轮只读场景的指令跟随不稳。已知非阻塞噪音: proxy WARNING unknown tool format external_web_access (codex 内置 web 工具, 丢弃); codex models-manager slug 报错 (cosmetic); rmcp chatgpt.com MCP 连接失败 (codex 尝试云端 MCP, 忽略)。
## [2026-08-08] 交付架构原则: 确定性→CLI, prompt 知识→skill/workflow, M2 远期 agent-loop
结论 (用户拍板): ① 能用确定性处理的环节一律用确定性 CLI 工具执行 (M1 解析链为该模式范本: opencode_m1_extract.sh 稳定入口 + parser 进程内直调, agent 只做调度与摘要); ② 需要 prompt 处理的知识规范成 skill 或 workflow 形式 (agent-prompt-contracts 契约库 + skills/ 版本化分发即为承载); ③ M2 当前保留灰度观察 (直连为主力, agent 路超时回落), 后续尝试以 agent loop 形式增强 RAG 任务 (多步检索/自检/查询改写迭代)。
理由: M1 已验证确定性链路的价值 (快路径 <2.1s 永久保留, 演示可复现); M2 的 agent 路价值在溯源遵从度与多步检索, 但延迟与方差仍需 B4 数据裁决, 故先观察后演进。本原则是 docs/25 路线 B 的落地取舍准绳。

## [2026-08-10] 场景 A 建议映射面板: 键匹配 + 用户 retarget 优先 + 回归门禁自动回滚
结论: apply/reject 按 (raw_column, table) 键匹配存储建议, standard_field 采纳请求侧值——UI 允许甲方改选目标字段, 后端不拒绝改选 (修复三元组精确匹配导致改选即 404 的 bug); apply 写 schema 后自动跑 scenario1 回归门禁 (--quick), FAIL 自动回滚 schema 并返 409, PASS 才落库 + 移入 applied。精确解析开关 (?llm_fallback=0, UI 勾选框) 作为确定性验证契约: AI 模式产生建议, 精确模式验证规则生效的命中率 delta。
理由: 甲方视角是"选择题"——改选是合法操作而非错误; 门禁保证任何沉淀规则不让既有命中率回归 (华泰 35.7%→100% 故事的防退化机制)。测试: tests/test_m1_schema_suggestions.py 10 case (含 retarget 与回滚)。
回滚: 面板为增量端点, 关闭不影响既有 /m1 功能; schema 误改可 git revert config/m1_table_schema.json。

## [2026-08-10] 台账漂移案例 4: "华泰紫金一轮 42.9%" 系样本张冠李戴（实为 233222LU 的数字）
结论: Loop C differential 审计 (docs/experiments/2026-08-10_audit_loop_c_differential.md F18) 查出 docs/23 等 6 处文档把华泰紫金一轮命中率写成 42.9%（实为 LU 样本某表数字），工件 final_results.json 实测 35.7%；同批国金 80%→70%、TraFax 单表值代表整份、30 表 vs 现行基线 31 表共 4 类漂移，已全部按工件校正并重生成发送版 docx。
理由: 第四例漂移（先例 5545fde/db6572b/2026-08-05 案例3）；本次根因是"故事性数字"在多文档间复制传播而无人回对原始工件。防御: 对外数字必须以 final_results.json / baseline JSON 为准, 文档修订时 grep 交叉核对; Loop C 发送前数字审计列为 docs/23 类文档的固定闸门。

## [2026-08-16] 模型升级专项 P0-P2: Qwen3.8-27B-FP8 探针闸门触发, 全量替换不通过 (模型卡)
结论: Qwen3.8-27B-FP8 + vLLM (vllm-gb10 v0.27.1) 探针 :8006 完成 P0-P2: 质量 GO (确定性 16/16 零回归, judge 交叉评 5.0≥基线 4.94, 视觉平手), 快路 FAIL (A_off p50=10.31s > 8s 闸门; 27B dense FP8 单流解码实测 ~4.8 tok/s) → **不做全量替换**。切换菜单 = 路线 A 双模型分工 (推荐先行: A3B 留快路+视觉, 27B 接 agent 验证链/judge/深度问答) vs 路线 B Qwen3.8-35B-A3B MoE 并行探针, 均待用户拍板; 详见 docs/32 §2.4。
模型卡 (候选): Qwen/Qwen3.8-27B-FP8 (hf-mirror, Apache); model_type qwen3_5 混合 linear+full attention, 原生 VLM, MTP, 262k ctx; 探针容器 vllm-probe: served-name qwen38-27b-fp8, GMEM=0.30, max-num-seqs 32, max-model-len 32768, reasoning-parser qwen3, tool-call-parser hermes。
思考档位实证: enable_thinking=false 零推理 (A 档); reasoning_effort 合法集 xhigh(默认)/medium/low (prompt 引导式); thinking_budget 模板不支持、传入被忽略; "high" 非法→400; vLLM 0.27 reasoning 存 message.reasoning 字段。
启动 SOP: scripts/gb10_reclaim_page_cache.sh 35 回收 page cache → GMEM=0.30 (0.27 差 0.44GiB) → --max-num-seqs ≤78 (Mamba 状态块约束) → 挂持久编译缓存; 冷启动 ~7min。
回滚 SOP (旧栈零损失): :8004 = LM Studio llama-server Qwen3.6-35B-A3B-Q4_K_M+mmproj (-c 65536 -ngl 999 --flash-attn on, pid 2642808); :8005 = llama-server Qwen3-14B-Q4_K_M (-c 32768 -ngl 20, pid 2645844); 完整 cmdline 见 dispatch_log 08-15 P0 条目; 旧 GGUF + llama-server 保留 48h (至 2026-08-17 18:00); 回滚 = docker stop vllm-probe + 按上述参数重启 llama-server, 预计 <2min。
理由: P2 闸门规则为用户预设 (A 档 p50>8s → 不全量替换, 出对比菜单); GB10 273GB/s 带宽是 dense 27B 快路的硬约束, 并发 3 流实测单请求劣化 7x 进一步坐实带宽受限。NF 未对候选重跑 (脚本锁 :5050 生产端点, 红线不重启), 留 P3 切换验证。

## [2026-08-16] 思考控制操作契约 (Qwen3.8 + vLLM 0.27, S1 沉淀补强)
结论: Qwen3.8 系开源模型 + vLLM 的思考深度唯一有效旋钮是 reasoning_effort, 合法集 {low, medium, xhigh} (默认 xhigh); "high" 为非法值→400, 需要高档必须写 xhigh; thinking_budget 被 chat template 忽略, 行为等同 xhigh (不得依赖它做封顶); enable_thinking=false = 零推理 token (快路)。vLLM 0.27 的 reasoning 输出内联于 message.reasoning 字段 (不在 content)。请求级经 chat_template_kwargs 传递; 探针/benchmark/judge 脚本均按本契约。
理由: P2 三档矩阵实测 (A_off 零推理 / effort low / xhigh 行为与契约一致); 本条为 08-16 模型卡"思考档位实证"的操作化表述, 防下次启动/接线时把 "high" 当合法值或误信 thinking_budget。详见 docs/architecture/gb10_vllm_startup_sop.md 与 docs/32 §2.2。

## [2026-08-16] 模型升级 S4: 双模型拓扑接线完成 (A3B 守快路 + 27B 接验证链/judge)
结论: 路线 A 接线完成 (配置层 only, 零重启)。opencode.json 增 gb10v provider
(经 thinking_inject_proxy :8008 → vLLM :8006), m2-qa + evidence-verifier 切
qwen38-27b-fp8 (服务器模板默认 thinking off + 代理注入兜底); m1-extraction /
tabular-* 保持 :8004 A3B (M1 热路径红线); judge 经 .env M2_JUDGE_ENDPOINT 指
:8006 (显式 enable_thinking=false 透传, 与 4.94/5.0 实测口径行为对等)。
实测发现: ① vLLM 0.27 reasoning-parser 按请求级显式 enable_thinking 键控
(FM5), 服务器模板默认不能替代 → 注入代理为必需件 (详见 SOP FM5); ② 27B agent
验证会话实测 首轮 ~30s / 热态 72s / 个别 >120s 超时, 慢于 A3B 的 39-55s
(dense 解码多轮累积), OPENCODE_ASK_TIMEOUT=18 下继续全回落 — 用户可见行为与
切换前一致 (零回归); ③ 接线验证 = 会话 modelID=qwen38-27b-fp8 坐实 + 代理
三态测试通过。
超时重议: OPENCODE_ASK_TIMEOUT 为模块级 env, 调整需 :5050 重启窗口; 与 M2
菜单项 (skill 预载/降轮次/档位感知超时) 合并待用户拍板。
回滚: opencode.json gb10v baseURL 与 m2-qa/evidence-verifier model 回指
gb10/qwen3.6-35b-a3b (配置级 <1min); 代理可 tmux kill thinking-proxy 停;
48h 旧栈回滚窗口 2026-08-17 18:00 到期 (不变)。
