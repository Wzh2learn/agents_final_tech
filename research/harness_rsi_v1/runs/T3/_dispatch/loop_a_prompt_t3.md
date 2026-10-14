# Loop A 任务：T3 可信执行与计数（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T3.md` 执行；卡内 `D:/AIRcommend/JinRongAgents/agents_final_tech/...` 路径在本机等价于 `~/wzh/projects/agents_final_tech/...`（仓库根）。**完成后必须自检并修到干净再交付**（后续仅 1 次 Loop C 评审名额）。

## 背景与依赖（先读，只读）
- `AGENTS.md`；`cards/T3.md`；`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`。
- 协议 FROZEN（`282f5213…`）；T2 已验收：run `runs/T2/20261014T145327Z_9a02a34a/`（评价器与资格），评审 `reviews/T2R-01/`（ACCEPTED）。把两处路径+哈希绑定进 receipt。
- 本卡预算 B0：**零** 编排/网络/远程/生产/数据库/训练调用；不得访问真实模型或生产服务（用模拟接口）。

## 写入所有权（硬）
- 只允许在 `research/harness_rsi_v1/runs/T3/<run_id>/` 下创建产物（run_id = 执行时 UTC `YYYYMMDDTHHMMSSZ` + `_` + UUID 前 8 位；已存在换新 ID；不覆盖）。不改任何其他文件；不做 git 操作。
- 第一个动作：把本任务书原文复制到 run 目录 `TASK_PROMPT.md` 并记录 sha256。
- **隔离边界**：本卡不做 OS 级隔离、不改执行环境；只实现"策略级"权限矩阵 + 拒绝逻辑（卡 §7 的 D 裁决门不触发）。

## 任务范围（bounded v1）
1. **`runner/`**：受限执行器（Python 3.12，仅标准库，确定性；可在任意主机运行，输出标注运行域）：
   - 唯一 run ID：`YYYYMMDDTHHMMSSZ_uuid8`；**重复 ID 拒绝**（已存在目录→拒跑，exit 非零，不覆盖）。
   - **写前请求记录**（persist-before-call）：任何被传输的请求先落 `attempts/<id>/request.json` 再"传输"。
   - 模拟传输接口（mock transport）：由本地 fixture 驱动；失败/超时/手动重试**全部计数**，计数单调只增；**预算上限无旁路**（超限即 fail-closed 且记录）。
   - **崩溃→INCOMPLETE**：模拟中途崩溃时，证据保留、状态记 `INCOMPLETE`（不静默）。
   - **覆盖尝试失败**：对既有 attempt 目录的任何覆盖写必须被拒绝。
   - 分账：`model_extra_requests` 与 `execution_chat_usage` 分开记录；不可计量者 UNRESOLVED（不填 0）。
   - `runner/README.md`（用法/边界/未验证面）+ `fixtures/`（自含模拟用例）。
2. **`permission_matrix.json`**：策略级权限矩阵：允许路径（本 run 目录 allowlist）、被拒路径（其他一律拒）、网络=拒、封存=拒、生产/DB=拒；每条含检查方式与拒绝证据格式。标注"策略级，非 OS 沙箱；实际隔离未实现/未声称"。
3. **`runner_qualification.json`**：资格测试（命令+退出码+结果）：重复 ID 拒绝；覆盖尝试失败；崩溃证据保留 + INCOMPLETE；预算超限 fail-closed 且无旁路；计数单调；非法路径/网络/封存访问被拒；分账字段分离。**scope 标注 `LOCAL_DEV_HOST`（本机开发资格，不构成正式运行面绑定、不代表生产/训练执行；GB10 权威绑定留待后续）。**
4. 标准运行包件：receipt.json（输入绑定：卡片 5 输入 + T2 两处依赖 + TASK_PROMPT；checks；usage；UNRESOLVED；authorization_ref=owner「继续…你自己设定goal去执行吧」+ R 线 U07=C）、summary.md、artifacts_manifest.json、events.jsonl。

## 完成前自检（硬性；修到干净再交付）
1. 重跑全部资格用例（同命令第二次，记录两轮结果一致）。
2. 重算所有声明哈希（artifacts_manifest、input_bindings、依赖引用）——仓库内被跟踪文件用 canonical `git rev-parse HEAD:<path>`（只读）；工作树值不单独声明。
3. 逐条映射卡 §6：A1（重复 ID 拒绝、崩溃证据保留、覆盖尝试失败）、A2（预算无旁路、计数单调、非法路径/网络/封存拒绝）、A3（LOCAL 标注）、A-common。
4. 写入边界：`git status --porcelain` 只出现 `runs/T3/<run_id>/`（外加既有 logs 脏件）；越界即回退并记录。
5. 自检结果写入 receipt.self_check 与 summary；发现并修复的问题如实登记（修复前后对照）。

## 停止条件
输入漂移、权限不明、需越界访问、需联网/模型/生产/数据库、预算不可计 → STOPPED：保留证据、如实报告、不扩范围。不得进入 T4。

## 交付回复（简短）
run 目录绝对路径；self_check 结论（A1–A4/A-common）；实际检查计数；未验证面与 UNRESOLVED；阻断（若有）。