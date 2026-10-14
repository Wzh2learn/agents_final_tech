# Harness RSI v2 规划包

状态：SPECIFICATION_ONLY；所有执行权限关闭。T−1 READY仅供文档核对；T0–T17 DRAFT。没有生成案例、候选、实验或验收签名。

## 导航

- [完整总体规划](MASTER_PLAN.md)：R 可靠性、C 科研能力、S skill 优化、两轮内容与物化澄清。
- [修订记录](REVISION_LOG.md)、[两轮原文身份](sources/provenance.json)。
- [评价协议](contracts/protocol.json)、[权威快照](contracts/authority_map.json)、[执行纪律](contracts/execution_policy.md)、[预算](contracts/budget_profiles.json)。
- [任务矩阵](cards/task_matrix.json)、[T−1 复核卡](cards/T-1.md)、[卡模板](cards/CARD_TEMPLATE.md)。
- [文件清单](FILES.md)、[机器清单](FILE_MANIFEST.json)、[待解决项](UNRESOLVED.md)。
- [可复制的新对话 prompt](EXECUTION_PROMPT.md)。

## 当前可做的第一步

本次用户已要求创建规划包；主体物化已经执行，但未伪造T−1独立验收。下一对话用T−1只读核对既有规格并写新run包。不要重复创建sources或自动运行T0。

T0–T17需后续精确授权、所需协议冻结、真实依赖验收和输入绑定。未知填写UNRESOLVED；READY不是执行授权。可验证的本地文件SHA-256只是原文字节/权威快照身份，不是科学证据或签署。

## 文件流

任务卡与绑定输入 → runs中的独立原始运行包 → reviews独立评审 → 追加验收事件 → 收口者生成state视图。执行者不自行写ACCEPTED，不直接改共享state/registry。当前空JSONL表示尚无事件，不表示通过。

## 永久边界

D:/AIRcommend/JinRongAgents/agents_final_tech/skills 仍是正式技能source of truth；本目录只放规格与未来候选快照。现役项目STATE/THREADS仍是全项目权威。冻结实验、论文结论、停止状态、生产服务与凭证保持保护；本地文档检查不代表GB10运行验证。
