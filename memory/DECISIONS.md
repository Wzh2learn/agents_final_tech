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
