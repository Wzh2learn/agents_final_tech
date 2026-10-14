# Loop C 独立复审任务 T1R-02：harness_rsi_v1 T-1 v2 运行包 + F1 争议仲裁

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立复审：不修改任何仓库文件、不 git、不通过自身运行以外的网络、不调用模型端点/生产服务/数据库、不进入 T0。全部输出只写 stdout。

## 背景
- 你（或同角色）此前完成 T1R-01 复评，对 v1（run 20261014T072826Z_6f19a394）给出 **REJECTED** 提案与 F1–F6。
- 执行者随后完成修复轮：R1（candidates/.gitkeep + FILE_MANIFEST/FILES.md 同步，并在后续补钉 FILES.md 条目）、R2（v2 重跑 run **20261014T085957Z_4e1698d1**，22 项 = 18 PASS + 4 INFO + 0 FAIL），并对 F1 提出**反驳与降级**仲裁（要点：pin=本地工作树字节且可复现；repo blob 双边逐字一致=无内容漂移；GB10 原始字节差异=EOL/检出表示；".gitattributes GB10-raw-bytes 权威"被扩大适用；"回填/自相循环"不成立）。另有一个被废弃的草案目录 runs/T-1/20261014T085638Z_ba9297ac/（内含 SUPERSEDED.md，勿当作结果）。
- 你的职责：独立复审 v2 运行包与修复是否成立，并对 F1 争议给出你自己的结论；输出**提案**（ACCEPTED/REJECTED/PENDING_HUMAN_REVIEW，针对 v2）。state/registry 不由你写。

## 必读（只读）
1. 仓库 AGENTS.md；2. `research/harness_rsi_v1/README.md`、`cards/T-1.md`、`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`、`sources/provenance.json`；3. v2 run 六件全文（`runs/T-1/20261014T085957Z_4e1698d1/`）；4. v1 run 六件（`runs/T-1/20261014T072826Z_6f19a394/`）；5. `reviews/T1R-01/` 四件 + 原始 log；6. `runs/T-1/20261014T085638Z_ba9297ac/SUPERSEDED.md`。

## 必须独立复算（记录命令与退出码；工具箱已放行 python3(含 -c/heredoc) 与 xargs；**避免 find -exec 与 $(...)（Claude Code 注入防护硬拦截）**；若某命令被拒请如实记录并改用等价写法）
1. v2 六件产物 SHA-256/字节 vs 其 artifacts_manifest（manifest 不自哈希）。
2. 包清单（排除 runs/、reviews/ 后）与 FILE_MANIFEST `required_files` 集合逐项一致；`files[]` 52 条逐件 bytes/sha256 实算一致（**特别复核 FILES.md 条目已被重钉**）；两轮原文与 provenance 一致；全部 JSON 解析、空 JSONL 核对。
3. 19 卡字段/§1–§10/状态/授权；依赖无环且卡↔矩阵依赖一致；预算 BR 4/3、BC 66/8、BS 106/4、SHADOW 6/2、META 12/2；docs/INDEX.md 恰 1 条入口；12 条 input_bindings。
4. **F1 争议的三域复算**（核心）：对 authority_map 13 条逐条计算：本地工作树 raw SHA-256（`sha256sum`）、本地 repo blob（`git rev-parse HEAD:<path>`）、GB10 工作树 raw 与 blob（本机即权威树）。检验执行者三项主张：(i) pin==本地 raw 13/13；(ii) 本地 blob==GB10 blob 13/13（=> 无内容漂移）；(iii) 恰好 6/13 GB10 raw≠pin。然后给出你对 F1 的独立结论：它是"HIGH/核心失信（含回填指控）"还是"MEDIUM 哈希域/标注缺陷"，并说明你接受/不接受执行者哪些反驳点；若你仍持"回填/自循环"判断，请给出可复核的实测证据。
5. 修复闭合核验：F2（candidates/.gitkeep 入库且双树存在、manifest 含该条目）；F3（v2 summary 计数与机器可读产物一致）；F4（unresolved_register U04 分类口径自洽）；F5（矩阵 outputs 约定注明）；F6（C17 写入边界、C18 R/C/S+人工门检查存在且可复算）；草案目录是否有 SUPERSEDED 标记且未被当作结果。
6. 反证尝试：v2 是否仍存在越界写入、伪造事件、历史 PASS 当结果、声称与实测不符等。

## 硬性约束
- 全程只读；不得创建/修改/删除任何文件；工作目录为仓库根；不 git；不联网；不调用端点/服务/数据库；不进入 T0。

## 输出（仅 stdout；三个标记块，机器将逐字转写）
=== FILE: REVIEW.md ===
（Markdown：范围；逐项检查结果与命令；对 F1 争议的独立结论；发现 Fx（含严重度/证据）；FACT/INFERENCE/UNVERIFIED 分列；未验证面；对 v2 的判定与理由）
=== FILE: review_receipt.json ===
（JSON：reviewer/runtime；reviewed_artifact_sha256（v2 六件 + T-1 卡 + protocol + T1R-01 四件）；recomputed 实测（含三域表）；checks；calls（自身模型会话 1；network/services/db 0；内部 token UNRESOLVED）；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}（针对 v2）；reviewed_artifact_sha256；scope；justification；dissent）
=== END ===

重申：只写提案；registry/state 由收口者更新。不要进入 T0。