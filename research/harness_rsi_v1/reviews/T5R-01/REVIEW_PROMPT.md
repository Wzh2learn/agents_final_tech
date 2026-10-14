# Loop C 独立评审任务 T5R-01：harness_rsi_v1 T5 R两个对象接口（本卡唯一 1 次 Loop C 评审名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改任何文件（仓库与被审包只读）、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T6。输出只写 stdout（三块标记见文末）。

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T1–T4 已验收（T4 v2=T4R-01 ACCEPTED，含 A1 消费约束：下游读 T4 baseline 须以 case-level 为准）。
- 被审对象：T5 run `research/harness_rsi_v1/runs/T5/20261014T195445Z_60c8e213/`（34 文件，已提交 `7f0bb9a`）。声称：两个 recipe（预检/证据交付）各一对象、仅引用 3 个以 T4 v2 只读适配器为目标的登记操作；调用方探针 17/17 ×2 轮一致（2 正例接受、15 负例拒绝）；坏摘要仅在内存派生；G1 全绿；B0 零调用。
- T4 教训继承：仓库内 .md 收据夹具必须全部过守卫（失配变体运行时派生，不落盘）。

## 必读（只读）
`cards/T5.md`、`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`、`evaluation/reliability_spec.md`、`docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`；T5 run 全文（先读 receipt.json、summary.md、recipe_interfaces.json、registered_operations.json、recipe_fixtures/README.md、run_probes.py、caller_validator.py，再抽查 recipe_fixtures/ 与 scratch/）；T4 v2 run 与 `reviews/T4R-01/`（依赖事实）。

## 工具约束（先读，避免撞墙）
- 白名单不含 git、mkdir、cp、mv、rm、chmod；git 被拒时用双方法替代（字节派生 git blob SHA-1 + `.git/index` 解析）；被拒命令如实记录。
- scratch/output 只放仓库外（例：`/home/testuser/wzh/loop_runs/t5r01_recheck_a/`）；不得在被审 run 或仓库内写任何文件；披露全部仓库外路径。
- 运行 .sh/.py 可用 `python3 -c 'import subprocess; ...'` 包装。

## 必须独立复算（记录命令与退出码）
1. **计数与哈希**：run 恰 34 文件；manifest 33 条（自不含，`self_hash_policy`）逐条 SHA-256/字节实算；无遗漏/多余。
2. **input_bindings 等**：卡片 6 输入 + T4 v2/T4R-01 依赖双方法复算；freeze 值一致；T4R-01 decision=ACCEPTED、blocking=0。
3. **核心——接口闭合与调用方校验（实弹）**：
   a. 用你自己的 scratch 重跑 `run_probes.py`（按其用法）两遍 → 17/17 一致；逐项核对 2 正例被接受、15 负例被拒绝；逐负例核对拒绝理由与探针定义（未登记操作引用、shell/命令文本、任意路径、类型/范围错误、伪造摘要、错哈希、漏字段等）。
   b. **独立对抗探针（自构造 ≥3 个新负例）**：例如新造的未登记 op_id、shell 注入变体、篡改哈希/字段后注入——必须全部被调用方校验拒绝；并至少 1 个新合法正例被接受。记录证据。
   c. 核对"不能执行任意 shell"：recipe 只能引用注册表条目；确认 caller_validator 在目标执行前拒绝命令文本/自由参数；抽查 registered_operations.json 每项含 允许参数边界+副作用声明+级别范围。
   d. **G1 与派生对照**：包内 4 个 `.md` 逐个守卫 check rc=0；按 README/脚本复现"内存派生坏摘要被拒"（不得落盘失配 .md）；确认包内无失败收据块 .md。
4. **A1/A2/A3/A-common 逐条 + 级别**：A1（一 recipe 一对象；不能任意 shell——含上面负例证据）；A2（接口错误调用方可见；伪造摘要不可通过）；A3（未修改 C/S 评分、旧实验组件、冻结件——写入边界+被引用工具 blob 未变）；A-common；所有 PASS 带级别+范围（不得裸 PASS，不得声称 END_TO_END/FORMAL）。
5. **T4 消费约束遵守**：核查 T5 对 T4 baseline 的读取仅用 case-level 字段；grep 证明未消费 `combination_results`/`failure_family_profiles` 派生汇总。
6. **对抗面**：交付字段四类分离（资格/审计/执行/科学结论，字段与状态无混合、无单一总体 PASS）；frozen_protections 覆盖 reliability_spec 硬门语义；探针契约来源为"真实调用方形态"且写明；修复记录（attempt1/retry 等多样件）与披露一致；usage 零声明与探针计数自洽；写入边界 mtime 扫描。
7. **披露准确性**：TASK_PROMPT 与派发原文比对（逐字性；若非逐字如实记录）；LOCAL/B0/范围限定措辞。

## 反证重点
- 探针是否只测"实现自己的假设"（实现-测试同错）？用你自己的新探针验证调用方契约。
- 15 个负例里是否有"为过而过"的构造（如天然必败的输入）？评估每个负例的判别力。
- 2 正例是否被宽松放行（应接受但也要记录其验证深度）。

## 输出（仅 stdout；三块标记）
=== FILE: REVIEW.md ===
（Markdown：范围与方法；逐项结果（命令/退出码证据）；实跑复算；BLOCKING/ADVISORY（ADVISORY 附升级条件）；FACT/INFERENCE/UNVERIFIED；判定与理由）
=== FILE: review_receipt.json ===
（JSON：review_id="T5R-01"；task_id="T5"；reviewer/runtime；reviewed_artifact_sha256（T5 关键文件 ≥12 件含 sha256/字节）；recomputed（计数/manifest/bindings/freeze/探针两轮/新对抗探针/G1 派生对照/T4 消费核查/写入边界）；checks；calls（session=1；network/services/db/model=0；token UNRESOLVED）；refused_commands；reviewer_side_effects_disclosed；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；blocking_items；advisory_items；scope；justification；dissent；next_steps）
=== END ===

重申：只写提案；registry/state 由收口者更新；不得进入 T6。
