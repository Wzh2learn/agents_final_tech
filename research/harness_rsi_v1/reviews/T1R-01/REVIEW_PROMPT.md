# Loop C 独立评审任务：harness_rsi_v1 T-1 文档核对运行包

你是在 GB10 上运行的 Loop C（独立质量审计层，Claude Code，角色与 `scripts/graph/loop_c_audit_prompt.md` 一致）。本任务只做**独立评审**：不修改任何仓库文件、不做 git、不联网、不调用模型端点/生产服务/数据库、不进入 T0。你的全部输出只体现在 stdout。

## 背景
- 规划包：`research/harness_rsi_v1/`（SPECIFICATION_ONLY；仅 T-1=READY，T0–T17=DRAFT；全部 execution_authorized=false；协议与预算均 DRAFT/未授权）。
- 另一会话的低成本执行者已交付 T-1 文档核对运行包：`research/harness_rsi_v1/runs/T-1/20261014T072826Z_6f19a394/`（6 件：document_inventory.json、unresolved_register.json、receipt.json、summary.md、artifacts_manifest.json、events.jsonl），其结论为 18 项检查 16 PASS + 2 INFO + 0 FAIL。
- 你的职责：独立判断该 run 包与其结论是否成立；按 `contracts/schemas.json` 的 decision 词汇给出**提案**（ACCEPTED / REJECTED / PENDING_HUMAN_REVIEW）。状态与 registry 更新不由你写。

## 必读（只读）
1. 仓库 `AGENTS.md`（必要规则）。
2. `research/harness_rsi_v1/README.md`、`cards/T-1.md`（卡内 JSON 与 §1–§10）、`contracts/protocol.json`、`contracts/authority_map.json`、`contracts/execution_policy.md`、`contracts/budget_profiles.json`、`contracts/schemas.json`、`sources/provenance.json`。
3. 上述 run 包 6 件全文。

## 必须独立复算（不得采信执行者摘要；逐项记录命令、退出码、实测值）
1. 6 件 run 产物逐件 SHA-256 与 artifacts_manifest.json 对照；确认 manifest 未自哈希。
2. 包内 52 个文件逐件 SHA-256 与 document_inventory.json 的 files[] 对照；抽核 FILE_MANIFEST.json 的 files[] 声明值。
3. 两轮原文（sources/planning_round1.md、planning_round2.md）字节 SHA-256 与 provenance 一致；确认原文未改写（字节数/行数）。
4. 状态与授权：19 卡仅 T-1=READY、T0–T17=DRAFT；全部 execution_authorized=false；protocol/budget 未授权；state/current.json 无 ACCEPTED/ACTIVE；registry/*.jsonl 为空账本。
5. 卡字段与依赖：每卡 §1–§10 + JSON 元数据齐全；依赖无环且卡↔task_matrix 一致；BR=4/3、BC=66/8、BS=106/4、SHADOW=6/2、META=12/2 与 budget_profiles 合计一致。
6. docs/INDEX.md 恰 1 条 harness_rsi_v1 入口。
7. receipt 声明 vs 证据：18 项 checks 是否可由文件复现；input_bindings 的 12 条实算哈希与卡输入实际哈希一致性；usage 的零调用声明是否有反证；UNRESOLVED 登记（9 项+4 项运行级）与 UNRESOLVED.md / state/open_decisions.json 相符。
8. 反证尝试（对抗式）：主动尝试推翻执行者结论，例如 C12 两项被修正为"历史原文 path:line 引用、基础文件存在"的理由是否成立；空账本是否被误当作证据；历史 PASS 文字是否被当作结果；是否存在任何越界写入迹象；执行者是否遗漏应有检查。
9. 对照 pin（仅供比对，必须自行重算）：
   - cards/T-1.md a28af6a87986b64c240db23fc77332b0401573eea133203c42d0126e96f79f6d
   - contracts/protocol.json bfbf453def9386eb378f0370491892faf14edfc36a978d77647ba34b8baffcf6
   - sources/planning_round1.md cc4ef2da38702fb21ae364710d0db7480a856df34d7951e6275c3cbf271b25dd
   - sources/planning_round2.md ce68b925d451f134277ce80dac4c79254b656ab55c8ada639279f15925e2e38a
   - runs/.../receipt.json 9282079334d2b51e479025b85b2bd5ecb0311af03612b674acd3c850983b3ebf
   - runs/.../document_inventory.json 97f675dedd5c236534acdb4092d72b0e71e0a7941c3724d0a19a1d14ffba470d
   - runs/.../summary.md 9d5ce0ae48d10b8c8e376c4b5ec3b036b926c1d20cd672197c5429574b60419e
   - runs/.../artifacts_manifest.json d2c19db81454c6058da3e3d369fc30d76ec72a1f70fb3628318d999dfe8adf40
   - runs/.../unresolved_register.json 39898a993cccc7ce5d080743d7e5d5e7946fe7780a79e9748b317f72ec54b5aa
   - runs/.../events.jsonl 69b8b08dd918415021ab73b3388d1a51c73135624047e8c08944bde32bc30bc7
   （runs/... 即 research/harness_rsi_v1/runs/T-1/20261014T072826Z_6f19a394/）

## 硬性约束
- 全程只读；**不得创建/修改/删除任何文件**；只允许只读命令（cat/sed/ls/find/sha256sum/wc/grep/python3 标准库等），工作目录为仓库根。
- 不执行 git；不联网；不调用模型端点/生产服务/数据库；不运行 Loop B 或训练；不进入 T0；不改任何配置。
- 不做与"判断 T-1 run 包与结论是否成立"无关的扩展调查。

## 输出（仅 stdout，用下列标记分隔，机器将逐字转写）
=== FILE: REVIEW.md ===
（Markdown：任务与范围；逐项检查结果与所执行命令；发现 F1..Fn（含严重度与精确证据/路径）；FACT / INFERENCE / UNVERIFIED 分列；未验证面；判定（ACCEPTED/REJECTED/CONDITIONAL 语汇可按你角色习惯，但提案文件用 schemas decision 词汇）与理由）
=== FILE: review_receipt.json ===
（JSON：reviewer（含 runtime 版本）、reviewed_artifact_sha256 列表（6 件 + T-1 卡 + protocol）、recomputed 实测值、checks、calls（自身模型会话计 1；network/services/database 计 0；内部 token 用量 UNRESOLVED）、unverified、verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；reviewed_artifact_sha256；scope；justification；dissent）
=== END ===

重申：即使你倾向 ACCEPTED，也只写**提案**；registry/state 由收口者更新，不由你写。