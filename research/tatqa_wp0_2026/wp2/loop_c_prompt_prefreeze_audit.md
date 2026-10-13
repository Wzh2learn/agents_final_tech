# TAT-QA WP-2 预冻结包独立审计 — Loop C 审计卡

> 状态: DRAFT — 尚未派发（Loop D 收口 2026-10-13）。

- task: tatqa-wp2-prefreeze-20261013
- 角色: 独立审计层。只读被审对象；只写自己的报告；不改任何被审文件、不 commit、不 push、不调模型、不跑 S4+。
- 背景: Loop A 将按任务卡于同一 repo 执行 S0–S3+S10（**尚未派发**；任务卡: research/tatqa_wp0_2026/wp2/loop_a_prompt_prefreeze.md）。

## 必读
1. docs/research/WP2_EXECUTION_RUNBOOK_v1.md
2. docs/research/WP1_COMPLETION_RECORD_v1.md（§4 解决政策）
3. docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md（spec rev 1.2）
4. docs/research/WP0_TATQA_EVALUATION_PROTOCOL_v1.md
5. research/tatqa_wp0_2026/wp1/ 代码与收据；wp2_split_dryrun.py 与收据；数据 data/research/tatqa_wp0_2026/

## A. 立即可做的设计级预检
- S0 政策一致性: 「向上对齐」是否确实更严格、无判据放松；fixture 是否覆盖 gated 用例（先按任务卡与代码现状评估）。
- 独立复算: 重跑 wp2_split_dryrun.py（同 seed）验证确定性；从 origin_manifest.json 独立复算 182 origins / 176 个 >=2 行 / 角色 disjoint；核对分桶规则 outcome-blind。
- 记录 WP-1 run3 收据与 run_logs 当前 sha256（后续比对基线）。

## B. 等待 Loop A 产物（窗口 <=40 分钟，每 2 分钟查一次）
轮询: research/tatqa_wp0_2026/wp1/S0_FIX_RECEIPT.json；research/tatqa_wp0_2026/wp2/{ITEMS_V2_RECEIPT.json, SPLIT_RERUN_RECEIPT.json, WP2_PREFREEZE_EXECUTION_REPORT.md}；docs/research/{WP1_PREFREEZE_FIX_NOTE_v1.md, WP2_TARGET_UNIT_RULES_DRAFT_v1.md}
出现即审计（能审多少审多少）:
- S0: 实现与政策一致；抽 1 项测试独立重跑；历史收据/日志未动；fixture 非恒真。
- S1: 从产物独立复算计数；22 角色 origins >=2 题；重跑 byte-compare；无标签/结果泄漏。
- S3: 独立重跑并回执比对。
- S2: 仅草案、未越权冻结、术语符合 protocol。
窗口内未出现 -> 只交付 A 部分，注明「实现审计待另行开窗」。

## 输出
只写 docs/research/WP2_PREFREEZE_LOOP_C_AUDIT_v1.md: 范围/时间、逐项发现（FACT/INFERENCE 分开）、命令与结果、未验证面、逐项 PASS/CONDITIONAL/REJECTED + 总体判定。
发现缺陷: 记录并交 D/A，不自行修复。

## 红线
不改被审对象与历史文件；零模型调用、零对外网络、不读写凭证、不 commit。
