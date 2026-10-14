# Loop A 任务：T2 独立评价底座（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。本任务按 `research/harness_rsi_v1/cards/T2.md` 执行；卡内 `D:/AIRcommend/JinRongAgents/agents_final_tech/...` 路径在本机等价于 `~/wzh/projects/agents_final_tech/...`（下称仓库根）。**完成后必须自检并修到干净再交付**（本轮预算仅为后续留 1 次 Loop C 评审名额，不做多轮往返）。

## 背景与依赖（先读，只读）
- 依据：`AGENTS.md`；`cards/T2.md`；`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`；`evaluation/{reliability_spec.md,human_review_protocol.md}`。
- 协议已 FROZEN（freeze_sha256 `282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`）；authority_map 已按 canonical blob id 重钉。
- 依赖 T1 已验收：run `runs/T1/20261014T141004Z_2647a7e1/`（16 例：13 真实 + 2 对照 + 1 未核验；6 族；7 组）；独立评审 `reviews/T1I-03/`（ACCEPTED）。把两处路径与哈希绑定进你的 receipt。

## 写入所有权（硬）
- 只允许在 `research/harness_rsi_v1/runs/T2/<run_id>/` 下创建产物（run_id = 执行当时 UTC `YYYYMMDDTHHMMSSZ` + `_` + UUID 前 8 位；已存在则换新 ID，不覆盖）。**不得修改任何其他文件**；不做 git 操作；不改共享状态/注册表/被审材料。
- 第一个动作：把本任务书原文复制到 run 目录为 `TASK_PROMPT.md` 并记录其 sha256（派发溯源）。

## 任务范围（bounded v1，估计 1–2 日工作量中的首个有界切片；不得扩范围）
1. **`evaluator_spec.json`**：R 轴评价器规格。定义：
   - 输入契约：`case_bundle`（你定义 schema：案例种类、失败族、冻结 `expected_category`、被检工件路径+哈希、证据清单、来源；至少覆盖 T1 六族与三类对照）。
   - 输出契约：`decision ∈ {ALLOW_WITHIN_SCOPE, BLOCK, REVIEW_REQUIRED}` + 三维独立状态（执行完整性 / 测量有效性 / 主张边界）+ 理由与 fail-closed 代码；**不得跨方向总分合并**（R/C/S 分开）。
   - 规则：缺字段、哈希绑定不符、空集 → **fail-closed**；评价器**不得读取候选自写的判分代码或标签**；不得读取封存。
2. **`evaluator/`**：可运行实现（Python 3.12，仅标准库；确定性）。
   - `evaluate.py`（CLI：`python3 evaluate.py --case <bundle.json> --out <result.json>`，exit code 语义明确）。
   - `fixtures/`：自含合成夹具（每族至少：1 个应有的 BLOCK 缺陷签名、1 个合法 ALLOW 对照、1 个 fail-closed 例；来源标注为合成挑战，不得冒充真实事故；真实事故引用一律指向 T1 v3 案例）。
   - `README.md`（用法、边界、未验证面）。
3. **`qualification.json`**：资格测试（记录命令与退出码）。
   - 对全部夹具 + T1 的 16 例（以 `case_bundle` 形式引用）跑评价器，记录 expected vs actual。
   - **三个退化策略**（全 BLOCK / 全 ALLOW / 全送审）必须证明**不满足**冻结的推广规则（硬门要求同时具备缺陷检出与合法对照不误拦）。
   - 体现辨别力：缺陷被抓、对照放行、缺字段/错绑定/空集 fail-closed。
4. **`sealed_access_proposal.json`**：封存访问提案（身份模型、访问流程、权限测试证据要求、未决项）。**只写提案**：不实现实际隔离，不声称封存资格通过。
5. 运行包标准件：`receipt.json`（schema=receipt；输入绑定含卡片 7 输入 + T1 两处依赖 + 本任务书；checks；usage —— 本卡额外 cheap 请求上限 0、强评审 1 次**保留给后续 Loop C**，你自身零编排调用；UNRESOLVED；authorization_ref 原文=owner「继续授权，这次让loop a 执行完后自检一下，避免loop c 独立评审次数过多」）、`summary.md`（一页）、`artifacts_manifest.json`（逐产物哈希、不自哈希）、`events.jsonl`（真实事件）。

## 完成前自检（硬性；修到干净再交付）
1. 重跑全部夹具与 `qualification.json` 流程（同命令、记录第二次结果）。
2. 重算所有声明哈希：`artifacts_manifest`、`receipt.input_bindings`、案例/证据引用——对仓库内被跟踪文件用 canonical 口径 `git rev-parse HEAD:<path>`（只读 plumbing）；工作树字节值一律不单独声明；任何失配即修。
3. 逐条映射卡 §6：A1（三退化不可满足推广规则）、A2（缺字段/错绑定/空集明确失败、层级不混用）、A3（候选不可写判分代码与标签取值；封存不可读须有权限测试证据——若未实现则如实写"未实现，提案中列权限测试要求"）、A-common（JSON 可解析、字段齐、路径在 allowlist、哈希实算一致、无越界写入、未知显式列出）。
4. 写入边界：`git status --porcelain` 应只出现 `runs/T2/<run_id>/`（外加既有 logs 台账脏件）；有越界即回退并记录。
5. 自检结果写入 `receipt.json` 的 `checks`/`self_check` 块与 `summary.md`；发现并修复的问题如实登记（修复前后对照）。

## 停止条件
输入漂移、权限不明、需越界访问、需联网/模型/生产/数据库调用、预算不可计 → STOPPED：保存已取得证据，如实报告，不自动扩范围。不得进入 T3。

## 交付回复（简短）
run 目录绝对路径；self_check 结论（逐条 A1–A4/A-common）；实际检查计数；未验证面与 UNRESOLVED；阻断（若有）。