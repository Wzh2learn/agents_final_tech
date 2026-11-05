
> 状态: 设计依据（现役使用说明 + 历史设计） | 更新: 2026-11-05 | 取代/被取代: 本件不提供任务授权或运行状态
> 治理规则（2026-08-24, 池×GUC 事故教训）: 任务卡含**多项同窗变更**时, premises 必含一条"交互假设检查"——
> 对每对同窗变更回答: 你们共同碰了什么资源/假设（连接生命周期/内存/文件/端口）, 一分钟证伪法是什么。
> 本次 GUC 兜底与实例缓存各自单项验证全绿, 经连接生命周期发生化学反应而无一捕获。

 # 17 - Graph Engineering: 多层 Loop 协同设计

 > **来源**: 基于文章《从 Loop 到 Graph Engineering 的演进思考与实战》(2026-07) 的核心思想，
 > 结合本项目 (JinRongAgents M1/M2) 的实际开发模式设计。
 > 文章核心参考: Carlos Perez《From Loop Engineering to Graph Engineering?》+ Peter Steinberger (OpenClaw) 的 Graph 范式讨论。

 > **现役职责**: 解释研发治理的 Loop/harness 关系；不是任务卡、排期表或当前运行快照。

 ## 现役使用说明（2026-09-22）

 - 协作闭环：**D 授权 → A 执行 → B 独立验证 → C 独立审计 → D 验收**；A 自测不代替 B/C 独立结论。
 - 具体任务、范围、模型、频率及执行面按当前用户授权与任务卡确定；规则、状态、未决分别归 [AGENTS](../AGENTS.md)、[STATE](../memory/STATE.md)、[THREADS](../memory/THREADS.md)，执行面边界见 [治理裁定](governance/2026-09-07_execution_plane_boundary.md)。
 - A/C 现役约束见 [Loop A prompt](../scripts/graph/loop_a_exec_constraints.md) 与 [Loop C prompt](../scripts/graph/loop_c_audit_prompt.md)；不再从旧模型、固定频率或 M1 单一目标推导任务。
 - `src/agents/` 是业务内 Agent 图，**不是研发 harness**；这里的 harness 是任务卡、`scripts/graph/`、hooks、skills 与独立验收组成的协作约束。
 - `graph_orchestrator.sh start` **实际只启动 Loop B**；A/C 分支仅打印派活说明，不代表已启动，也不是自动 A→B→C 流水线；其 `status` 也会探测服务。
 - `loop_b_verify.sh` 虽由脚本驱动，默认 canary / API / PG 检查有真实访问，可能触及模型后端，**不是零调用或离线单测**；运行须有相应授权并申报实际调用。
 - 仓内 scripts/hooks/skills 存在不等于机器已安装、钩链已接入或调度已生效；安装态和运行态须分别取证，不由目录或旧报告推断。
 - 非冻结测试可按授权合法补充或修复；不得擅改冻结节点、删除有效断言或削弱判据来制造通过。

## 科研协作增量：从候选到可复核结果（2026-11-05）

[ScientistTwo](https://arxiv.org/abs/2609.19644) 描述了文献局限与候选生成、强基线和小样本筛选、扩大实验、轨迹驱动修订、消融以及审稿反馈回流。论文还检查结果复现、任务规则、文献真实性和方法—代码一致性。这里借鉴其研究组织，而不声称已复现其闭环或效果；其模拟审稿评分不是实际会议录用，作者另报告有限的人类专家评估。

本项目沿用 D/A/B/C，按任务需要组合：D 明确问题与预算，A 按需实现与运行，B 或确定性脚本检查数据和结果，C 对值得独立检查的冻结快照提出审阅。以现有 `spec-first` 在原计划中记录来源、候选、基线、开发与确认数据、结果和下一步；保留未尝试候选及失败轨迹，并按证据回到设计或实验。成本、轮数与协作频率由任务和现有授权决定，失败、无定论、接口故障分别记录，不把模型评审视为人工裁决。

`scripts/graph/research_evidence_graph.py` 是**可选、离线、只读**的快照检查器：在调用者指定的根目录下，检查候选父子关系、实验和评审的引用，以及绑定文件的 SHA-256。示例与字段见脚本 docstring 和测试；运行 `python scripts/graph/research_evidence_graph.py --root <工作目录> <该目录内的快照.json>`。它不创建任务、派发 Agent、触发实验或修改账本；快照由使用者维护，并非持久队列。哈希只说明读取的文件与登记摘要一致，结构合格不证明结果正确、来源独立、文献真实、评审有效或获得执行授权。审稿反馈与消融的科学判断仍需 D 和合适的独立检查完成。

## 基建升级：事实、记忆与协作（2026-11-05）

本次按用户要求暂停科研目标，以**现有实现反向拆解**后选择增量改进。外部参考固定为 [Khazix Skills `35bd05b`](https://github.com/KKKKhazix/khazix-skills/tree/35bd05b466ceb83a727b28afb54b45b69a6c3b0a)、[Agent Autoloop `8f8e2ee`](https://github.com/KKKKhazix/agent-autoloop/tree/8f8e2eef3cfaa8f7a418818adc442450fe6bd884) 和 [DeepSeek Superagent 原型 `8c32a9d`](https://github.com/deepseek-ai/dsh-superagent-prototype/tree/8c32a9dc5d72c033816c6a8110b37f40cf94fba4)；均为 MIT 许可的参考源码，未直接安装自动调度器。参考原型、设计文章和本项目实测需分开，不能把源码设计当成本项目已上线能力。

现有 Graph Loop 的 D/A/B/C 已有角色划分和按需派发；业务层另有会话持久化、向量情景记忆与反射代码，但现役配置和运行态尚未在本次验证。外部值得借鉴的能力包括：控制层汇总状态、按任务隔离执行、可恢复的状态与去重、限制循环次数、以及引用原文而非只保留摘要；这些能力不能因为项目中存在同名文档就算已实现。用户提出的每日原文、摘要、知识关联、复习和反思是候选功能，不等于当前已有完整的八层记忆。

本批实施合同：

1. 从上游审计并升级现有 `neat-freak`，把目标编排的有效做法融入现有 `spec-first`，保留来源与分发一致性，不复制另一套重复 skill。
2. 为现有情景记忆元数据的会话归属加离线回归测试：普通附加元数据可保留，调用者给定的会话与类型不得被附加字段覆盖；从错误会话召回的条目不得返回。仅改内部实现，不访问数据库或生产服务。
3. 提供可选的离线上下文包：显式选择项目内 Markdown 原文，按预算保留完整行、来源路径与哈希；放不下的行必须保留可定位的溢出信息，不把摘要、第三方内容或历史结论升级成新指令。先做无模型、无网络、合成文件测试；不新建生产记忆数据库、不默认启动守护进程、不自动对外发送或触发执行。
4. 加固现有 A/C 派发入口的任务身份：同一任务 ID 与角色已有回执或日志时，不覆盖、不重新启动；不同角色仍可使用同一任务 ID。用替身 tmux 在临时目录测试并发争用和重试，不启动真实 Agent。
5. 用带稳定消息 ID 的合成对话验证增量反思：处理过的消息不重复摘要，40 条滑动窗口中的新消息仍可被处理；同会话并发不重复写入，保存失败不推进游标。游标暂限单进程，缺少稳定 ID 或游标已滑出窗口时明确停下，不伪造跨进程持久性。

完成标准：新增或更新的能力有可复现的正反例测试；用户授权的仓库、本机及 GB10 skill 分发分别核验；GitHub 在认证恢复前继续如实标记滞后。后续关于定时唤醒、多角色自主执行、跨端长期记忆和 KAG 的设计应沿用现有存储与权限边界，先在隔离环境验证，再决定是否接入运行面。

### 现有记忆与下一步

| 层面 | 仓库中可核实的实现 | 当前边界 |
| --- | --- | --- |
| 会话与项目状态 | `src/storage/chat_persistence.py` 提供会话数据库读写；`memory/STATE.md`、`THREADS.md` 是人工或 Agent 维护的项目状态和未决事项 | 两者用途不同；代码存在不等于所有宿主对话被采集或当前数据库已启用。 |
| 情景记忆 | `src/storage/memory/episodic_memory.py` 提供按会话写入和向量召回；检查点在 `src/storage/memory/memory_saver.py` | 本批固定写入的会话/类型元数据、向调用者返回适配器是否接受写入，并测试跨会话过滤；这不代替请求层的用户身份与会话归属认证，也不证明存储持久成功。后端可因配置或故障回退为进程内内存。 |
| 摘要与反思 | `src/biz/agent_service.py` 在代码路径上可触发 `src/tools/memory_reflector.py` | 原长度游标在 40 条滑动窗口满后会停更，且可能重复摘要；本批改为单进程消息 ID 游标，至少有 15 条未反思的人/AI 消息时处理最早 10 条，同会话并发和写入失败有离线反例。跨进程/重启不共享游标，缺 ID 或旧游标离开窗口会跳过并告警；若存储已写入但响应丢失，重试仍可能重复。反射工具仍配置外部模型接口，可能传送待摘要内容；本批未调用、未验证生产运行状态，个人对话接入前须先确定数据范围与授权。 |
| 关联、复习、梦境 | 有向量存储和 `dream-engine` 等 skill | 不等于已有完整 KAG、自动复习或持续自进化服务；应先使用可回溯的候选记录和隔离评测，再决定是否持久化或调度。 |
| 控制与派发 | D 负责主任务，A/C 按需独立执行/复核，B 为验证脚本；launcher 有状态和日志 | 当前不是持久化事件队列；上游 Superagent 的 worker 可拥有操作者完整系统权限，本批仅借鉴分层，不安装该原型或启动其对外连接。 |

建议逐步把原文引用、摘要、结构化候选和行动记录分层：每条候选保留来源、时间、适用范围和可撤回状态；召回时先限定用户/任务范围，再显式标明不确定性。复习或离线反思先以手动、私有、可回溯方式验证，避免把自动生成的推断直接写成长期事实。

### 可选上下文包

`scripts/graph/context_packet.py` 从显式列出的仓库内 Markdown 构造只读 JSON 交接包；默认使用 `STATE`、`THREADS`、`CORE` 和现役 Loop D 入口，按来源轮询并保留完整非空行。每个来源附原文件 SHA-256、行号和未纳入的行范围；字符预算仅计算正文，不等同于模型 token 或完整 JSON 大小。原文被更改或包内容被改写后，验证会失败。来源内容只是待解释的数据，文件哈希不证明结论真实，也不能代替对话级权限校验。

```bash
python scripts/graph/context_packet.py --max-chars 12000 --output /tmp/jinrong-context.json
python scripts/graph/context_packet.py --verify /tmp/jinrong-context.json
```

`--source` 可重复指定其他仓库内 Markdown；`--output` 只创建新文件，不覆盖原件。使用前自行确认所选文本可供目标 Agent 阅读；脚本不自动扫描个人会话、不连接模型或服务、不写数据库，也不自行启动其他 Agent。Windows 可将输出路径改为个人临时目录。

 > **历史阅读边界**：下文 §1–§8 保留原设计、菜单与演进证据，均不可直接派工；其中固定模型/频率、全 tests 禁改、强制 commit、自动启动及旧窗口承诺不构成现役权限。09-11 R3 解锁记录不等于本轮开窗授权。

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
 │  载体: Claude Code + mimo-v2.6-pro (2026-10-09 起)          │
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
 | API 端点真的能用 | `curl -s http://127.0.0.1:5050/health` 返回 200 (Loop B 实际锚点: GET /health, GET /api/m1/sample) | 不是日志写一句"成功" |
 | pytest 真的跑过 | Loop B 独立执行, 捕获完整输出 | 不是被标记 skip/xfail |
 | 甲方样本解析正确 | 真实 PDF/TXT/DOCX 解析结果 vs 人工标注 golden 值 | 不是合成数据自测 |
 | 模型服务真的在跑 | `curl http://127.0.0.1:8004/health` 返回 ok | 不是 ps aux 看到进程就算 |

 ### 3.2 Frozen Nodes (冻结节点) -- 执行层永远不能碰

 | 冻结对象 | 路径 | 校验方式 |
 |----------|------|----------|
 | 合约测试 | `tests/test_m1_service.py` | git diff --name-only 检查 |
 | 甲方真实样本 | `~/wzh/m1_samples/` (repo 外) | md5sum 清单比对 |
 | 字段定义 (冻结基准) | `~/wzh/m1_samples/m1_table_schema.json` | md5sum 与 scripts/graph/frozen_hashes.txt 比对 (config/m1_table_schema.json 为可写覆盖层, 非冻结) |
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

 ### 4.1 远端 GB10 模型服务（历史快照 07-29; 现拓扑见根 AGENTS.md / memory/CORE.md）

 | 端口 | 模型 | 用途 | 状态 |
 |------|------|------|------|
 | :8004 | Qwen3.6-35B-A3B Q4_K_M + **mmproj 视觉** | 主力 (Loop A/C) | 运行中, capabilities: [completion, multimodal] |
 | :8005 | Qwen3-14B Q4_K_M (20层GPU卸载) | 辅助 (Loop C 审计) | 运行中 |
 | :8100 | responses2chat proxy | 流式代理 | 运行中 |
 | :5050 | FastAPI 应用 | M1/M2 业务 API | 运行中 (2026-07-31 自 :5000 迁移) |
 | :15432 | PGVector | 向量数据库 | 运行中 |

 内存: 44GB / 121GB 已用, 77GB 可用。

 ### 4.2 待下载模型 (历史快照, 2026-07-29)

 | 模型 | 大小 | 下载位置 | 状态 |
 |------|------|----------|------|
 | ~~Qwen3-72B-Instruct Q4_K_M~~ | 44.1 GB | 已删除 | 2026-07-31 评估否决 (结构化提取退化), 2026-08-03 文件删除, 此节为历史快照 |

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

 ### 5.1 [HISTORICAL][P1] Codex CLI + GLM 5.2 模型配置测试

 **状态**: 历史失败记录，已被 2026-10-09 Xiaomi/agent_env 路由与 loop_ac_launcher 取代

 之前尝试在远端 Codex CLI 中配置 GLM 5.2 模型 (通过千问平台 Token Plan),
 配置后测试失败, 模型不可用。具体表现:
 - Codex CLI config.toml 中配置了 Token_Plan provider
 - GLM 和 DeepSeek 模型在 Codex CLI 中均无法调用
 - 怀疑是 Codex CLI 版本兼容性问题 (可能需要升级)
 - 参考文档: https://platform.qianwenai.com/docs/developer-guides/clients-and-developer-tools/codex

 **后续方向**:
 - 升级 Codex CLI 到最新版本后重试
 - 或确认千问平台 Token Plan 对 GLM 5.2 的支持状态
 - 当前 Codex CLI 使用 deepseek-v4-flash-0731 (2026-08-06 切换, 经 :8100 代理; 详见 memory/DECISIONS.md), 功能正常

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
 - 你不能修改: tests/test_m1_service.py, ~/wzh/m1_samples/, scripts/graph/frozen_hashes.txt (完整清单见该文件)。
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
 - 你的载体是 Claude Code (mimo-v2.6-pro, Xiaomi Anthropic 兼容端点, 2026-10-09 smoke PASS); 审计 prompt 见 scripts/graph/loop_c_audit_prompt.md。
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
| `scripts/graph/loop_d_daemon.sh` | Loop D | 战略层守护进程 |
| `scripts/graph/write_report.py` | Loop B | verify-report.json 写入 |
| `scripts/graph/sync_skills.sh` | 全局 | 仓库 skills/ → 各 harness 幂等分发 |

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


> **Loop A / Loop C 派活说明 (2026-10-09)**: 两者均为一次性派活，统一入口是 `scripts/graph/loop_ac_launcher.sh`。launcher 使用 detached tmux、外层 timeout、status JSON 和日志，避免 SSH 断线或前台超时杀掉任务。先 `preflight`，再 `start a|c <task-id> <prompt-file> [timeout-seconds]`；状态用 `status`，日志用 `logs`。旧手工 tmux 命令仅作历史记录，不再是现役派发入口。完整口径见 `docs/governance/loop_ac_launcher_v1.md`。

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

| 2026-08-04 | Phase 3 文档漂移修复: 端口 :5050、Loop C 载体 Claude Code + qwen3.8-max、冻结路径对齐 frozen_hashes.txt、72B 终态、§8 索引补全、Loop A/C 派活说明 | Loop D |
| 2026-08-08 | 漂移修复: Loop A 载体更新为 deepseek-v4-flash-0731 (08-06 起); 模型分工边界见 memory/DECISIONS.md | Loop D |
