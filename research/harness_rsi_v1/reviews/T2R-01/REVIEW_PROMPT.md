# Loop C 独立评审任务 T2R-01：harness_rsi_v1 T2 评价底座（本卡 BR 强评审仅此 1 次名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T3。输出只写 stdout。

## 背景
- R 线已获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T-1/T0/T1 已验收。
- Loop A（`t2-eval-base`，rc=0）已交付 **T2 run**：`research/harness_rsi_v1/runs/T2/20261014T145327Z_9a02a34a/`（52 件；含 evaluator_spec.json、evaluator/（evaluate.py + fixtures + run_qualification.py + README）、qualification.json、sealed_access_proposal.json、receipt.json、summary.md、artifacts_manifest.json、events.jsonl、TASK_PROMPT.md）。
- Loop A 已完成"完成前自检"（receipt.self_check：A1/A2/A3/A-common PASS；含 issues_found_and_fixed）。**本卡 BR 强评审仅 1 次名额**：请在不降低标准的前提下，把发现分为 **BLOCKING（必须修复后重审）** 与 **ADVISORY（不影响验收、可收口层登记）** 两类，各自附证据。
- 你的职责：独立复算并给出提案（ACCEPTED/REJECTED/PENDING_HUMAN_REVIEW）。registry/state 不由你写。

## 必读（只读）
`cards/T2.md`、`evaluation/reliability_spec.md`、`evaluation/human_review_protocol.md`、`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`、上述 T2 run 全文（先读 receipt/summary/evaluator_spec/README）。

## 必须独立复算（命令+退出码；python3 可用；避免 find -exec 与 $(...)）
1. run 目录恰 52 件；`artifacts_manifest` 51 条逐条 SHA-256/字节实算一致（自不含）。
2. receipt：`input_bindings`（卡片 7 输入 + T1 v3 receipt + T1I-03 + TASK_PROMPT）逐条实算；`protocol_freeze_check` 与 FROZEN 值一致；usage 零编排调用声明无相反证据；三轴三值正确；无伪造 ACCEPTED/freeze。
3. **实跑评价器（核心）**：`python3 evaluator/run_qualification.py`（按其用法；记录 exit）；抽查 `python3 evaluator/evaluate.py --case <fixture> --out -` 的 BLOCK/ALLOW/REVIEW 与 exit code（正常 0、fail-closed 3）；复核 `qualification.json` 的 34/34（两轮）、六族覆盖、三退化策略"硬门失败"的判定逻辑（并独立按 promotion_rule 重算三个策略是否确实不满足推广规则）；抽查 3–5 个 T1 case bundle 的 expected vs actual。
4. A1/A2/A3/A-common 逐条核验（含：缺字段/错绑定/空集 fail-closed 的显式性；R/C/S 不混用；候选不可写判分代码与标签——在 evaluate.py 中确认只读工件字节与哈希；封存隔离未实现 + sealed_access_proposal 的 PT-01..06 权限测试要求、无封存资格主张）。
5. 反证尝试：exit-code 契约是否与 README/声明一致；是否有隐藏偏向（全 BLOCK/全 ALLOW 倾向）；自检 `issues_found_and_fixed` 是否如实；T1 嵌套证据哈希漂移披露是否准确；写入边界（`git show --name-only 5756984` + 当前 status）；是否有越界/联网/模型调用痕迹。

## 硬性约束
只读；不 git 写；不联网；不调端点/服务/数据库；不进入 T3。被拒命令如实记录。

## 输出（仅 stdout；三块标记；块间不要多余分隔符）
=== FILE: REVIEW.md ===
（Markdown：范围；逐项结果；3 项实跑证据；发现分 BLOCKING/ADVISORY（各附证据与建议）；FACT/INFERENCE/UNVERIFIED；对 T2 的判定与理由）
=== FILE: review_receipt.json ===
（JSON：reviewer/runtime；reviewed_artifact_sha256（T2 八件 + T2 卡 + reliability_spec + protocol）；recomputed；checks；calls（自身会话 1；network/services/db 0；token UNRESOLVED）；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；blocking_items；advisory_items；scope；justification；dissent）
=== END ===

重申：只写提案；registry/state 由收口者更新。