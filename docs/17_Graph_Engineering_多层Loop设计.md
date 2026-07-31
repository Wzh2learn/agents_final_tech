 # 17 - Graph Engineering: 多层 Loop 协同设计

 > **来源**: 基于文章《从 Loop 到 Graph Engineering 的演进思考与实战》(2026-07) 的核心思想，
 > 结合本项目 (JinRongAgents M1/M2) 的实际开发模式设计。
 > 文章核心参考: Carlos Perez《From Loop Engineering to Graph Engineering?》+ Peter Steinberger (OpenClaw) 的 Graph 范式讨论。

 > **本文档面向**: 指挥层 (本机 Codex + 用户) 和执行层 (远端 GB10 Codex CLI / OpenCode)。
 > 任何 Loop 在启动前应阅读本文档，理解自己在 Graph 中的位置、约束和汇报对象。

 ---

 ## 1. 为什么要从双 Loop 升级到 Graph

 ### 1.1 之前的结构 (双 Loop)

 ```
 用户 + 本机 Codex (指挥层)  ──指令──>  远端 Codex CLI / tmux (执行层)
 ```

 ### 1.2 双 Loop 的结构性缺陷

 对照文章提出的四种单 Loop 失败模式，我们实际踩过的坑:

 | 失败模式 | 文章定义 | 我们的实际表现 |
 |----------|----------|----------------|
 | **古德哈特定律** | 单指标优化导致刷分 | 执行层自己写代码、自己跑 pytest、自己报 "18/18 passed"，既是运动员又是裁判 |
 | **向上盲视** | Loop 不质疑目标本身 | TAT-DQA 实验持续优化，不会自己判断"甲方需求已变，该冻结了" |
 | **冲突** | 多 Loop 互相打架 | codex-m1-verify / codex-m1-batch / codex-m1-schema 多个 tmux 共享 :8004 和 git 工作区，互相踩踏 |
 | **测量衰减** | 偷偷改考题 | tests/ 和 samples/ 理论上可被执行层修改后重新跑"通过率 100%" |

 ### 1.3 Graph Engineering 的核心思想

 **"Loops watching loops"** -- 用不同速度的循环互相监督:

 - 快循环: 日常执行 (每天称体重)
 - 中速循环: 独立验证 (每月体检)
 - 慢循环: 方法审计 (每季度复盘方法是否科学)
 - 超慢循环: 目标校准 (问自己"为什么要减肥? 70kg 这个目标对吗?")

 三个安全机制:

 - **Anchors (锚点)**: 不可自欺的外部事实 (钱真的到账了，不是报告写了"成功")
 - **Frozen Nodes (冻结节点)**: 优化器永远不能碰的规则 (测试集不可篡改)
 - **External Judgment (外部判断)**: 人来决定"什么值得追求"

 ### 1.4 Graph vs Workflow 的区别

 我们做的不是 CI/CD pipeline (固定流水线)，而是多个不同节奏的循环在动态制衡。
 Loop C 可以驳回 Loop A 三天的工作; Loop D 可以冻结整个 Loop A 换方向。
 图不是预先画好的，而是在运行中动态显现的。

 ---

 ## 2. 我们的四层 Graph 设计

 ```
 ┌─────────────────────────────────────────────────────────┐
 │  Loop D: 战略层 (超慢)                                   │
 │  载体: 用户 + 本机 Codex (本对话 / 主线程)                │
 │  频率: 每天 / 按需                                       │
 │  职责: 目标校准, 优先级仲裁, 冻结/解冻工作流              │
 │  典型决策: "M1 甲方需求优先于通用方法论"                   │
 │           "TAT-DQA 冻结"                                │
 │           "OCR 为主, 视觉为辅"                           │
 │  权限: 可推翻任何下层 Loop 的判断                         │
 └──────────────────────┬──────────────────────────────────┘
                        │ 目标 + 约束 + 冻结指令
 ┌──────────────────────▼──────────────────────────────────┐
 │  Loop C: 质量审计 (慢)                                   │
 │  载体: 远端 tmux codex-audit + Codex CLI (:8005 14B)     │
 │  频率: 每轮执行完成后 / 每 4-6 小时                       │
 │  职责:                                                   │
 │    - 用真实甲方样本 (~/wzh/m1_samples/) 端到端验证        │
 │    - 审查代码变更是否偏离甲方需求                         │
 │    - 检查 Loop A 有没有"改考题" (冻结文件完整性)          │
 │    - 评估架构漂移 (是否引入了不必要的复杂度)              │
 │  输出: 审计报告 -> docs/experiments/ 下                   │
 │  权限: 可驳回 Loop A 的产出, 要求重做                     │
 └──────────────────────┬──────────────────────────────────┘
                        │ 审计报告 + 驳回/通过
 ┌──────────────────────▼──────────────────────────────────┐
 │  Loop B: 独立验证 (中速)                                 │
 │  载体: 远端 tmux verify-guardian + 纯 bash 脚本          │
 │  频率: 每次 Loop A 产生 git commit 后 / 每 30 分钟轮询    │
 │  职责:                                                   │
 │    - git pull 拉最新代码                                 │
 │    - 校验冻结文件 hash (tests/, schema, samples)          │
 │    - 独立跑 pytest tests/test_m1_service.py -v           │
 │    - curl API 端点验证真实响应                            │
 │    - 写 verify-report.json                              │
 │  关键: 纯脚本, 不用 AI, 不会"耍花招"                    │
 │  权限: 冻结文件被篡改 -> 立即驳回 + 告警 Loop D          │
 └──────────────────────┬──────────────────────────────────┘
                        │ 通过 -> 允许继续 / 失败 -> 打回
 ┌──────────────────────▼──────────────────────────────────┐
 │  Loop A: 执行层 (快)                                     │
 │  载体: 远端 tmux codex-m1-exec + Codex CLI (:8004 主力)  │
 │  频率: 持续自主                                          │
 │  职责: 写代码, 修 bug, 迭代解析逻辑, 完善 UI             │
 │  约束:                                                   │
 │    - 不能修改 tests/ 和 ~/wzh/m1_samples/                │
 │    - 每次产出必须 git commit                              │
 │    - 等 Loop B 验证通过后才能继续下一个任务               │
 │    - 不能自行调整目标优先级                               │
 └─────────────────────────────────────────────────────────┘
 ```

 ---

 ## 3. 安全机制落地

 ### 3.1 Anchors (锚点) -- 不可自欺的事实

 | 锚点 | 验证方式 | 说明 |
 |------|----------|------|
 | API 端点真的能用 | `curl -s http://127.0.0.1:5000/api/m1/parse-file` 返回 200 + 有效 JSON | 不是日志写一句"成功" |
 | pytest 真的跑过 | Loop B 独立执行, 捕获完整输出 | 不是被标记 skip/xfail |
 | 甲方样本解析正确 | 真实 PDF/TXT/DOCX 解析结果 vs 人工标注 golden 值 | 不是合成数据自测 |
 | 模型服务真的在跑 | `curl http://127.0.0.1:8004/health` 返回 ok | 不是 ps aux 看到进程就算 |

 ### 3.2 Frozen Nodes (冻结节点) -- 执行层永远不能碰

 | 冻结对象 | 路径 | 校验方式 |
 |----------|------|----------|
 | 合约测试 | `tests/test_m1_service.py` | git diff --name-only 检查 |
 | 甲方真实样本 | `~/wzh/m1_samples/` (repo 外) | md5sum 清单比对 |
 | 字段定义 | `docs/m1_schema/*.json` | git diff 检查 |
 | 评测基准 | `docs/experiments/` 下已归档报告 | 只增不改 |

 Loop B 在每次验证前执行冻结检查。如果发现被篡改:
 1. 立即驳回本轮所有产出
 2. 写告警到 verify-report.json
 3. 等待 Loop D (人) 介入裁决

 ### 3.3 External Judgment (外部判断) -- 人决定的事

 以下决策只有 Loop D (用户) 有权做出，任何下层 Loop 不能自行推翻:

 - 工作流优先级 (M1 甲方需求 > 通用方法论)
 - 工作流冻结/解冻 (TAT-DQA 已冻结)
 - 技术路线选择 (OCR 为主 / 视觉为辅 / 模型选型)
 - 交付标准 ("good enough" 的定义权)

 ---

 ## 4. 当前基础设施状态

 > 更新时间: 2026-07-29 23:10 CST

 ### 4.1 远端 GB10 模型服务

 | 端口 | 模型 | 用途 | 状态 |
 |------|------|------|------|
 | :8004 | Qwen3.6-35B-A3B Q4_K_M + **mmproj 视觉** | 主力 (Loop A/C) | 运行中, capabilities: [completion, multimodal] |
 | :8005 | Qwen3-14B Q4_K_M (20层GPU卸载) | 辅助 (Loop C 审计) | 运行中 |
 | :8100 | responses2chat proxy | 流式代理 | 运行中 |
 | :5000 | FastAPI 应用 | M1/M2 业务 API | 运行中 |
 | :15432 | PGVector | 向量数据库 | 运行中 |

 内存: 44GB / 121GB 已用, 77GB 可用。

 ### 4.2 待下载模型

 | 模型 | 大小 | 下载位置 | 状态 |
 |------|------|----------|------|
 | **Qwen3-72B-Instruct Q4_K_M** | 44.1 GB | `~/wzh/models/gguf/qwen3-72b/` | 下载中 (tmux: download-72b), ~12% @ 9.7MB/s, 预计 ~77min |

 下载完成后需要 Loop D 决定: 替换 35B-A3B 做主力, 还是作为第三模型并存。
 72B 加载后预计占用 ~46GB, 与 14B 辅助共存后总占用 ~60GB, 仍剩余 ~60GB。

 ### 4.3 已有模型资产 (磁盘)

 | 模型 | 路径 | 大小 |
 |------|------|------|
 | Qwen3.6-35B-A3B Q4_K_M | ~/.lmstudio/models/.../Qwen3.6-35B-A3B-GGUF/ | 20 GB |
 | Qwen3.6-35B-A3B mmproj | 同上 | 861 MB |
 | Qwen3.5-35B-A3B Q4_K_M | ~/.lmstudio/models/.../Qwen3.5-35B-A3B-GGUF/ | 20 GB |
 | Qwen3-14B Q4_K_M | ~/wzh/models/gguf/qwen3-14b/ | 8.4 GB |
 | Qwen3-8B Q4_K_M | ~/wzh/models/gguf/qwen3-8b/ | 4.7 GB |
 | Qwen3-4B Q4_K_M | ~/wzh/models/gguf/qwen3-4b/ | 2.4 GB |

 ### 4.4 OCR / 视觉模型

 - PaddleOCR-VL: conda env `wzh_vision` (保持可用, 作为 OCR 主力)
 - Qwen3.6-35B-A3B mmproj: 已激活 (作为视觉增强保底, 不替代 OCR)

 ---

 ## 5. 待办事项 (Pending)

 ### 5.1 [P1] Codex CLI + GLM 5.2 模型配置测试

 **状态**: 失败, 待后续排查

 之前尝试在远端 Codex CLI 中配置 GLM 5.2 模型 (通过千问平台 Token Plan),
 配置后测试失败, 模型不可用。具体表现:
 - Codex CLI config.toml 中配置了 Token_Plan provider
 - GLM 和 DeepSeek 模型在 Codex CLI 中均无法调用
 - 怀疑是 Codex CLI 版本兼容性问题 (可能需要升级)
 - 参考文档: https://platform.qianwenai.com/docs/developer-guides/clients-and-developer-tools/codex

 **后续方向**:
 - 升级 Codex CLI 到最新版本后重试
 - 或确认千问平台 Token Plan 对 GLM 5.2 的支持状态
 - 当前 Codex CLI 使用 qwen3.8-max-preview 作为替代, 功能正常

 ### 5.2 [P2] Qwen3-72B 下载完成后的评估

 下载完成后:
 1. 在 :8006 临时加载, 用甲方样本做对比测试 (72B vs 35B-A3B)
 2. 评估中文金融对账单解析质量差异
 3. 由 Loop D 决定是否替换主力

 ### 5.3 [P2] Graph Engineering 各 Loop 的实际部署

 本文档是设计稿。实际部署顺序:
 1. **Loop B (独立验证脚本)** -- 最基础, 纯 bash, 优先实现
 2. **Loop C (质量审计)** -- 需要设计审计 prompt + 甲方样本 golden 值
 3. **Loop A 约束改造** -- 在 Codex CLI 的 system prompt 中加入冻结规则
 4. **Loop D 汇报机制** -- 本机 Codex 定期轮询远端状态

 ### 5.4 [已冻结] TAT-DQA 实验

 不再投入新的开发资源。已有产出保留在 docs/experiments/ 下。
 解冻需 Loop D (用户) 明确指令。

 ---

 ## 6. 给各 Loop 的启动提示

 ### Loop A (执行层) 启动时应知:

 ```
 你是 Graph 中的执行层 Loop A。
 - 你的产出会被 Loop B (独立脚本) 验证, 被 Loop C (审计 Agent) 审查。
 - 你不能修改: tests/, ~/wzh/m1_samples/, docs/m1_schema/。
 - 每次完成任务必须 git commit, commit message 写清楚做了什么。
 - 你不能自行调整优先级或冻结/解冻工作流。
 - 如果 Loop B 验证失败, 根据 verify-report.json 修复后重新提交。
 - 如果 Loop C 驳回, 阅读审计报告, 修正方向后重做。
 ```

 ### Loop C (审计层) 启动时应知:

 ```
 你是 Graph 中的质量审计 Loop C。
 - 你的职责是审查 Loop A 的产出是否真正服务于甲方对账单解析需求。
 - 用 ~/wzh/m1_samples/ 中的真实文档做端到端验证。
 - 检查代码变更是否引入不必要的复杂度或架构漂移。
 - 检查冻结文件是否被篡改 (配合 Loop B 的 hash 校验)。
 - 你的审计报告写入 docs/experiments/, 格式: YYYY-MM-DD_audit_*.md。
 - 你使用 :8005 (Qwen3-14B) 作为推理引擎, 不占用 :8004 主力。
 - 你可以驳回 Loop A 的产出, 但不能自行修改代码。
 ```

 ---

 ## 7. 演进记录

 | 日期 | 变更 | 决策者 |
 |------|------|--------|
 | 2026-07-29 | 初始设计, 基于 Graph Engineering 文章 | Loop D (用户 + 本机 Codex) |
 | 2026-07-29 | :8004 激活 mmproj 视觉能力 | Loop D |
 | 2026-07-29 | :8005 Qwen3-14B 辅助模型上线 | Loop D |
 | 2026-07-29 | Qwen3-72B Q4_K_M 开始后台下载 | Loop D |
 | - | TAT-DQA 冻结 | Loop D |
 | - | M1 甲方需求优先于通用方法论 | Loop D |
| - | OCR 为主, 视觉为辅 | Loop D |

 ---

 ## 8. 实现文件索引

 所有实现文件位于 `scripts/graph/` 目录:

 | 文件 | 对应 Loop | 说明 |
 |------|-----------|------|
 | `scripts/graph/frozen_hashes.txt` | Loop B | 冻结节点 MD5 清单, Loop B 校验基准 |
 | `scripts/graph/loop_b_verify.sh` | Loop B | 独立验证脚本 (纯 bash, 不用 AI) |
 | `scripts/graph/loop_c_audit_prompt.md` | Loop C | 质量审计 Agent 的 system prompt |
 | `scripts/graph/loop_a_exec_constraints.md` | Loop A | 执行层约束指令 + 冻结规则 |
 | `scripts/graph/loop_d_monitor.sh` | Loop D | 战略层状态监控 (可 SSH 远程调用) |
 | `scripts/graph/graph_orchestrator.sh` | 全局 | 编排器: start/stop/status/logs |

 ### 快速启动

 ```bash
 # 在远端 GB10 上:
 cd ~/wzh/projects/agents_final_tech

 # 启动所有 Loop
 bash scripts/graph/graph_orchestrator.sh start

 # 查看状态
 bash scripts/graph/graph_orchestrator.sh status

 # 查看日志
 bash scripts/graph/graph_orchestrator.sh logs

 # 停止所有 Loop
 bash scripts/graph/graph_orchestrator.sh stop
 ```

 ### 从本机 (Loop D) 远程监控

 ```powershell
 # 战略层状态一览
 ssh jinrong-dev "bash ~/wzh/projects/agents_final_tech/scripts/graph/loop_d_monitor.sh"

 # 单独跑一次 Loop B 验证
 ssh jinrong-dev "bash ~/wzh/projects/agents_final_tech/scripts/graph/loop_b_verify.sh"
 ```

| 2026-07-30 | 过夜 Loop D 监督：M1 解析 unmapped 5→3（kv 路由+标准名优先）；switch 助手；72B vs 35B 有界对比（72B 跑完即 kill） | Loop D |
| 2026-07-30 | 战略仲裁：未启动 Loop A 自主写代码；72B 不整夜常驻；严格 JSON 调优延后交互；客户原始数据不入库 | Loop D |
| 2026-07-30 | Loop B 守护常驻 + Loop D 影子；Loop C 按需；详见 docs/18 | Loop D |
| 2026-07-30 | 第二轮：事1 修 /m1 页面路由 gap(1472c6a)；事2 v3 enable_thinking=false 35B 修好 72B 退化(a8f640f)；事3 冷启动列暂不建模(1472c6a)；事4 不开 Loop A；事5 72B 按需临时 | Loop D |
| 2026-07-31 | 8h 自主循环完成：8 轮 Loop A + 6 轮 Loop C + Loop B 持续 PASS；M1 解析率 20%→100%；reconcile 全 PASS + disposition；M1→M2 RAG 闭环 3/3；OCR 并行 200s→74s；15 commits；Loop C 连续 3×ACCEPTED 降频至 12h | Loop D |
| 2026-07-31 | Graph 运行模式确立：Loop B 常驻 30min 周期；Loop C 降频 12h；Loop A 待命派活；AoE send 不适用 codex exec（一次性），改用 tmux 直启 | Loop D |
| 2026-07-31 | 流程修复 5 项：anti-amend 规则、anti-git-add-A、API_BASE :5050、disposition 字段、OCR 并行化 | Loop D |
