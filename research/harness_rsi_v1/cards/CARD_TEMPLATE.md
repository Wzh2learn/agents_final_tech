# 独立任务卡模板

状态 DRAFT；execution_authorized=false。必填：身份、目标/排除、输入绝对路径与哈希、依赖验收、写入所有权、步骤、精确产物、自动断言、人工门、预算、停止/回滚、结果回写。

卡内JSON为机器元信息；已知内容哈希可实算，未来绑定填UNRESOLVED。READY不代表授权。卡无输入、依赖或预算时不得激活。

运行目录规则：D:/AIRcommend/JinRongAgents/agents_final_tech/research/harness_rsi_v1/runs/{task_id}/{UTC_YYYYMMDDTHHMMSSZ_uuid8}。UTC时间与随机UUID前8位组成新ID；存在则换ID。为每个具体产物展开绝对路径，禁止latest或复用旧目录。

四件基本回写：receipt.json、summary.md、artifacts_manifest.json、events.jsonl。receipt使用contracts/schemas.json的receipt定义；额外对话消耗未知写UNRESOLVED；结果只写DELIVERED/FAILED/STOPPED + UNREVIEWED + NOT_ENABLED。

独立评审在reviews目录，收口者之后生成状态。执行者不能直接改registry/state或自己的验收状态。
