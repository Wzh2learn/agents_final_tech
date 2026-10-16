# DISAGREEMENTS — Loop D AI Evidence Review v1

> 性质：AI 诊断复核，OPEN_BOOK，非盲态，非人工 gold。
> 本轮没有推翻任何 R1 暂定标签；以下记录的是**证据与因果归属层面的分歧**。

## D1 Q06：接受 ALTERED，但不同意“整表证据损坏”的宽泛表述

- 证据：c2/c3 由 `Net Tangible Assets Acquired`、`Purchased Intangible Assets` 变成 `资产(assets)`、`资产(元)`；段落3只有 purchase consideration allocation（in millions）。
- 反驳：损伤集中在两列的身份与单位证据；`Goodwill`、`Purchase Consideration`、行标签和金额仍在。不能写成“整表全部不可用”。
- 结论：维持 ALTERED，但限定为 **column-identity/unit evidence damage**，不是已观测模型失败。

## D2 Q07：接受 UNDETERMINED，但不同意归因于扰动

- 证据：官方 `(13,846+13,434)/2=13,640` 平均了 2018 与 2019；题干只写 2019 average。扰动只改 `Free cash flow (pre-spectrum)` 成 `cashflow`。
- 反驳：`cashflow` 标题改动与 adjusted EBITDA 问题无关；U 来自题干/官方参考不一致。
- 结论：维持 U；必须写成 reference/question-quality gap，不能写成扰动造成的任务损伤。

## D3 Q11：接受 UNDETERMINED，但不同意归因于 `turnover`

- 证据：数值 2,493+2,407=4,900；段落2/5 明确 Bell Wireless operating revenues；扰动 `OPERATING REVENUES -> turnover`。
- 反驳：`turnover` 在段落语境中足以恢复 operating revenues；真正缺口是表内没有直接 `in millions`，官方 `rel_paragraphs=11` 是 capex。
- 结论：维持 U；归因于 reference/source unit gap，不是扰动语义损伤。

## D4 Q08/Q09：接受 U，但拒绝临时建立冲突优先级规则

- 证据：Q08 给 Exercise date 加 `2021-期末日期`；Q09 把 Consolidated 改成 `Consoli2021期末d`。
- 反驳：两者都与表内 2018/2019 年份、year ended 30 June 2018 等上下文冲突，但契约没有规定“何时忽略额外年份/范围词”。
- 结论：维持 U。若后续契约明确任务只需年列算术，可重新评估；本轮不造规则。

## D5 Q01：接受 U，但归因于题干/参考期间歧义

- 证据：题干 `in 2018`，但 Forfeited 行位于 2018 年末至 2019 年末滚动表中；官方参考直接取 19.83−18.80。
- 反驳：扰动 `2017期末` 增加了新歧义，但原参考期间与题干对齐本身已有缺口。
- 结论：维持 U；先修题/参考期间定义，不能先算扰动损伤。

## D6 六个 P：接受，但必须逐题限定

- Q02、Q03、Q04、Q05、Q10、Q12 的 P 均来自具体题目的剩余证据或上下文冗余，不代表整表其他问题安全。
- Q04、Q12 尤其是“冗余上下文恢复”案例；Q02 是“未变段落直接定义”；Q10 是“扰动不在本题使用的列”。
