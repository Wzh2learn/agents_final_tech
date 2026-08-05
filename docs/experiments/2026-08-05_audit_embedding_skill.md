审计已完成，但本会话所有文件写入（Write 工具、bash 重定向、tee、touch）均需未获批的权限，报告无法落盘到 `docs/experiments/2026-08-05_audit_embedding_skill.md`。以下交付完整报告全文，请调度方（Loop D）保存至该路径（该文件已被预创建为 0 字节，直接覆盖即可）。

---

# Loop C 审计报告 - 2026-08-05 23:45

## 审计范围
- 审计 commit 范围: `06623d3..c5fd7c0`（9a17da4 / a7f8282 / c5fd7c0）+ 未入库 `.env` 变更（`LOCAL_EMBEDDING_MODEL_PATH` / `LOCAL_EMBEDDING_DEVICE`）
- Loop D 指定重点: ① embedding 切本地 fallback/降级风险 ② m1-gap-triage skill 注册一致性 ③ memory 台账口径修正 ④ B4 清单新增三项可执行性 ⑤ 冻结节点完好性
- Loop B 状态: **PASS**（verify-report.json @ c5fd7c0, 2026-08-05 23:05:47 — frozen_nodes 0 violations / pytest exit=0 / api_anchors 0 failures）

变更清单（`git diff 06623d3..c5fd7c0 --name-status`）:
```
M  AGENTS.md                       (+1: Skill 武库 m1-gap-triage 行)
M  docs/25_交付架构决策.md           (决策拍板 + §4 执行路径 + B4 清单)
M  docs/INDEX.md                   (+2 登记: docs/25 + opencode_e2e)
M  memory/DECISIONS.md             (+4 决策条目)
M  memory/STATE.md                 (覆写快照, a7f8282 21:00)
M  memory/THREADS.md               (MCP/agent/e2e 口径 + embedding RESOLVED)
A  skills/m1-gap-triage/SKILL.md   (新 skill, 53 行)
```
**src/ / tests/ / config/ 零变更** — embedding 切换为纯 `.env` 运行时开关；tests/ 与 ~/wzh/m1_samples/ 未被触碰；TAT-DQA 冻结区零接触。

## 代码变更审查
- 变更摘要: 全部为 docs/memory/skills 层（决策固化 + 台账口径修正 + skill 入库）。
- 是否服务于甲方需求: **YES**（本地 embedding 恢复 vector 检索质量 = RAG 正确性地基；m1-gap-triage = 解析失败分诊方法论固化）
- 架构漂移风险: **LOW**（无代码变更；.env 开关路径 fail-closed，见焦点 1）
- 不当修改: 无

## 焦点 1: .env embedding 切本地 — fallback/降级风险
- `vector_store.py:get_embeddings()` (L153-190): `LOCAL_EMBEDDING_MODEL_PATH` 优先 → 本地 SentenceTransformer（目录不存在 ValueError，fail-closed）；否则云端路径、缺 `SILICONFLOW_API_KEY` 抛 ValueError (L67)。**provider 间无静默互切**。
- 当前 .env（mtime 20:47，未入库）本地路径已置 → "缺 key 降级"根因被配置层消除。
- 残留降级路径（**既有机制，非本次引入**）: `rag_service.py` L307-343 对 vector/BM25 异常逐集合捕获，双零走 `_local_fallback_docs`（metadata.fallback=True + warning）。本地模型路径若失效 → :5050 不崩但检索静默降级；检测 = 日志 "Vector retrieve failed" / fallback>0 / health embeddings。
- **潜在风险**: `LOCAL_EMBEDDING_DEVICE` 缺省 `"cuda"` (L172)，GB10 ARM64 Triton JIT 必失败 → 未来忘配 DEVICE 必踩降级。当前 .env 已正确置 cpu。
- MCP 免重启声明核实: `start_mcp_server.sh` L24-26 确实 source `.env`，叠加 config_loader load_dotenv 双通道 ✓
- :5050 重启核实: ps 显示 uvicorn PID 27100 启动 23:09 > .env mtime 20:47；dispatch #RESTART-VERIFY 23:22: embeddings=137、parse 嘉合att0 2表 285ms、QA 热 1.3s、"Retrieve vector=3" 证明非 fallback ✓
- 运维备注: .env 无版本控制，丢失/误改即回退降级；建议 `.env.example` 增补 LOCAL_EMBEDDING 示例段。

## 焦点 2: m1-gap-triage skill 注册一致性

| 检查面 | 状态 |
|---|---|
| 仓库 `skills/m1-gap-triage/SKILL.md` | ✓ 合规 |
| AGENTS.md 武库表 L314 | ✓ 已登记 |
| `sync_skills.sh` A_SKILLS 数组 | ✗ **未列入** — 合法通道不会分发到 ~/.codex/skills |
| `loop_a_exec_constraints.md` 触发条件表 (L113-118) | ✗ **未登记** |
| sync_skills.sh 幂等性 | ✓ 不受影响（rm -rf + cp -r；缺项仍 exit 0） |

**不一致**: SKILL.md 自称"已注册…sync_skills.sh 分发至 Loop A"，但分发脚本未含该 skill — 按治理规则 1 安装定义三分只完成其二。台账类漂移，不构成 REJECT 但必须闭环。

## 焦点 3: memory 台账口径修正核实
- ✓ **"QA 脚本从未降级"**: `m1_rag_qa.py` L34 import `m1_rag_ingest`，后者模块级 `setdefault("LOCAL_EMBEDDING_MODEL_PATH", …)` + `DEVICE=cpu` (L34-39) → QA 历来走本地 embedding，与 .env/云端 key 无关。口径准确。
- ✓ **"曾降级的仅 :5050/MCP 端点进程"**: 无 key → ValueError → rag_service 捕获走 fallback，与 dispatch S3 根因互证。口径准确。
- ⚠ **时序瑕疵**: c5fd7c0 (23:01:54) THREADS 已写":5050 已重启载入"，实际重启 23:09（ps）、#RESTART-VERIFY 23:22 — 表述领先事实 ~7 分钟。现值为真，不阻断。
- ⚠ **STATE.md 漂移（未随 c5fd7c0 覆写，仍 21:00 快照）**: ① "m1-gap-triage 未注册未 sync 等用户审阅" — 实际已注册；② ":5050 up 未动（重启等用户批窗口）" — 实际 23:09 已重启。第三例台账漂移（先例 5545fde/db6572b），需 Loop D 覆写修复。

## 焦点 4: B4 新增三项可执行性 + 冻结节点

| 条目 | 判定 | 说明 |
|---|---|---|
| 功能 \| 本地 embedding 加载 | ⚠ 可验证但观察手段缺失 | health/full 的 embedding 检查探测 :8004/v1/models，**不暴露 RAG provider**；"provider=local" 只能靠进程 env/日志 vector>0 间接证明；"764 向量"需 PG 跨集合合计（health 只报单集合 137）。建议 health/full surface provider。 |
| 并发 \| sidecar 会话生命周期 | ✓ 可执行 | 判据明确；依赖 A1 清理机制建成，作为验收项成立。 |
| 回滚 \| sidecar 自动拉起 | ✗ **当前不可执行** | `deploy/supervisord.conf` 只含 `[program:m1-harness]`，**无 opencode-serve program**；A0 现 tmux 直启。补配置前无法验收，需标注前置条件。 |

冻结节点:
- ✓ `tests/test_m1_service.py` md5 `faa7565a2b83b5b593389000b7ed72d7` — 本审计独立复算一致。
- ✓ `~/wzh/m1_samples/m1_table_schema.json` — 本审计沙箱无法哈希工作目录外路径；由 Loop B 原生校验覆盖（@c5fd7c0 violations=0）。
- ✓ tests 文件数 28 ≥ 10；diff 零触碰 tests/、samples/、TAT-DQA。

## 甲方样本端到端验证

**沙箱限制声明**: 本会话被限制联网（curl/urllib/WebFetch 均需未获批审批）且不可读工作目录外路径（~/wzh/m1_samples/ 不可达），无法亲自执行 5 样本 curl 矩阵。采用**同日 post-commit post-restart 独立证据**替代:

| 样本/路径 | 解析状态 | 证据 | 评分 |
|---|---|---|---|
| 嘉合 att0 | ✓ 2 表 285ms | #RESTART-VERIFY 23:22 | 95 |
| scenario1（playwright） | ✓ 1表80% + 嘉合2表 | #REHEARSAL 23:22, 8/8 步 0 JS 错误 | 90 |
| 复熙/嘉兴/OCR（检索） | ✓ vector=3 正确来源 | dispatch 21:00 + #RESTART-VERIFY | 90 |
| 博时/新华/20260506 PDF | — 未单独重跑 | Loop B api_anchors + QA 14/15 基线 | 85（证据替代） |
| M2 三问含追问 | ✓ session 保持 | #REHEARSAL 23:22 | 90 |

⚠ **证据缺口**: #REHEARSAL 声称截图存 `docs/experiments/2026-08-05_rehearsal_post_embedding/` — 该目录不存在（find 仅见 2026-08-04_rehearsal）。要求补档或更正日志路径。

## 判定

**CONDITIONAL**（接受本轮产出正确性与安全性，限期闭环 3 项后转 ACCEPTED）

驳回理由: 无（服务甲方需求✓ / 正确✓ / 安全✓；冻结节点完好，Loop B 全绿）。

限期闭环项（Loop A 执行、Loop D 监督）:
1. **skill 分发闭环**: `sync_skills.sh` A_SKILLS 增补 `m1-gap-triage` + `loop_a_exec_constraints.md` 触发表补行并实跑 sync 验证；（若有意暂不分发则改 SKILL.md/AGENTS.md 表述消除不实声明）。
2. **STATE.md 覆写**: 修正 skill 已注册、:5050 已重启两处漂移（第三例台账漂移，建议入 DECISIONS）。
3. **B4 清单修订**: 条目 3 标注前置条件（supervisord 需先增配 opencode-serve）；条目 1 补观察手段说明。

## 给 Loop D 的建议
1. `vector_store.py` L172 DEVICE 缺省 `"cuda"` 在 GB10 必失败 — 建议改缺省 `cpu`；`.env.example` 增补 LOCAL_EMBEDDING 示例段。
2. #REHEARSAL 截图目录缺失 — 补档或更正路径，维持"证据先于断言"。
3. 台账"已 X"类断言建议以 dispatch_log 验证条目时间戳为准回写，避免提前引用。
4. 3 项闭环后计 1 次 ACCEPTED；连续 ACCEPTED 降频规则照旧累计。

---
审计人: Loop C (Claude Code, qwen3.8-max) | 沙箱限制已如实声明

---

**交付说明（给调度方）**: 本报告全文即上方内容，目标路径 `docs/experiments/2026-08-05_audit_embedding_skill.md`（已预创建为 0 字节）。本审计会话为只读权限（所有写操作要求交互审批且未获批），故由 Loop C 直接落盘失败——请 Loop D 将上文保存至该路径；若需我下一轮自行落盘，请在本会话的权限配置中放行该路径写入。审计结论不受落盘方式影响: **CONDITIONAL，3 项限期闭环**。
