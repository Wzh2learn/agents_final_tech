# G3 增量证据选择性补查探针 v1

日期：2026-10-23，Asia/Shanghai  
状态：`DEV_PROBE_COMPLETE_CANDIDATE_RULE_NEGATIVE_MODEL_POLICY_UNEVALUATED`

## 1. 独立问题与 G2 边界

本探针研究：BM25 top-3 已经到达后，何时应保留现有证据，何时值得继续检查排名
4-5 的两个候选 session，以补到旧状态和新状态两端。

它与 G2 的状态到行动迁移不同：模型只输出 `KEEP/EXPAND`，不回答用户任务，也不把
恢复状态映射为行动。主结果因此只测证据获取，不测行动正确性。当前判断是
`DO_NOT_MERGE_WITH_G2`；若未来 G2 端到端流程纳入 retrieval，也应把本阶段单独计分。

## 2. 冻结协议

- 数据：公开 STALE `T1_T2_400_FULL.json`，SHA-256
  `5f3ec375179e20e2e94469e018189188f34e2e7e5f21cbecbd99fcfa648c1876`。
- 查询：`dim1_query`。
- 初始证据：BM25 top-3；增量证据：BM25 ranks 4-5。
- 模型可见：query、top-3 session 原文、session 可见标签和时间。
- 事后参考：隐藏 `relevant_session_index`，只用于评价是否新增 old/new relevant session。
- 禁止 actor 字段：`M_old`、`M_new`、`explanation`、`relevant_session_index`。
- 模型：GB10 `Qwen3.6-35B-A3B-Q4_K_M.gguf`，temperature 0，单并发，零 retry，
  最多 8 accounting calls。
- 8 个模型 UID 在调用前按“排除既有 28 UID 后，T1/T2 各取 UID 升序前 4”冻结。
  该样本隐藏评价构成为 3 个 top-5 有用扩展、5 个无增益扩展；该事实只做事后评价。

## 3. 强基线、候选与 oracle

| 策略 | 身份 | 动作 |
|---|---|---|
| `keep_top3` | 强成本下界 | 全部 KEEP |
| `always_expand_top5` | 强覆盖基线 | 全部 EXPAND |
| `visible_gap_rule` | 透明候选 | query coverage、past/update cue、rank-3/rank-1 score 决定 |
| `model_selective_expansion` | 模型候选 | top-3 后输出 KEEP/EXPAND |
| `oracle_gain_rule` | 隐藏诊断 | 仅在 top-5 确实新增 relevant session 时 EXPAND |

oracle 不是可部署基线，只界定可利用空间。

## 4. 离线真实数据结果

400 个 UID 的确定性 replay：

| 策略 | EXPAND | BOTH old/new | useful expand | no-gain expand | missed gain | mean context chars |
|---|---:|---:|---:|---:|---:|---:|
| `keep_top3` | 0 | 144/400 (0.3600) | 0 | 0 | 43 | 34,712.86 |
| `always_expand_top5` | 400 | 187/400 (0.4675) | 43 | 357 | 0 | 64,338.07 |
| `visible_gap_rule` | 9 | 145/400 (0.3625) | 1 | 8 | 42 | 35,365.92 |
| `oracle_gain_rule` | 43 | 187/400 (0.4675) | 43 | 0 | 0 | 37,292.01 |

解释：

1. 增量证据问题真实存在：43/400 的 ranks 4-5 能新增 relevant session，且都补成
   old/new 两端。
2. always-expand 可以达到 187/400，但 357 次扩展没有新增 relevant session，平均上下文
   比 top-3 增加 29,625.21 chars。
3. oracle-selective 以 43 次扩展达到相同 187/400，平均上下文仅比 top-3 增加
   2,579.15 chars；这证明选择空间有成本价值，但 oracle 不可部署。
4. `visible_gap_rule` 只发现 1/43 useful expansion，扩展 precision 为 1/9，recall 为
   1/43。它只比 keep 多 1 个 BOTH 覆盖，不能支持词面 cue 是充分选择机制。

确定性 double-run 与首跑字节一致，SHA-256 均为
`07486af674c774841e3bd62a7bb588087d1ab02310fadc3a2b95dcb0100a18c5`。

## 5. 模型开发调用与失败

预算内实际发生 2/8 calls，零 retry，随后按冻结 stop rule 停止：

- call 1：15,109 prompt + 512 completion = 15,621 tokens。错误使用顶层
  `enable_thinking`，输出进入 reasoning，`message.content` 为空；早期 runner 又在保存
  raw 前解析失败。没有重发。精确 token 从 llama-server task `2810516` 恢复。
- call 2：8,490 prompt + 128 completion = 8,618 tokens。已改用
  `chat_template_kwargs.enable_thinking=false`，但 128 token 不足，`finish_reason=length`；
  输出把 `missing_information` 写成 string，JSON 截断，严格合同判为 INVALID。

两次合计 24,239 tokens、23,599 prompt、640 completion、2 physical HTTP、0 retry。
raw 请求/响应中 call 2 完整保留；call 1 response hash 无法在丢失 raw 后重建。

这两个失败是接口/预算失败，不是“模型无法判断补查”的科学证据。由于协议规定严格解析
失败后停止，剩余 6 calls 未使用。`model_selective_expansion` 因此为
`UNEVALUATED_NO_VALID_DECISION`，不能计为 0/8 或负准确率。

## 6. 失败解释与候选裁决

- `visible_gap_rule`：`STOP_CURRENT_RULE`。词面 past/update cue 与 BM25 score tail
  不能识别绝大多数 useful expansion。
- 模型策略：`INTERFACE_FAILURE_NOT_SCIENTIFIC_FAILURE`。下一版必须在独立新协议中
  使用单字段 action 或更高且预冻结的输出预算；不得把本次截断输出补解析成决策。
- 研究问题：`KEEP_WITH_HEADROOM`。43 个真实 useful expansion 和 oracle 成本差说明
  选择性补查仍有可识别空间。
- 学习主张：`NOT_ESTABLISHED`。本轮没有训练、参数学习、loss 或可泛化选择器。

## 7. 与 G2 的合并判断

`DO_NOT_MERGE_AT_CURRENT_STAGE`。

- G2 输入是已恢复状态/证据，输出是事实或行动；
- G3 输入是 top-3 证据，输出是是否继续获取证据；
- G3 成本是新增检索上下文和查询次数，G2 成本是回答/行动失败风险。

只有在未来端到端实验把 retrieval、state recovery 和 action 三层分别计分时，二者才进入
同一系统分析；不能把 G3 的补查收益写成 G2 行动收益。

## 8. 下一信息量最高的动作

在不复用本次失败 prompt 的前提下，先用零模型可见特征做 UID-grouped 交叉验证，判断
43 个 useful expansion 是否能被 score、query coverage、时间跨度和证据 anchor 不确定性
稳定预测。只有可见特征显著超过 `visible_gap_rule` 并接近 oracle 的成本覆盖率，才值得用
剩余模型预算测试简化 `KEEP/EXPAND` 接口；否则停止该候选并保留为边界材料。

## 9. 证据绑定

- 协议：`G3_PROTOCOL_V1.json`，SHA-256
  `41cc670db422a5dc345301a54fdb6cab7939dbbf78eb7daf0a8d4da88f0ce84d`。
- 离线结果：`G3_OFFLINE_RESULTS_V1.json`，SHA-256
  `07486af674c774841e3bd62a7bb588087d1ab02310fadc3a2b95dcb0100a18c5`。
- 模型结果：`G3_INCREMENTAL_EVIDENCE_RESULTS_V1.json`，SHA-256
  `f694d3b4a2df7e4635cde8c2d280a62c20c8275878c39ecac8e666146edc3b0c`。
- 模型 receipt：`G3_MODEL_RECEIPT_V1.json`，SHA-256
  `0450203b131455aa71d746be93e03bc18e4b1619529ca960433a28398f5fffae`。
- 首次失败 receipt：`G3_MODEL_FAILURE_RECEIPT_V1.json`，SHA-256
  `011457710bc3f003a7890829ecb528f9a2de8f1faea8a65e7d9860daf7715408`。

本轮所有写入均位于 `revision_v5/G3_*`；未修改 G2、memory、研究入口或既有结果。
