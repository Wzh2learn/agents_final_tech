---
name: jinrong-docs-sync
description: JinRongAgents 项目文档四层结构（活文档/当前/实验/归档）治理与 docs/INDEX.md 单一入口维护。新增文档、归档文档、neat 收尾、发现文档与实况脱节、或不确定某份文档是否仍有效时使用。
---

# jinrong-docs-sync

固化本仓库文档治理规则。任何文档新增/归档/整理操作先读本 skill，再动手。

## 四层结构

| 层 | 位置 | 性质 | 写入规则 |
|---|---|---|---|
| 活文档 | docs/ 顶层 + 根 AGENTS.md + memory/ | 持续维护，冲突时以这层为准 | 随代码变更同步更新 |
| 当前 | docs/ 顶层编号文档 | 当前事实与交付面 | 事实变化即更新；过时则归档 |
| 实验 | docs/experiments/ | 实验与审计记录 | 只追加不重写；汇总进 SUMMARY_*.md |
| 归档 | docs/archive/ | 只读历史 | git mv 进入，禁止 rm，禁止作为现状依据 |

## INDEX.md 维护规则

`docs/INDEX.md` 是文档导航唯一入口：

1. 任何文档新增或归档，必须同步更新 INDEX.md 对应分组，二者在同一个 commit 里。
2. 归档文档从"当前"组移入"归档"组条目，保留一行说明。
3. 新实验报告不必逐条登记；新类别（如新 SUMMARY）需登记。

## 红线

1. OpenCode/MCP 交付物三件永不归档或删除：`docs/09_OpenCode与现有RAG_MCP实施方案.md`、`docs/10_OpenCode开发机运行说明.md`、`docs/2026-07-19_m2_mcp_verification.md`。
2. `HANDOFF.md` 冻结于 2026-08-03 快照，不再更新；现状快照写 `memory/STATE.md`。
3. 归档用 `git mv` 不用 `rm`。
4. 带日期的历史快照保留原文，加"历史快照"标注，不改写数值。

## neat 文档同步 checklist

1. 读 `memory/STATE.md` 与最近 `logs/graph/dispatch_log.md`，确定当前事实。
2. 找出本轮新增/修改的文档，确认放入正确层。
3. 找出被本轮工作取代的文档，`git mv` 归档。
4. 更新 `docs/INDEX.md`。
5. 用 `docs/architecture/phase2_docs_inventory.md` 口径抽查：引用现状数字（测试数、RAG QA、模型路由）的段落是否与实况一致。
6. commit 信息以 `docs:` 开头。

## 现状数字的权威来源

测试数/RAG QA/解析率等指标以远端实测为准（pytest 输出、scripts/m1_rag_qa.py 输出），不抄旧文档。模型路由以根 AGENTS.md "Model Routing" 节为准。