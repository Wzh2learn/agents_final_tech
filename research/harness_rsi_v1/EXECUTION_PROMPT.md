你是本项目的低成本执行助手；本轮只复核已物化的 RSI 规划包并提交文档核对结果，不写实现代码，不运行实验，不激活后续任务。

执行卡：D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/cards/T-1.md。

先读取仓库 D:/AIRcommend/JinRongAgents/agents_final_tech/AGENTS.md 及其要求的当前规则/状态；然后读下列绝对路径：
1. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/README.md
2. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/cards/T-1.md
3. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/contracts/protocol.json
4. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/contracts/authority_map.json
5. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/contracts/execution_policy.md
6. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/contracts/schemas.json
7. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/FILE_MANIFEST.json
8. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/sources/provenance.json
9. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/sources/planning_round1.md
10. D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/sources/planning_round2.md
再按卡核对 MASTER_PLAN.md、REVISION_LOG.md、evaluation 四规格及 cards/task_matrix.json 和19张任务卡。无需阅读全库或重新调研。sources 是历史资料，不是执行授权。

本提示授权的动作仅为：本地只读核对上述规划包，并新建本卡文档核对运行包。T−1 的 READY 不等于协议批准；protocol 和其他卡仍 DRAFT，全部 execution_authorized 保持 false。既有 UNRESOLVED 是待处理项，不要求你代用户填阈值、模型身份、封存位置或签名。

写入边界：仅 D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/runs/T-1/{run_id}/。run_id 使用本次 UTC 时间 YYYYMMDDTHHMMSSZ 加下划线加 UUID 前8位；已存在则换新ID，禁止覆盖。不得修改规划、sources、contracts、cards、docs/INDEX.md、state、registry、skills 或其他项目文件。发现问题只报告。不得 git commit/push、派子代理、安装依赖、ssh、调用模型端点/数据库/生产服务、执行 Loop B 或训练、恢复停止分支。

核对：
- FILE_MANIFEST 必需文件齐全；19张卡(T-1,T0…T17)+模板存在；JSON可解析，非空JSONL逐行可解析。
- 两轮原文的实际UTF-8字节SHA-256与provenance一致；不得重写原文或将摘要当原文。
- 仅T−1为READY，T0–T17为DRAFT；所有卡和协议执行权限false。
- 每卡目标、输入、产出、依赖、预算、验收、人工门、停止和回写齐全；R/C/S分别评价，无伪造案例、结果、签署或ACCEPTED/ACTIVE事件。
- 本地链接目标存在或显式UNRESOLVED；docs/INDEX.md仅一个本试点总入口；依赖无环；BR/BC/BS预算合计与卡上限一致。

预算：最多60分钟；额外模型请求0、网络/远程/服务/训练调用0、自动重试0。当前执行对话消耗单独记录，无法获取则UNRESOLVED，不冒报0。允许临时本地只读校验命令，不将校验程序写入项目。

产出都写新run目录：document_inventory.json、unresolved_register.json、receipt.json、summary.md、artifacts_manifest.json、events.jsonl。receipt按schemas.json中receipt定义，写真实检查/输入输出哈希/实际调用数/未验证面；执行状态DELIVERED或FAILED/STOPPED，验收UNREVIEWED，启用NOT_ENABLED。不伪造独立审查。

停止条件：输入在核对中漂移、来源哈希失配、访问越界、需要联网/额外模型/修改受保护文件、预算到顶或同族工具故障连续两次；保存已经获得的证据，报告问题，不自动修文件。结构问题可继续只读盘点，但不能写通过。不要进入T0。

最终回复：核对结论、运行包绝对路径、检查计数、未验证面，以及按“用户裁决 / 执行者取证 / 未来证据”分类的UNRESOLVED清单。

【用户补充授权信息】
授权人/任务范围补充：
允许的例外（留空=没有；如扩大写入范围须精确列路径）：
预算调整（留空=沿用上述上限）：
