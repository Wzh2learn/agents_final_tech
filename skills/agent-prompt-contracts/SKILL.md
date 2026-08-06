---
name: agent-prompt-contracts
description: JinRongAgents 已验证的 4 条 agent prompt 契约 (verbatim 首查 / FORMAT_HINT / bash 先行 / 只读 summary)。编写或修改任何 OpenCode agent、Loop A/C prompt 时必读; 修复失败的 prompt 改动必须同 commit 补录本 skill (AGENTS.md 治理规则)。
---

# Agent Prompt 契约库 (已验证)

每条契约都来自真实失败 → 修复 → 回归验证。格式: 失败模式 → 对策 → 验证方式。新契约无证据链接不得入库。

## 1. verbatim 首查 (Verbatim First Query)

**适用**: 任何自主发起检索查询的 LLM (m2-qa、RAG agent)。

**失败模式**: 模型把用户问题"善意"缩写成实体名 ("嘉兴民安的总资产是多少?" → 只检索 "嘉兴民安")。本系统 fallback 排序 = 查询词在 chunk 内包含计数, 查询越短命中越差 → 漏召回。

**对策**: prompt 明写 "首查必须逐字使用用户完整原问题 (保留 资产总值/币种/市值 等全部字段词), 不得缩写"; 仅允许在字段缺失时追加一次 "实体名+字段关键词" 补充查询。

**验证方式**: RAG QA 15 问回归全跑 (scripts/m1_rag_qa.py, 基线 15/15); 抽查检索侧日志首条 query 是否为完整问句。

**证据**: docs/experiments/2026-08-05_opencode_e2e.md §6 (08-05 S3 M2 链 PASS 带引用)。

## 2. FORMAT_HINT (机器解析输出契约)

**适用**: 输出被程序解析的任何 agent (JSON 契约场景)。

**失败模式**: a) 答案包 markdown 围栏/散文 → 解析失败走兜底; b) sources=[] 但出处内嵌在答案文本里 → 下游溯源丢失 (08-06 实测约半数请求)。

**对策**: 三层防御: ① agent prompt 内嵌输出契约 — "最终回复必须是且仅是单个 JSON, 无围栏无 bullet" + 完整示例 + 显式拒绝条款; ② 请求侧追加 FORMAT_HINT (src/biz/opencode_adapter.py); ③ 确定性保守兜底提取器 — 只提取答案中已出现的真实引用, 永不虚构。

**验证方式**: 连续 10 问零空 sources; 单测钉住契约透传 / sources:[] 显式拒绝 / echo 提示词示例负例 (tests/test_opencode_adapter.py)。

**证据**: 62d21e3 (契约加固) + c5a8ecf (F3/F4 测试守卫); docs/18 08-06 section。

## 3. bash 先行 (Bash First, 证据先于断言)

**适用**: 所有验证/判定类任务 (Loop B、evidence-verifier、任何验收)。

**失败模式**: 模型凭训练记忆或 commit message 声明"判定 PASS"; 声称跑过测试但实际没跑 → 验收失真 (08-04 夜间验收审计抓出过多处声明与实况漂移)。

**对策**: 判定必须由真实执行的 bash 命令产生 (pytest/curl/diff/md5sum), 模型只转述输出并判定; 验证层尽量纯 bash 无 AI (Loop B = 信任锚点, 1800s 周期常驻)。审计 prompt 明写"不轻信任务描述与 commit message, 逐项独立核验"。

**验证方式**: verify-report.json 与手动复跑一致; "已修复"声明抽查复验 (重跑相关 pytest/curl)。

**证据**: scripts/graph/loop_b_verify.sh (07-31 起持续 PASS); docs/experiments/2026-08-05_opencode_e2e.md S3。

## 4. 只读 summary (Read-Only Compact Summary)

**适用**: 多 agent pipeline 的判定方 (evidence-verifier 类)。

**失败模式**: 判定方自行打开原始文件 → 超出证据范围再解读、scope creep、与执行方数据得出矛盾结论; 多信息源互相打架。

**对策**: prompt 把判定方数据源写成白名单: "第一且唯一数据源是 /tmp/opencode/m1_compact_summary.json, 用 bash cat 读一次; 禁止 open/glob/grep 任何其他文件 (尤其原始样本)"; 同时给判定模板 (PASS/FAIL + 具体理由 + 必须出最终文本, 不得静默结束)。

**验证方式**: e2e 彩排观察工具调用轨迹 (应仅一次 cat); verdict 与执行方实测数据交叉一致。

**证据**: opencode.json evidence-verifier prompt; 08-05 S3 verdict PASS 与 m1-extraction 实测一致。

## 治理规则

1. 修复任何 prompt 相关失败的改动, 必须同 commit 在本 skill 补录/更新对应契约 (失败模式 → 对策 → 验证方式)。
2. 契约条目必须附证据链接 (commit hash / 实验报告路径); 无证据不入库。
3. 新增 agent 前先扫本库: 涉及检索→契约 1, 涉及机器解析→契约 2, 涉及验证→契约 3/4。
