# Loop A 任务：T5 v2 返工 —— 按 T5R-01 修复 2 个 blocking + 折叠 6 个 advisory（执行 + 完成前自检；第二轮独立评审）

你是 Loop A（GB10 上的 Codex CLI 执行层）。T5 v1 run（`runs/T5/20261014T195445Z_60c8e213`）已被独立评审 **T5R-01 判定 REJECTED（2 blocking / 6 advisory）**；本任务 = T5 v2 全量返工。先通读 `reviews/T5R-01/REVIEW.md`、`reviews/T5R-01/ACCEPTANCE_PROPOSAL.json`、`reviews/T5R-01/review_receipt.json`。任务卡 `cards/T5.md` 不变；除下述修复外，v1 已通过的面（接口闭合、15/15 负例码、四类分离、frozen_protections、T4 消费约束、TASK_PROMPT 逐字性）全部保留。

## 背景
- R 线获授权（至 M1）；协议 FROZEN（`282f5213…`）；B0：零模型/网络/远程/生产/数据库/训练调用；零自动重试。
- T4 消费约束：读 T4 baseline 只准用**真案级字段 `baseline.cases[]`**（v1 措辞误指 `summary.case_results` 派生字段——本次修正措辞，代码已合规保持）。
- 收据守卫（G1）：包内每个 `.md` 逐个 `python3 scripts/graph/hooks/summary_recompute_guard.py check <path>` 必须 rc=0；失配变体运行时派生、不落盘 .md。

## BLOCKING-1 修复 —— 交付态必须自证「17/17」（执行位是合同要素）
事实（T5R-01）：`recipe_fixtures/dispatch/watcher.sh` 提交时丢失执行位（mode 100644）；目标工具 `dispatch_precheck.sh` 强制 F-0907-1（watcher 必须有执行位）→ 交付态实测 16/17（正例 P01 失败）。执行位**不得绕过**（它是该场景目标工具的合同要素），必须**交付**。要求：
1. 清点所有"合同要求可执行"的文件（至少 `recipe_fixtures/dispatch/watcher.sh`；审查全部 .sh/.py 的调用形态与目标工具合同），确保本地 `test -x` 通过；
2. `artifacts_manifest.json` 每条记录 `mode`（如 "100755"/"100644"），并含 `required_executables` 列表；
3. **fresh-delivery 模拟自检**：把包复制到 scratch → 对副本 `chmod -x` 全部 → 按 manifest 记录恢复模式（模拟新 checkout）→ 跑全量探针矩阵 → 必须逐项与预期一致（含 P01 通过）；再在当前树复核一遍；两轮都记录；
4. receipt/summary 的头号主张只许写"交付字节+交付模式"可复现的计数；修复后矩阵如实更新（新总例数含下面新增探针）；
5. 提交侧说明：执行者不做 git；提交者将以 `git update-index --chmod=+x` 落实模式，v2 须在 receipt 注明"模式由提交者应用、fresh-delivery 模拟已按同语义自证"。

## BLOCKING-2 修复 —— 伪造摘要保护（Loop D 裁决，按卡 §7）
事实（T5R-01）：X06「自洽伪造摘要」（text 与 hash 同时伪造）被 ACCEPT 并执行目标操作，击穿卡 §6 A2。
**Loop D 裁决（形态=外部 pin；满足 T5R-01 的窄/宽两种读法）**：摘要接受必须绑定"生产者控制之外的身份来源"：
1. 调用方在 `caller_context` 中提供**期望 pin**（如 `expected_artifact_sha256`，来源为调用方自己的可信记录：manifest/注册表/上游收据链）；
2. 校验器要求：声明哈希 == 实测哈希 == pin；**无 pin 或 pin 不符 → fail-closed 拒绝**（新增明确 fail_closed_code，如 `FC_ARTIFACT_NOT_PINNED` / `FC_PIN_MISMATCH`）；
3. 新增对照：X06a 自洽伪造-无 pin → 拒；X06b 自洽伪造-错 pin → 拒；**X06c 正确 pin → 接受（新正例）**；保留原 E06（摘要与工件失配）负例；
4. 在 caller_contract/error_surface/README 写明 pin 语义与**威胁边界**（校验器不防"调用方自己递假 pin"——边界须显式声明）。

## ADVISORY 折叠（全部 6 条）
- ADV-1：manifest 记 mode（已含于 BLOCKING-1 修复）。
- ADV-2：新增有界 `max_tick_age_minutes` 正例（运行时生成 observed_at 于界内），不得只剩单点 0。
- ADV-3：`caller_validator.execute_operation` 显式固定 `cwd`（或声明并强制所需 cwd），保证 T4 适配器 `git rev-parse --show-toplevel` 语义稳定。
- ADV-4：修复记录的"叙述性证据"改为可复核工件，或如实标注为仅叙述。
- ADV-5：措辞修正（同背景节）。
- ADV-6：写入边界/自检扩展到 **gitignored 路径**（对 run 目录与仓库窗口做含忽略件的 mtime 扫描），使"无越界写入"声明不盲。

## 其它要求
- **全量重建**：新 run_id；`receipt.json` 含 `supersedes`（v1 run id + T5R-01 REJECTED 原因 + 本修复清单）；
- 标准包件：recipe_interfaces.json、registered_operations.json、recipe_fixtures/、receipt.json、summary.md、artifacts_manifest.json、events.jsonl、TASK_PROMPT.md（**逐字复制本任务书**）；
- 写入所有权：仅 `runs/T5/<v2 run_id>/`；不做 git；不改其他文件；
- 完成前自检：A1/A2/A3/A-common 逐条（含级别+范围、不得裸 PASS）+ G1 + fresh-delivery 模拟 + 两轮探针一致性；修复记录如实登记；
- 停止条件同 v1；不得进入 T6。

## 交付回复（简短）
v2 run 目录绝对路径；BLOCKING-1/2 修复证据摘要（模式矩阵、fresh-delivery 模拟、pin 探针结果）；advisory 折叠对照表；self_check 结论；未验证面与 UNRESOLVED；阻断（若有）。
