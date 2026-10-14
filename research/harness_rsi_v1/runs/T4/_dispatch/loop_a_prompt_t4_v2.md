# Loop A 任务：T4 v2 返工 —— 夹具可提交性修复 + 全套包件再生成（supersedes v1；执行 + 完成前自检；单轮强评审预算）

你是 Loop A（GB10 上的 Codex CLI 执行层）。本任务是 T4 v1 run（`runs/T4/20261014T174628Z_2cc25c92`）的**返工版本**。任务卡 `cards/T4.md` 与科学范围不变；唯一返工动机 = v1 包无法通过仓库 pre-commit 守卫（详见下）。

## v1 阻断事实（必须先读）
- 本地对 v1 做提交时，仓库 pre-commit 链的"收据块守卫"（`scripts/graph/hooks/summary_recompute_guard.py` + `summary-recompute-guard.precommit.sh`）拒绝并硬阻断：`[summary-guard] FAIL 校验失败: request_count = 4 (声称满足 3)`。原因是 `fixtures/summary/effect_mismatch.md` 内嵌的收据块与其工件 `effect_artifact.json` 为**故意失配**（这正是该夹具的用途），守卫将其判为"声明与存储工件不一致"，拒绝入库。
- 仓库内既定模式（先读 `tests/test_guard_sentinels.py` 头部说明与 `tests/fixtures/guard/` 哨兵为参照）：
  - **仓库内落盘的 .md 收据夹具必须全部通过守卫复算**（deliberately NON-poisonous，避免"自己的未来提交被自己阻断"）；
  - **失配（tampered/mismatched）变体必须"runtime 派生"**：在运行时生成到临时/派生区，随工具输出留证，不得持久化为 .md 落盘；
  - 原因（仓库原文）：无任何针对夹具的豁免机制——"A repo-resident mismatched .md would be permanently rejected by the very guard it is meant to test"。
- 结论：v1 不可提交；v1 保留在两机磁盘（不进 git）作为前史（其锚点：manifest sha256 `8ef43aec8974ca4bf94931df14c138620ae02a9a9114c78138cf2c3f0dfb48af`；receipt sha256 `f270cab1177dc293ca0b94c21132e3dcdc70f2514e3e5cf4a71fc030e7691dbd`）。**v2 的硬要求：包内任何 `*.md` 都能通过守卫复算。**

## v2 唯一必须变更的内容
1. **summary 夹具合规化改造（核心）**：
   - 不得在 v2 包内任何"会提交"的路径存放"故意失配"的 .md（包括 scratch 下）。
   - 失配场景改为 **runtime 派生**：推荐 = 存放一个本身能通过守卫的基底件 + 一个小的派生脚本（如 `derive_case_mismatch.py`），运行时以代码化变换生成失配变体（例：把某 claim 从匹配值改为不匹配值），在 scratch 内对派生件执行守卫并记录 FAIL 输出日志；派生件本体不落盘（以派生脚本 + 输出日志 + 派生件 sha256 留证）；如坚持保留派生件本体，只允许非 `.md` 扩展名并附说明。
   - 现有 4 个 `*_match.md` 与 `usage_no_block.md` 的等价设计可保留（它们能过复算），但所有收据块内的 `artifact:` 引用必须改为 **v2 run 内路径**（禁止引用 v1 路径——v1 不进 git，且未来 clone 中不存在）。
   - 语义保持：该组合仍需证明"守卫能抓住预算/效果类声明失配"（对应原 v1 的 INC-13 相邻映射），预期防御行为不变。
2. **受影响组合重跑**：对全部适用 (工具, 案例) 组合做两轮重跑（至少覆盖 summary 相关组合；建议全量 11 组合），重生成 `scratch/tool_outputs/` 证据与 `baseline.json`、`baseline_recipe.json`。
3. **全套包件再生成**（新 run_id；全量重建而非补丁）：`adapters/`、`fixtures/`、`baseline.json`、`baseline_recipe.json`、`receipt.json`（新增 `supersedes` 字段：v1 run_id + 返工原因 + v1 保留方式）、`summary.md`、`artifacts_manifest.json`、`events.jsonl`、`TASK_PROMPT.md`。
4. **不得改变**：案例→检查映射语义；适配器对旧工具的路由范围（除 summary 适配器为支持派生流程所需的最小调整——在适配器 README 记录变更）；结论口径与未验证面处置。若全量重跑后画像与 v1（detected 6 / missed 2 / not_applicable 2 / unverified 6）不一致，如实记录差异并分析，不得为对齐粉饰。

## 完成前自检（硬性；保留 v1 全部自检项，并新增 G1/G2/G3）
- **G1（新）**：对 v2 包内每个 `*.md` 逐个运行 `python3 scripts/graph/hooks/summary_recompute_guard.py check <path>`，**全部 rc=0**；输出矩阵写入自检记录。这是本地提交时守卫将对 staged blob 执行同类复算的前提。
- **G2（新）**：全包扫描：不存在任何"含失配收据块"的 `.md`；不存在行首收据 opener 的失配项；派生失配件仅以运行期/非 `.md` 形式存在或完全不留本体。
- **G3（新）**：v2 与 v1 的结果差异表（应当零差异，或逐项给出解释）。
- 原有 A1/A2/A3/A-common、两轮一致性、哈希重算、写入边界、B0 计数：全部保留。
- 自检发现问题必须修到干净再交付；修复记录写入 receipt.self_check。

## 约束（与 v1 相同，重申）
- 写入所有权：仅 `runs/T4/<v2 run_id>/`；run_id = UTC `YYYYMMDDTHHMMSSZ` + `_` + UUID 前 8 位，已存在换新；不覆盖；不做 git commit/push；不改任何其他文件。
- B0：零模型/网络/远程/生产/数据库/训练调用；零自动重试；执行对话 token 不可计量写 UNRESOLVED。
- **不得以降级验证面来"过守卫"**：不许删除案例、不许放宽检查、不许丢失证据；派生脚本、命令与输出日志必须完整可复核。
- 停止条件同 v1：输入漂移、权限不明、需越界访问、需联网/模型/生产、预算不可计 → STOPPED，保留证据如实报告。

## 交付回复（简短）
v2 run 目录绝对路径；G1/G2/G3 结论；A1/A2/A3/A-common 与两轮一致性结论；v1↔v2 差异表；未验证面与 UNRESOLVED；阻断（若有）。
