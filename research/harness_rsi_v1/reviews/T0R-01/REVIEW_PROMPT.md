# Loop C 独立评审任务 T0R-01：harness_rsi_v1 T0 提案包（协议 + 权威重钉 + 决策包）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审：不修改任何仓库文件、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T1。全部输出只写 stdout。

## 背景
- owner 已就 T-1 争议作出裁决：**1A**（6 项哈希失配按"工作树换行表示差异"处置、无内容漂移；T0 以 canonical 方式重钉 13 项、旧值留档）；**2行**（D:/AIRcommend 目录为合法钉定域）；**3确认**（T0 开跑）；此前 U01–U09 决定（U01 预算"不用担心"按建议采纳；U03 执行分工=便宜执行者+GB10 Loop A；U05 人类门=wzh；U06=B 远程核验已做；U07=C 仅 R 线至 M1；U08 未来证据；U09 标尺可辨别性预检；U02/U04 各自流程）。
- 执行者本轮产出 T0 提案包（**未生效**）：`research/harness_rsi_v1/runs/T0/20261014T101305Z_026e6533/`（7 件），含 authority_binding_proposal.json、protocol_proposal.json、owner_decision_packet.md、receipt.json、summary.md、events.jsonl、artifacts_manifest.json。
- 你的职责：独立复算并判断该提案包是否可交 owner 签字冻结；给出**提案**（ACCEPTED/REJECTED/PENDING_HUMAN_REVIEW）。registry/state/authority_map 的落地不由你写。

## 必读（只读）
`AGENTS.md`；`cards/T0.md`；`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`；`state/open_decisions.json`；上述 T0 包 7 件全文；`runs/T-1/20261014T085957Z_4e1698d1/receipt.json`；`reviews/T1R-01/`、`reviews/T1R-02/`。

## 必须独立复算（记录命令与退出码；工具箱：python3(含 -c/heredoc) 与 xargs 可用；**避免 find -exec 与 $(...)**（注入防护硬拦截），被拒请如实记录并改用等价写法）
1. T0 六件产物 SHA-256/字节 vs 其 artifacts_manifest（不自哈希）；run 目录恰 7 件。
2. T0 卡 7 个输入存在且实算哈希 = `receipt.input_bindings`。
3. **authority 提案**：对 13 条逐条（a）`canonical_blob_id` == `git rev-parse HEAD:<path>`；（b）`local_worktree_raw_sha256` == 实算文件 sha256；（c）本机（GB10）raw 与提案记录一致；（d）分类计数 == {pin_matches_worktrees:7, eol_representation_uniform_crlf:3, eol_representation_mixed:3}、`unexplained`==0；（e）对 6 个失配项独立复验"剥离 CRLF 后与仓库对象内容逐字节一致"；（f）确认本提案**未改动** `contracts/authority_map.json`（`git status`/`applied:false`）。
4. **protocol 提案**：`proposed_protocol.status`==DRAFT、`execution_authorized`==false；是否忠实写入 U01–U09 与 1A/2行/3确认 决定、且**未新增任何权威/未伪造冻结**；用以下规则独立重算并比对 `proposed_freeze_sha256`：`json.dumps(proposed_protocol, ensure_ascii=False, separators=(",", ":"), sort_keys=True)` 的 utf-8 字节 SHA-256；确认 `contracts/protocol.json` 未被改动。
5. **决策包**：`owner_decision_packet.md` 的每条陈述是否与 owner 原话记录一致（重点核对 U01 的"不用担心"措辞与"3 项措辞小修待你点头"的说法）；先前发现的两处笔误（`Lo:p C`、U01"无上限"）是否已修正。
6. T0 receipt：三轴 DELIVERED/UNREVIEWED/NOT_ENABLED；usage 声明（模型请求 0 等）是否有反证；写入边界（仅 runs/T0/<id> + 本次评审目录）；无伪造 ACCEPTED/freeze。
7. 反证尝试：是否有越界写入、把提案当已生效、把历史 PASS 当结果、声明与实测不符。

## 硬性约束
全程只读；不得创建/修改/删除任何文件；工作目录为仓库根；不 git 写；不联网；不调端点/服务/数据库；不进入 T1。

## 输出（仅 stdout；三块标记，机器逐字转写）
=== FILE: REVIEW.md ===
（Markdown：范围；逐项结果与命令；发现 Fx（严重度/证据）；FACT/INFERENCE/UNVERIFIED；未验证面；判定与理由；明确"是否可交 owner 签字冻结"）
=== FILE: review_receipt.json ===
（JSON：reviewer/runtime；reviewed_artifact_sha256（T0 七件 + T0 卡 + protocol + authority_map）；recomputed（含 13 项 canonical 复算与 freeze 复算）；checks；calls（自身会话 1；network/services/db 0；token UNRESOLVED）；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；reviewed_artifact_sha256；scope；justification；dissent）
=== END ===

重申：只写提案；registry/state 与 authority_map 的落地由收口者/owner 决定。