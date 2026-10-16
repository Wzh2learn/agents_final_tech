# LOOP_D_RETURN — AI-Assisted Evidence Review v1

> 状态：`AI_REVIEW_COMPLETED_NOT_GOLD`
> 日期：2026-10-16
> 性质：明确标注的 AI 辅助诊断，不是人工标注，不是独立 gold，不是资格 PASS。

## 1. 执行情况

- 执行者：Loop D（AI）。
- 输入：A1 的 12 题 AI 初标、`packets/stage2_cases.json`、原表/扰动表/段落/官方参考、`coordinator/case_provenance.json`、机械检查。
- 方法：逐题读取真实表与段落；独立重算可用算术；对参考状态、任务影响和证据引用做挑战。
- 调用：0 model / 0 judge / 0 API / 0 training；未启动子代理。
- 未修改：A1 初标、原人工包、人员表、封存表、官方题目、冻结稿、v1-v4。

## 2. 科学发现

- R1 暂定分布：PRESERVED 6 / ALTERED 1 / UNDETERMINED 5。
- R2 复核后：标签分布不变；`label_changes = 0`；12 题全部 `ACCEPT_PROVISIONAL`。
- 没有证据推翻标签，但发现了比标签更重要的问题：
  - Q06：ALTERED 应限定为局部 column-identity/unit evidence damage，不是整表损坏或模型失败。
  - Q07：U 来自题干/官方参考期间不一致，与 `cashflow` 扰动无关。
  - Q11：U 来自表级 unit 证据缺失；`turnover` 语义可由段落恢复。
  - Q08/Q09：缺冲突优先级规则，不能临时造规则；保留 U。
  - Q01：U 先由题干/参考期间歧义驱动。
  - Q02/Q04/Q05/Q10/Q12：P 成立，但必须逐题限定，不推广到整表。

## 3. 四类状态

- 材料状态：原包材料保持只读；本轮只读取与本地复算，未改材料。
- 人员状态：AI 支线 R1=A1、R2=Loop D、R3=总规划师助手；不是三位独立人类；原 human roster 仍 `UNASSIGNED`。
- 标注状态：AI 诊断复核已完成；人工独立标注仍未发生；没有 Stage1/Stage2 人类提交或封存。
- 科学资格状态：`NOT_ESTABLISHED`；本轮不能签发 task-gold PASS，不能启动 Layer-2。

## 4. 剩余缺口

- 独立人工 gold 仍不存在；本轮不可替代。
- Q01/Q07/Q11 的参考/来源问题需要题目或来源修订。
- Q08/Q09 需要先定义冲突优先级。
- Q06 需要更强来源映射确认是证据损坏还是可恢复。
- A1 与本轮均为 OPEN_BOOK，已见历史标签；模型版本未独立记录。
- 数据包仍 `LOCAL_ONLY`，未做远端同步。

## 5. 唯一下一步

由总规划师/R3 先决定是否修订测量契约并隔离 Q01/Q07/Q11；在契约修订前，不启动 Layer-2，不把 AI 标签升级为 gold，不报告总体有害率或人际一致率。

## 6. 产物

- `LOOP_D_CASE_REVIEW.json`：12 题逐例复核。
- `DISAGREEMENTS.md`：证据/归因分歧。
- `NEXT_RESEARCH_DECISION.md`：下一步设计与预算。
- `LOOP_D_RETURN.md`：本文件。
