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

## [2026-08-03] Loop A/C 模型路由收敛 qwen3.8-max
结论: Loop A (Codex CLI) 与 Loop C (Claude Code) 统一 qwen3.8-max; deepseek-v4-flash 试用结束; qwen3.8-max-preview 判不兼容 Claude Code。
理由: 22:28 双端验证通过 (codex exec / claude tool_use); preview 不跟随多步指令, 05:25 曾切回 deepseek-v4-flash-0731 (8e466ee 有其审计报告)。

## [2026-08-03] 遗留问题"记录不修"裁定
结论: OCR meta-query 接受 14/15=93% (高于 80% gate); 110/137 chunk product_name 元数据垃圾不修; .msg→htmlBody 预处理脚本暂不入库。
理由: T4 (23:36): 修复需 --reset 重灌 (会丢 scenario1 chunks) 或重做 ingest 注入, 风险>收益; 详见 blocked_questions.md。

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
