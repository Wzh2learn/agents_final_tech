# Loop A 任务：T4 R 适配器与基线（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T4.md` 执行；卡内 `D:/AIRcommend/JinRongAgents/agents_final_tech/...` 路径在本机等价于 `~/wzh/projects/agents_final_tech/...`（仓库根）。**完成后必须自检并修到干净再交付**（后续仅 1 次 Loop C 评审名额）。

## 背景与依赖（先读，只读）
- `AGENTS.md`；`cards/T4.md`；`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`；`evaluation/reliability_spec.md`。
- PREFLIGHT 权威：`docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`（只读；级别定义 UNIT/COMPONENT/CONTRACT/INTEGRATION/END_TO_END_PREFLIGHT/FORMAL_RUN，任何 PASS 必须带级别+范围，不允许裸 PASS）。
- 协议 FROZEN（`282f5213…`）。依赖已验收：T1 v3 run `runs/T1/20261014T141004Z_2647a7e1/`（16 案例，评审 T1I-03）；T3 run `runs/T3/20261014T161814Z_245b86ab/`（可信执行，评审 T3R-01）。T2 评价器（`runs/T2/20261014T145327Z_9a02a34a/` + T2R-01）作为基准评测底座身份一并绑定。把上述路径+哈希绑定进 receipt。
- 本卡预算 B0：**零** 模型/网络/远程/生产/数据库/训练调用；零自动重试。

## 写入所有权（硬）
- 只允许在 `research/harness_rsi_v1/runs/T4/<run_id>/` 下创建产物（run_id = 执行时 UTC `YYYYMMDDTHHMMSSZ` + `_` + UUID 前 8 位；已存在换新 ID；不覆盖）。不改任何其他文件；不做 git commit/push。
- 第一个动作：把本任务书原文复制到 run 目录 `TASK_PROMPT.md` 并记录 sha256。
- 所有复盘 fixture、工具运行现场只准写本 run 目录内（如 `scratch/`）；**不得触碰真实仓库文件、旧实验/历史 run 目录、生产与 daemon**。工具如需要输入，使用只读副本。

## 任务范围（bounded v1）
1. **`adapters/` — 现有检查工具的只读适配**。
   - 先做工具盘点与副作用核实：候选在 `scripts/graph/` 内，例如：
     - 预检类：`dispatch_precheck.sh`（watcher 双实证合同校验，只读取证）、`formal_experiment_preflight.py`（fail-closed 正式预检验证器；FinQA/formal 专用资格语义）；
     - 摘要类：`hooks/summary_recompute_guard.py`（声明摘要≠存储工件，机械复算；gen/check）；
     - 证据/索引类：`hooks/index-guard.precommit.sh`、`hooks/large-file-guard.precommit.sh`、`frozen_hashes.txt` 只读哈希校验、`governance_drift_scan.py`、`check_skill_sync.sh`、`generate_repository_receipt.py`（按适用性取舍）。
   - 逐工具核实：会写哪些路径、是否触发服务/cron/网络/daemon。只适配**获准离线入口**（只读调用形态）；任何带副作用或需要在线环境的入口**不得直接运行**，在 receipt 中记录排除原因。
   - **明确排除**：`loop_b_verify.sh`（现役验证 daemon，硬禁止运行——验收 A3「无现役 Loop B 执行」）；一切网络/服务/模型路径。
   - 适配器只准做"路由到已存在离线入口 + 结果结构化"；**不得修改工具、不得扩展其作用域、不得包装增强语义**（验收：不扩张旧检查器作用域）。
   - `adapters/README.md`：每个适配器含 目标工具、允许入口、副作用核实结论、级别与范围声明、未验证面。
2. **`baseline_recipe.json` — 可复现配方**：环境身份（主机、OS、python3、仓库 HEAD、工作树状态）、案例身份（T1 run_id + `incidents.jsonl`/`coverage_matrix.json`/`source_groups.json` 的 git_blob_id）、工具身份（每个被选/被排除工具路径 + git_blob_id + 理由）、评价器身份（T2 评价器与 T2R-01 哈希）、模型身份（NONE，B0 零调用——写明）、逐命令、两次回放方法、允许/禁止动作、复现注意。
3. **`baseline.json` — 旧流程实际能力基线**（工程画像，**不得**写科学结论或历史实验数字）：
   - 挑战集 = T1 v3 run 的 16 例（13 真实 + 2 对照 + 1 未核验；含 `expected_category`/`applicability`/`legal_control_design`/`source_refs`/`artifact_level`）。24/24/24 分层集仅构建计划——**本卡不造数**。
   - 为全部 16 例建立"案例→适用检查"映射表（含映射依据）；仅对可离线、只读、最小复盘的组合构造 fixture；每个 fixture 记录构造依据（source_refs + 缺陷/对照变体如何构成），保证可复核。
   - 逐项结果：`detected` / `missed` / `not_applicable` / `unverified` + **级别 + 范围** + 证据路径 + 两次回放一致性；对照例（CTRL-01/02）用于观察误拦（有误拦如实记录）。
   - 缺环境/数据 → 该组合标 `unverified` + 精确原因；**禁止合成结果冒充正式基线**。
   - 汇总：按工具/按失败族的工程画像（如"工具 X 覆盖 Y/16 例；Z 组合不可离线复盘"）。
4. 标准运行包件：`receipt.json`（输入绑定：卡片 6 输入 + PREFLIGHT + T1/T3/T2 依赖；checks；usage；UNRESOLVED；authorization_ref=owner「继续…你自己设定goal去执行吧」+ R 线 U07=C）、`summary.md`、`artifacts_manifest.json`、`events.jsonl`。
5. **执行记录纪律（复用 T3 纪律，但不得扩展 T3 runner）**：唯一 run_id、写前记录（每次工具调用先落 request 记录再执行）、计数单调、禁覆盖、崩溃保留证据；三轴 DELIVERED/UNREVIEWED/NOT_ENABLED；执行对话 token 不可计量写 UNRESOLVED（不填 0）。
6. **FinQA 专用协议范围保留**：复用 `formal_experiment_preflight.py` 等 FinQA/formal 相关器件时保持其专用资格语义，不泛化、不推广为通用资格。

## 完成前自检（硬性；修到干净再交付）
1. 对全部适用 (工具, 案例) 组合做第二次回放：确定性判定必须与第一次一致；不一致如实记录。
2. 重算所有声明哈希（artifacts_manifest、input_bindings、依赖引用）——仓库内被跟踪文件用 canonical `git rev-parse HEAD:<path>`（只读）；run 内新文件用 sha256 实算。
3. 逐条映射卡 §6：A1（baseline 与模型/环境/案例/评价器身份齐全）、A2（同输入确定性判定一致；每一 PASS 带级别和范围）、A3（无旧实验输出、无网络、无现役 Loop B 执行）、A-common。
4. 写入边界：`git status --porcelain` 只出现 `runs/T4/<run_id>/`（外加既有 logs 脏件）；越界即回退并记录。
5. 自检结果写入 receipt.self_check 与 summary；发现并修复的问题如实登记（修复前后对照）。

## 停止条件
输入漂移、权限不明、需越界访问、需联网/模型/生产/数据库、需运行 daemon（含 Loop B）、预算不可计 → STOPPED：保留证据、如实报告、不扩范围。不得进入 T5。

## 交付回复（简短）
run 目录绝对路径；self_check 结论（A1/A2/A3/A-common）；案例→检查映射计数与检出/未检出/不适用/未验证统计；实际检查计数；未验证面与 UNRESOLVED；阻断（若有）。
