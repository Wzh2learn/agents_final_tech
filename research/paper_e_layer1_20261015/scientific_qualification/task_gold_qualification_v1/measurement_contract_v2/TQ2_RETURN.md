# TQ2_RETURN

> 状态：`OFFLINE_CHECKS_PASS_TASK_GOLD_NOT_ESTABLISHED`
> 身份：Loop D（AI）。无额外模型端点调用、无网络检索、无候选系统推理、无训练/生产 API。
> 日期：2026-10-16

## 1. 实际可执行的任务范围

- 9 份任务规格：Q02/Q03/Q04/Q05/Q06/Q08/Q09/Q10/Q12。
- 3 份隔离卡：Q01/Q07/Q11，保留原题与参考，不补写修正版。
- 9 份 public_inputs：仅含 task_id、question、perturbed_table、paragraphs；无原表、官方参考、证据坐标、gold、v4/checker 字段。
- 状态：6 份 `REFERENCE_REPLAY_READY`；3 份 `PARTIAL_REFERENCE_REPLAY`（Q06/Q08/Q09）；0 份 `MEASUREMENT_SPEC_BLOCKED`。
- 离线检查：7 项检查全部 PASS；4 个负向检查全部按预期拒绝或阻断。

## 2. 参考复算结果

Q02 span、Q03 15363-1309=14054、Q04 135-138=-3、Q05 31 Jan 2019+10y=31 Jan 2029、Q06 319-11=308（仅原参考路径）、Q08 排除 Total 后 argmax 405,000→2 Jul 2017、Q09 9.73%、Q10 0.47（非 47%）、Q12 10-4=6。全部通过机械复算。

## 3. 仍依赖 AI 解释的语义假设

- Q04：`operat1ng`→operating 的恢复依赖 Finance Leases 列与段落 1（AI_INFERENCE）。
- Q06：原参考列身份只在原表成立；扰动表 c2/c3 身份与单位未解决（UNRESOLVED）。
- Q08：附加 `2021-期末日期` 是否作用于 Exercise Date 必要维度未解决（UNRESOLVED）。
- Q09：`Consoli2021期末d` 是否影响本题范围必要维度未解决（UNRESOLVED）。
- Q12：左侧 For the Year 与右侧 As of 的组选择依赖行名、n/a 结构与段落 1（AI_INFERENCE）。
- Q02/Q05/Q10：P 依赖未变的下层表头、段落或本题不使用被改列。

## 4. 未解决缺口

- Q01：2018 题干与 forfeiture 滚动期间缺口。
- Q07：2019 average 与跨 2018/2019 平均缺口。
- Q11：表级/report 级 million 单位来源缺口；rel_paragraphs=11 是 capex。
- Q06：局部列身份/单位证据损伤候选，未证明唯一不可恢复或可恢复。
- Q08/Q09：缺附加年份/范围词的冲突优先级规则。
- 无独立人工 gold；无系统输出；`system_outcome = NOT_RUN`。

## 5. 是否值得进入下一阶段设计

**条件性：只有先解决参考缺口与语义冲突规则，才值得设计新的独立小面板。** 当前主要成果是机械复算与字段隔离，尚没有可辩护的完整任务语义 gold。若 Q01/Q07/Q11 无新增来源、Q08/Q09 无预定义冲突规则，建议停止对旧面板继续投入；不要把离线 PASS 当作 task gold 或论文贡献完成。
