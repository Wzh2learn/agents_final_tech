# 任务：M1 用 LLM 为未知表头建议映射（冷启动）

## 背景
北极星之一 = 未知表头冷启动能力。A 扩 schema 后仍有 unmapped 列；甲方 UI 的
"新增字段"本质是人工补映射。本轮把 LLM 角色定位为**给未知表头建议标准字段 / 补
synonym**（不是抽实体），并用 A 的勾稽校验把关建议是否有害。
样本 `~/wzh/m1_samples/`（项目外，不入库，报告脱敏），schema 同目录
`m1_table_schema.json`。:8004 = Qwen3-14B。

## 约束
- 样本不入库、报告脱敏；不下载模型；不改 src/biz/m1_service.py；不 push；不碰
  TAT-DQA / test split。
- :8004 限流：逐个 unmapped 列**串行**调，每次 30s 超时，不并发轰炸。
- 调 Qwen3-14B 必须 `/no_think`（否则 content 空，已有结论）。

## Phase 0 收集 unmapped
重跑 `scripts/m1_statement_parser.py`（或读 A 的结果 json `/tmp/m1_results.json`
若存在），收集每样本 unmapped 源列名 + 该列前 3 个脱敏样本值 + 所属表。去重得
unmapped 列清单（带样本值上下文）。若需，给 parser 加一个 `--dump-unmapped`
只读小开关（不改解析逻辑）。

## Phase 1 LLM 建议
对每个 unmapped 列，prompt（/no_think, temp0, 仅 JSON）：列出标准字段清单 + 现有
synonyms；给该 unmapped 列名 + 样本值；要求输出
`{"suggested_standard_field":"<已有标准字段名 或 NEW>","new_field_label":"<若 NEW>",
"suggested_synonyms":[...],"confidence":0.0-1.0,"reason":"..."}`。

## Phase 2 把关评测
对 confidence>=0.7 的建议，临时并入 schema **副本**（内存/临时文件，不改原 schema），
重跑 parser：
- unmapped 下降量；
- 用 A 的 reconcile 勾稽校验：若采纳后某样本勾稽从 pass 变 fail，或出现
  "明细和≠合计"等新错配 → 判该建议有害，**拒绝**，记拦截原因。
- 采纳的安全建议汇总为"待人工确认的 schema 补丁"贴进报告，**不自动写回原 schema**
  （冷启动建议需人审，对应甲方运营闭环）。

## Phase 3 报告
`docs/experiments/$(date +%F)_m1_header_mapping_llm.md`：
- unmapped 列清单 + LLM 建议表（列名/建议/置信/采纳?/勾稽拦截?）
- unmapped 前后对比（采纳安全建议后）
- 勾稽拦截的有害建议清单（证明 LLM 不能裸信，需校验把关）
- 成本：token/列、延迟/列
- 对冷启动北极星指标的贡献 + 与甲方"unmapped→补→回写"闭环的对应。脱敏。

## Phase 4 提交（不 push）
若为收集 unmapped 加了 `--dump-unmapped` 小功能可一并 commit；否则只 commit 报告。
commit 注明建议未自动写回 schema、需人审。

## 停止条件
:8004 不可用→BLOCKED；连续 3 列调用失败→停；全完成→正常结束。
不 push、不碰 TAT-DQA、不并发轰炸 :8004。
