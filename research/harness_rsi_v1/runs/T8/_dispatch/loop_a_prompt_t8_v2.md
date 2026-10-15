# Loop A 任务：T8 v2 受控影子执行 —— 三个真实任务窗口（执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T8.md` 执行。Owner 已授权三个真实任务窗口（authorization_ref=owner「你找三个真实的我们项目的任务去跑呗」2026-10-15）。

## 背景
- R 线 T-1→T8 已全部验收；T7 结论 NO_PROMOTION（候选不可执行）；T8 承接原 R 版本（T5 v3 @115f396）。
- 影子版本 = T5 v3 recipes（precheck + evidence-delivery）；基线版本 = 无 recipe 的现有检查流程。
- 每个任务：同一冻结资料集，跑旧流程（现有检查）和新流程（T5 v3 recipe），记录对比。

## 三个任务窗口（owner 已授权）

### 窗口 1：TAT-QA 许可记录完整性验证
- 材料：`docs/datasets/tatqa_licence_record_v1.md`（冻结 SHA-256 在执行时计算并记录）
- 旧流程：直接读文件，人工核对关键字段（license、permitted uses、covered artifacts）
- 新流程：通过 T5 v3 precheck recipe 对输入做合同校验（哈希绑定、字段齐全性、路径合法性）
- 产出：验证收据 + 对比记录

### 窗口 2：TAT-QA WP-1 实施合同哈希校验
- 材料：`research/tatqa_wp0_2026/wp1/implementation_contract.md` + `implementation_contract.sha256`（冻结 SHA-256 在执行时计算并记录）
- 旧流程：sha256sum 对照 .sha256 文件
- 新流程：通过 T5 v3 evidence-delivery recipe 对工件做哈希绑定验证（声明==实测==外部 pin）
- 产出：验证收据 + 对比记录

### 窗口 3：研究底座状态一致性审计
- 材料：`research/harness_rsi_v1/state/current.json` + `registry/task_events.jsonl` + `runs/` 目录结构（冻结快照 SHA-256 在执行时计算并记录）
- 旧流程：逐项手动核对 accepted_tasks 与实际 run 目录
- 新流程：通过 T5 v3 recipe 接口做结构化验证（字段齐全、路径合法、身份绑定）
- 产出：审计收据 + 对比记录

## 影子协议要求（每个窗口）
- 材料冻结：记录每个输入的 SHA-256 + 字节数 + 冻结时间
- 环境身份：主机、OS、Python 版本、仓库 HEAD
- 权限窗：只读（两个流程均不修改被检查材料）
- 预算窗：SHADOW profile，0 额外模型请求，0 网络
- 顺序：先旧后新（记录顺序，声明 order 为限制）
- 停止规则：任何严重回归 → 停用 candidate 并回滚
- 回滚：材料只读，无需回滚；记录 rollback state = PASS_READ_ONLY

## 产出
- `shadow_comparison.json`：三个窗口的完整对比记录（含所有协议要求字段）
- `release_proposal.json`：基于影子结果的启用/拒绝建议
- `rollback_receipt.json`：回滚状态
- 标准包件：receipt/summary/artifacts_manifest/events/TASK_PROMPT（逐字）
- 自检：A1（三个真实任务证据齐全）、A2（候选哈希与验收一致）、A3（旧实验零改、无权限外请求）、A-common、G1

## 硬性约束
- 只写 `runs/T8/<v2 run_id>/`；不改被检查材料；零模型调用；零网络；G1 守卫全绿。
- 基线版本 = "无 recipe 的现有检查"（具体描述用了什么命令/方法）；候选版本 = "T5 v3 recipe 调用"。
- 停止条件同前。不得进入 T9。

## 交付回复（简短）
run 目录绝对路径；三个窗口的对比结论（旧 vs 新，各自检出/漏检了什么）；shadow_status；release_proposal 摘要；self_check；usage（模型 0）；未验证面与 UNRESOLVED。
