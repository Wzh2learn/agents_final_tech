# GB10 production 对齐可行性实测（决策 1 与决策 2 同根因；只读，未执行）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代任何既有报告；把 `memory/THREADS.md` 里「三选项」的定性描述升级为可执行定量方案
> 用途: 用只读实测把「GB10 production 对齐」从三个待定选项变成一条**已核验安全、可立即执行**的确定流程，并证明 Loop B 连续 FAIL 与它是**同一个根因**。
> 边界: **本件不执行任何对齐动作**——未 pull、未 commit、未 merge、未 push、未 checkout/reset/stash/clean production；GB10 production 全程停在 `e5ab809`、5 个脏件不变。裁定权在用户。

## 1 结论摘要

1. 已提交内容是**纯 fast-forward**：production `e5ab809` 是 `origin/main`（`f0fdda8`）的祖先，落后 **21**、领先 **0** ⇒ production 无独有提交，不存在丢提交风险。
2. 5 个脏件中**只有 1 个**与来件路径相交（`logs/graph/dispatch_log.md`）；其余 4 个来件完全不碰 ⇒ 不构成阻碍。
3. 该文件两边都是**纯尾部追加、零删除**，且基线版本是两边工作副本的**精确前缀**；两侧新增行**零重叠**（0/36 与 0/15）⇒ 并集机械可构造，**无任何证据会被覆盖或语义丢失**。
4. Loop B 最新周期 `2026-09-24T03:40:51` 的 9 项检查里**只有 `git_alignment` FAIL**，其余 8 项全 PASS ⇒ **决策 2 不是独立问题，对齐即清除唯一失败项**。
5. 来件 29 条路径**不含任何 `scripts/` 与 `src/`** ⇒ `loop_b_verify.sh`、daemon `1816933`、`:5050` `1868428` 均不受影响，**对齐不需要重启任何服务**。
6. 唯一**不使用破坏性命令**的可执行路径 = 先在 production 提交那 36 行，再 merge `origin/main` 并手工解尾部并集（§5）。git 不会在相交脏件存在时允许 FF，而 `checkout`/`reset`/`stash`/`clean` 一律禁用。

## 2 拓扑实测

| 项 | 实测值 | 取法 |
|---|---|---|
| production HEAD | `e5ab809` | `git rev-parse --short HEAD` |
| origin/main | `f0fdda8` | fetch 后 |
| 落后 / 领先 | **21 / 0** | `git rev-list --count` 双向 |
| 是否祖先 | **是**（⇒ 已提交内容纯 FF） | `git merge-base --is-ancestor HEAD origin/main` |
| production 脏件数 | **5** | `git status --porcelain` |
| 来件改动路径数 | **29** | `git diff --name-only HEAD..origin/main` |
| 脏件 ∩ 来件 | **1** = `logs/graph/dispatch_log.md` | `comm -12` 两个排序集合 |

不相交的 4 个脏件（来件不碰，FF/merge 均不受影响）: `config/schema_suggestions.json`、`logs/graph/docs_lint_report.json`、`logs/graph/governance_drift_latest.md`、`logs/graph/verify-report.json`。

## 3 `dispatch_log.md` 两侧的追加性质与不相交性

| 版本 | 行数 | 相对基线 | 基线是否为其精确前缀 |
|---|---|---|---|
| 基线 `e5ab809` | 1115 | — | — |
| 上游 `origin/main` | 1130 | **+15 / -0** | **是**（逐字节 `diff -q` 通过） |
| production 工作副本 | 1151 | **+36 / -0** | **是**（逐字节 `diff -q` 通过） |

不相交性双向实测:

- 上游新增 15 行中，出现在 production 新增 36 行里的 = **0**
- production 新增 36 行中，出现在上游完整版本（1130 行）里的 = **0 / 36**（逐行 `grep -Fxq` 全串精确匹配）

⇒ 并集行数 = 1115 + 15 + 36 = **1166**，两种排序均不丢任何一行。

### 3.1 这 36 行是什么（18 天运行证据）

全部为 `#LOOP-B-FLIP` 记录，时间跨度 **09-06 14:53 → 09-23 11:11**，36 个**互不相同**的时间戳，格式 `[MM-DD HH:MM]`（**无 `UTC` 后缀**，与上游 Loop D 条目的 `[MM-DD HH:MM UTC]` 格式不同）。首尾实例:

```text
[09-06 14:53] #LOOP-B-FLIP overall FAIL -> PASS (head=39307d4; ...)
[09-06 19:21] #LOOP-B-FLIP overall PASS -> FAIL (head=39307d4; ...)
[09-22 22:33] #LOOP-B-FLIP overall PASS -> FAIL (head=3dabbc7; ...)
[09-23 00:12] #LOOP-B-FLIP overall FAIL -> PASS (head=d351d7e; ...)
[09-23 11:11] #LOOP-B-FLIP overall PASS -> FAIL (head=e5ab809; ...)
```

这些是 Loop B daemon 自身写下的翻转历史，**上游零命中**，一旦用破坏性命令清掉即不可再生 ⇒ 必须先落盘再对齐。

## 4 排序约定：为什么用尾部并集而不是按时间插入

该文件**本来就不是严格时间序**——上游自己新增的 15 行里就存在逆序（`06:10` 之后接 `04:43`、`05:06`），说明它一直是**多写者追加式尾部日志**，而非排序时间线。

⇒ **尾部并集符合既有约定**；按时间戳交错插入反而是**改写历史行序**，风险更高且违反 append-only 纪律，**不建议**。

推荐序 = **上游 1130 行作前缀 + production 36 行接尾部**。这样结果文件的前 1130 行与 `origin/main` 的版本**逐字节相同**，即已提交历史保持为精确前缀，本地运行记录留在尾部，可追溯性最好。

## 5 唯一不使用破坏性命令的执行流程（待授权，本件未执行）

```text
# 0) 前置：已有只读备份 /tmp/prod_dl.md（1151 行全量）与 /tmp/prod_added.txt（36 行）
#    建议另做一份仓外持久备份，/tmp 非持久
# 1) 在 production 提交那 36 行（逐路径 add，禁 -A / --amend / --no-verify）
git add -- logs/graph/dispatch_log.md
git commit -m "chore(loop-b): 落盘 09-06..09-23 的 36 条 LOOP-B-FLIP 运行记录"
#    此时 production = 领先 1 / 落后 21
# 2) 合并上游（会产生尾部冲突，属预期）
git merge origin/main
# 3) 手工解冲突为尾部并集：基线 1115 行 + 上游 15 行 + 本地 36 行 = 1166 行
#    解完必须机械核验（见 §6），不得目视了事
# 4) 提交合并，push，然后核 Loop B 下一自然周期是否转 PASS
```

为什么不能走更短的路: production 领先 0 本可纯 FF，但 `dispatch_log.md` 是**相交脏件**，git 会拒绝在本地修改可能被覆盖时执行 FF/merge；而清除脏件只能用 `checkout --` / `reset` / `stash` / `clean`，**四者均被纪律明令禁止**。故必须先提交、再合并。

## 6 执行后的机械核验清单（授权后必须逐条给数）

1. 行数 = **1166**；`git diff --numstat` 对合并结果的增删如实报。
2. 前 **1130** 行与 `origin/main:logs/graph/dispatch_log.md` **逐字节相同**（`head -n 1130 | diff -q`）。
3. 后 **36** 行与 `/tmp/prod_added.txt` **逐字节相同**（`tail -n 36 | diff -q`）。
4. 36 个 `#LOOP-B-FLIP` 时间戳**一个不少**（`grep -c` = 36，且 `sort -u` 后仍 36）。
5. 上游 15 条 Loop D 条目**一个不少**。
6. 文件末字节为换行；无 `\r\r\n` 双 CR（该文件为 CRLF 行尾，追加须用二进制 `newline=''` 写，历史上踩过一次双 CR 坑）。
7. 其余 4 个脏件**内容未变**（逐个 sha256 与对齐前比对）。
8. daemon `1816933` 与 `:5050` `1868428` 的 `lstart` **未变**；crontab 未变（当前仅 1 条 `governance_drift_scan.py --cron`，每日 03:30）。
9. Loop B **下一自然周期**转 `overall=PASS` 且 `git_alignment=PASS`；不得手工重置或改 crontab 催它。

## 7 Loop A / B / C 组织面现状（本轮只读核实）

- **Loop A**: **无** `~/.jinrong-loop-a` 控制面；无 Loop A 进程在跑；`:4096` OpenCode sidecar 在线（PID `3153507`，lstart 08-24 23:50:55，已 30 天）⇒ 派发前需先建控制面或按批派工，且**派发即产生模型调用**，须先定预算与 canary（决策 46 口径）。
- **Loop B**: daemon `1816933` 连续运行 11 天；最新周期 `2026-09-24T03:40:51` = `overall FAIL`，9 项检查中**仅** `git_alignment` FAIL，`frozen_nodes`/`pytest`/`api_anchors`/`qa_canary`/`docs_lint`/`model_topology`/`agent_watchdog`/`pg_pool_guard` **全 PASS**，`head_commit=e5ab809`。
- **Loop C**: `~/.jinrong-loop-c` 已安装，无 STOP、`ACTIVE.json={}`、state `IDLE`；队列 6 = 2 READY / 4 BLOCKED；`base_commit` 仍是 `e5ab809`。
  - `LC-GOV-002`（治理图与归档候选盘点）虽 READY，但其 `stop_conditions` 明含 **"Loop B not aligned"** ⇒ **被决策 1 直接卡住**，对齐后才可派。
  - `LC-RESEARCH-001` 另有卡片自相矛盾（决策 7），且 `forbidden_paths` 含 `paper/*` 与 `research/*`。
  - 两张 READY 卡的 `model` 均为 `mimo-v2.6-flash` ⇒ 派发即模型调用，同样受预算与 canary 约束。

⇒ **对齐 production 是当前唯一的单点解锁项**：它同时清除 Loop B 的唯一失败项、解除 `LC-GOV-002` 的停止条件、并让 Loop C 的 `base_commit` 前移到 `f0fdda8`。

## 8 红线自查

- 全程**只读**：未 pull、未 commit、未 merge、未 push、未 checkout/reset/stash/clean production；production 仍 `e5ab809` + 5 脏件。
- 未重启 daemon 与 `:5050`，未改 crontab，未动任何生产端口，未连业务端点。
- 零模型调用、零 canary、零 judge、零起 run；未派发任何 Loop A/B/C 卡。
- 未改冻结判据/阈值/oracle/冻结 hash；未解 `DATA_NO_GO`；未启动 Phase 1a/2；未授权训练或端点。
- 未动 `docs/33`、`docs/34`；四件用户资产零触碰。
- 中间产物只落 GB10 `/tmp`（仓外，不 commit）: `/tmp/base_dl.md`、`/tmp/up_dl.md`、`/tmp/prod_dl.md`、`/tmp/up_added.txt`、`/tmp/prod_added.txt`。`/tmp` 非持久，故 §3 的关键数字与 §6 的核验清单全部写进本件，授权后可据此复核。
