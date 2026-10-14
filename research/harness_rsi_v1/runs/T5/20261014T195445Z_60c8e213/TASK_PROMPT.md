# Loop A 任务：T5 R 两个对象接口（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T5.md` 执行；卡内 `D:/AIRcommend/JinRongAgents/agents_final_tech/...` 路径在本机等价于 `~/wzh/projects/agents_final_tech/...`（仓库根）。**完成后必须自检并修到干净再交付**（后续仅 1 次 Loop C 评审名额）。

## 背景与依赖（先读，只读）
- `AGENTS.md`；`cards/T5.md`；`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`；`evaluation/reliability_spec.md`；`docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`（级别定义，任何 PASS 必须带级别+范围）。
- 协议 FROZEN（`282f5213…`）。已验收依赖：T4 v2 run `runs/T4/20261014T184810Z_c9dcfe0e/`（评审 `reviews/T4R-01/`，ACCEPTED；其中含只读适配器 adapters/ 与 baseline）；T3 run `runs/T3/20261014T161814Z_245b86ab/`（T3R-01）与 T2 评价器（`runs/T2/20261014T145327Z_9a02a34a/`）作为执行与评测底座身份绑定。
- **T4 教训（必须继承）**：
  (1) 仓库内落盘的 .md 收据夹具必须全部通过仓库收据守卫（`scripts/graph/hooks/summary_recompute_guard.py`）；失配（坏摘要）变体必须"运行时派生"、不得持久化为 .md（参照 `tests/test_guard_sentinels.py` 头部 Decision 34）。本卡自检 G1 与 T4 v2 相同：包内每个 .md 逐个 check 必须 rc=0。
  (2) T4R-01 A1 消费约束：读取 T4 baseline 时**以 case-level `case_results` 为准**；不得直接信任 `combination_results`/`failure_family_profiles` 派生汇总字段（如需要，从 case-level 重算）。
- 本卡预算 B0：**零** 模型/网络/远程/生产/数据库/训练调用；**本卡不请求模型提案**；零自动重试。

## 写入所有权（硬）
- 只允许在 `research/harness_rsi_v1/runs/T5/<run_id>/` 下创建产物（run_id = 执行时 UTC `YYYYMMDDTHHMMSSZ` + `_` + UUID 前 8 位；已存在换新 ID；不覆盖）。不改任何其他文件；不做 git commit/push。
- 第一个动作：把本任务书**逐字**复制到 run 目录 `TASK_PROMPT.md`（含空行原文；不做改写），并在 receipt 记录其 sha256。
- 所有 fixture、工具运行现场只准写本 run 目录内；不得触碰真实仓库文件、旧实验/历史 run、生产与 daemon。

## 任务范围（bounded v1）
1. **两个 recipe 接口**（`recipe_interfaces.json`）：预检（precheck）与证据交付（evidence-delivery）各一个 recipe 接口；**一个 recipe 只负责一个对象**：
   - 每个 recipe = {recipe_id、单一对象声明、operations（仅引用已登记操作 + 受限参数）、frozen_protections（不得减少的必需保护清单）、caller_contract（输入/输出/错误面）、delivery_fields（分四类：资格/审计/执行/科学结论，字段不得混合）、probes（引用本包 recipe_fixtures/）}。
   - `frozen_protections` 至少覆盖 reliability_spec 的硬门语义（严重缺陷漏检=0、合法案例误拦不高于基线、证据完整率、主张越级=0、原始记录完整性、预算完整性、成本记录）——以引用+声明方式冻结，不实现评分。
   - 交付字段四类分离：资格（qualification）、审计（audit）、执行（execution）、科学结论（scientific）各自独立字段/状态；不得出现单一"总体 PASS"。
2. **已登记操作注册表**（`registered_operations.json`）：封闭词表；每项 = {op_id、目标（优先复用 T4 adapters 的离线只读入口或等价既有工具，注明路径+git_blob_id）、固定语义、允许参数（有界枚举/范围）、**明确禁止任意 shell / 自由文本命令/任意路径**、副作用类别（只读）、级别与范围声明}。recipe 只能引用注册表条目——引用未登记操作或注入 shell 字符串必须在调用方校验层被拒。
3. **调用边界探针**（`recipe_fixtures/`）：探针定义**从真实调用方契约出发**（该 recipe 在实际流水线中的调用形态，例如"Loop D 对 run 包发起预检"、"交付时对 receipt/manifest 做投递校验"），不得由实现自己的假设定义（避免实现与测试同错）；在接口文件或 README 写明契约来源。
   - 必备负例对照：**坏摘要**（伪造/失配收据——运行时派生，不落盘失配 .md）、**错哈希**、**漏字段**、未登记操作引用、参数越界/类型错误；必备正例：合法调用可被接受。
   - 调用方可验证性：接口错误必须由**调用方侧校验**发现（探针从调用方执行，记录拒绝证据）。
4. 标准运行包件：`receipt.json`（输入绑定：卡片 6 输入 + T4 v2/T4R-01 依赖；checks；usage；UNRESOLVED；authorization_ref=owner「继续…你自己设定goal去执行吧」+ R 线 U07=C）、`summary.md`、`artifacts_manifest.json`、`events.jsonl`。
5. **执行记录纪律（复用 T3 纪律，不扩展 T3 runner）**：唯一 run_id、写前记录、计数单调、禁覆盖、崩溃保留证据；三轴 DELIVERED/UNREVIEWED/NOT_ENABLED；执行对话 token UNRESOLVED（不填 0）。

## 完成前自检（硬性；修到干净再交付）
1. 逐条映射卡 §6：A1（一个 recipe 只负责一个对象；不能执行任意 shell——用负例证明未登记操作/shell 注入被拒）、A2（接口错误可被调用方验证发现；伪造摘要不能通过）、A3（不修改 C/S 评分、旧实验组件或冻结件——写入边界+哈希证据）、A-common。
2. **G1（收据守卫合规）**：包内每个 `.md` 逐个运行 `python3 scripts/graph/hooks/summary_recompute_guard.py check <path>`，全部 rc=0；含幂等派生对照（派生坏摘要被守卫 rc≠0）。
3. 重算所有声明哈希（tracked 文件用 canonical `git rev-parse HEAD:<path>`；run 内新文件 sha256）。
4. 写入边界：`git status --porcelain` 只出现 `runs/T5/<run_id>/`（外加既有 logs 脏件与未提交的 T4 v1 目录）；越界即回退并记录。
5. 自检结果写入 receipt.self_check 与 summary；修复记录如实登记（修复前后对照）。

## 停止条件
输入漂移、权限不明、需越界访问、需联网/模型/生产/数据库、需运行 daemon（含 Loop B）、预算不可计 → STOPPED：保留证据、如实报告、不扩范围。不得进入 T6。

## 交付回复（简短）
run 目录绝对路径；self_check 结论（A1/A2/A3/A-common + G1）；两个 recipe 与注册表条目计数；探针矩阵（正/负例结果计数）；实际检查计数；未验证面与 UNRESOLVED；阻断（若有）。
