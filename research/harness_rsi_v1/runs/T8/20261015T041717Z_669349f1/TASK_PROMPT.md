# Loop A 任务：T8 受控影子与精确启用 —— R 单方向（边界执行；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。按 `research/harness_rsi_v1/cards/T8.md` 执行；先读 T7/T7R-01、T6/T6R-01、T5 v3 与卡全文。**本轮以两个 owner 门为诚实边界**：
- (i) 卡 A1 要求"三个**真实新任务**证据"，预算注记写明"三个**新获批任务**的窗口（时间 UNRESOLVED）"；当前授权范围内不存在三个新获批任务的窗口；
- (ii) §7"用户决定启用和精确分发目标"。
因此本轮执行到合法边界：交付影子框架/计划、身份绑定、回滚演练、release_proposal（**仅建议**）、以及**如实标注的 NOT_SATISFIED 影子状态**；**不得伪造任务/证据、不得启用或分发、不得改 skills/全局配置**。

## 范围
1. **被影子版本**（"先承接原 R 版本"）= 已验收 R 版本：T5 v3 @115f396（recipes/caller_validator）+ T6 @ef5e84e（archive）+ T7 @0579b64（验收/回滚记录）；以内容哈希组绑定身份（canonical git blob/commit）；核对"候选哈希与验收一致"（A2）。
2. **`shadow_comparison.json`**：影子协议与计划——定义"三新任务同资料旧新比较"所需的窗口要素（每任务需有的资料、权限/预算窗口、记录字段、严重回归停用规则、回滚保持）；如实记 `shadow_status=NOT_SATISFIED_NO_THREE_TASK_WINDOWS`（附授权范围核查证据与精确缺口清单）；逐任务结果表**留空并注明未执行**（不得填造）；写明技术前提（任务如何接入影子记录、记录什么）。
3. **`release_proposal.json`**：**仅建议**——如"R 版本具备进入影子条件；建议在获得三个新获批任务窗口后启动影子；启用/分发属 user 裁决（§7）；本包不启用、不分发"。含候选身份、回滚计划、风险与未验证面。
4. **`rollback_receipt.json`**：回滚演练（模拟 shadow 态→恢复 base 态；哈希一致、旧证据零改）。
5. 标准包件：receipt/summary/artifacts_manifest/events/TASK_PROMPT（逐字）；三轴 DELIVERED / UNREVIEWED / NOT_ENABLED。
6. **预算 SHADOW（6 便宜 / 2 强）**：不激活即不调用；记 0/6、0/2（窗口缺席时不得调用任何模型）。网络/远程/生产/数据库/训练/daemon/Loop B 均 0；自动重试 0。
7. 自检：A1（如实"未满足：三任务证据缺"）、A2（身份绑定；**安装态/装载态不由仓库存在推断**——明示未安装、未装载）、A3（旧实验零改、无权限外请求）、A-common；G1（每个 .md rc=0）；写入边界含 gitignore 视野；修复记录如实；模式声明与交付一致（提交侧落实 755 全集）。
8. 停止条件同前；不得进入 T9；停在 owner 门。

## 交付回复（简短）
run 目录绝对路径；shadow 状态与依据；身份绑定与 rollback 结论；release_proposal 摘要（仅建议）；usage 0/6、0/2；self_check（A1/A2/A3/A-common+G1）；未验证面与 UNRESOLVED；阻断/owner 门清单。
