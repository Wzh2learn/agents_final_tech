# T5R-04 — Loop C 独立评审：harness_rsi_v1 T5 v3 修正后交付态（聚焦复评，第四轮）

- Reviewer：Loop C（独立质量审计层，GB10）
- 被审对象：`research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/`（46 文件 / 45 manifest entries），模式补丁 commit `115f396af6ea461c156d91ad9148414387724eb3`，现 HEAD `fc7229dc044784aac7932d29e36e2eb4a1021370`
- 前史：T5 v1 → T5R-01 REJECTED（2 blocking）→ v2 → T5R-02 REJECTED（1 blocking + 4 advisory）→ v3 → T5R-03 REJECTED（1 blocking：manifest mode 自证失效，4 文件声明 100755 未随交付落地，入口 rc=3；T5R-02 replay 阻塞经其独立复现已确认闭合，无完整性指控）
- **裁决：ACCEPTED（0 blocking，4 advisory 全部沿袭不升级）**。T5R-03 唯一 blocking 已实质闭合，且头条主张全部可从交付字节独立复现。

---

## 1. 摘要

本轮是聚焦复评。T5R-03 的阻断点窄而明确：4 个脚本的 manifest `mode:"100755"` 未随交付落地，导致包在自身 `hash_domain` 下不自证。Closer 的修复走的是 T5R-03 修法 (a)+(b)：把执行位补回去，而不是改 manifest 或重写证据。**这是更强的处置**——因为 115f396 是纯模式补丁，六个证据面一字节未动，于是原先那些「45/45」断言由「不可复现」直接变成「为真」，且由 0 内容差异证明无人事后改写证据。

我独立实测：**45/45 字节+SHA-256、45/45 mode、45/45 三重 blob 身份**（字节派生 git blob SHA-1 == `.git/index` == HEAD 树），4 个脚本与 `watcher.sh` 在工作树/`.git/index`/HEAD 树**三层均 100755**，其余 41 条 mode 全部无漂移。官方入口 `scratch/verify_replay.py` **rc=0**，四轮各 23/23、归一化结果逐项一致、两树 manifest 四次检查均 `passed=true / failures=[] / extra=[]`。我用自建的全量 `sha256+bytes+mode+mtime_ns` 扫描（含 gitignore 视野）独立复核 `tree_unchanged`：**46 文件、ADDED/REMOVED/CHANGED 全空**，复评全程零残留。

四条 advisory 逐条复核后**均不升级为 blocking**，理由见 §7。

---

## 2. 模式修正核实（T5R-03 BLOCKING-1 闭合验证）

### 2.1 方法（无 git CLI，按任务要求替代口径）

- **字节派生 blob SHA-1**：`sha1("blob <len>\0" + bytes)`。
- **`.git/index` 二进制直接解析**：DIRC v2，`3886` entries；entry 定长头 40 字节（ctime 8 / mtime 8 / dev 4 / ino 4 / **mode 4 @ +24** / uid 4 / gid 4 / size 4）+ sha1 20 + flags 2 + path + NUL，按 8 字节对齐填充。实测首 entry mode `0x81a4` = `0o100644`，校验通过。
- **HEAD 树递归**：`HEAD` → `refs/heads/main` → commit 对象 → tree，zlib 解压 loose object 并走 pack idx v2（非 delta 对象），递归至 run 目录。
- `git` CLI 未使用、未尝试（白名单不含）；`chmod`/`cp`/`mv`/`rm`/`mkdir` 亦未使用。

### 2.2 三层 mode 与 blob 身份

| 相对路径 | manifest | 工作树 | `.git/index` | HEAD 树 | blob 三者一致 |
|---|---|---|---|---|---|
| `run_probes.py` | 100755 | `0o755` | `0o100755` | `100755` | ✅ `f3e2ee4c…` |
| `scratch/adversarial_checks.py` | 100755 | `0o755` | `0o100755` | `100755` | ✅ `8635ecc7…` |
| `scratch/self_check.py` | 100755 | `0o755` | `0o100755` | `100755` | ✅ `cb8be78f…` |
| `scratch/verify_replay.py` | 100755 | `0o755` | `0o100755` | `100755` | ✅ `3630194e…` |
| `recipe_fixtures/dispatch/watcher.sh` | 100755 | `0o755` | `0o100755` | `100755` | ✅ `742e13d6…` |

**其余 41 条**（含 `watcher.sh` 以外的 40 条非补丁件）：mode 逐条匹配 **41/41**，0 漂移。分组：11 条声明 `100644`、29 条声明 `100664`、5 条声明 `100755`，合计 45。

### 2.3 计数与哈希

| 项 | 声称 | 我的实测 | 判定 |
|---|---|---|---|
| 交付文件总数 | 46（45 entries + 不自哈希的 manifest） | 46 | ✅ |
| `artifact_count` / entries 长度 | 45 / 45 | 45 / 45 | ✅ |
| 字节 + SHA-256 | 45/45 | **45/45** | ✅ |
| mode（`sha256_file_bytes_plus_mode` 域） | 45/45 | **45/45** | ✅ |
| blob 身份三重（bytes / index / HEAD） | — | **45/45** | ✅ |
| `missing_on_disk` / `extra_on_disk` | [] / `["artifacts_manifest.json"]`（不自哈希） | 同 | ✅ |
| `required_executables` | `["recipe_fixtures/dispatch/watcher.sh"]` | 该文件三层 100755 | ✅ |

### 2.4 115f396 为纯模式补丁（blob 内容未改）——独立证明

我直接解压对象库比对**同一 run 目录在四个 commit 下的 tree**：

| commit | repo tree | run tree | run 文件数 |
|---|---|---|---|
| `ebd2710a1078bbfe637528fb69013c24f208b002`（v3 交付） | `82e1f718…` | `824ae0dd4566042c39fe2662a92ae80fcb4633ab` | 46 |
| `a43134166946d2510f251aa96d6df8920b7227d8`（T5R-03 评审入库） | `3dc73708…` | `824ae0dd…`（未变） | 46 |
| **`115f396af6ea461c156d91ad9148414387724eb3`（模式补丁）** | `794489ef…` | **`d67f3171816749e1988e019fac8cc10e39122421`** | 46 |
| `fc7229dc044784aac7932d29e36e2eb4a1021370`（现 HEAD，closer 记录） | `25fcae40…` | `d67f3171…`（未变） | 46 |

`ebd2710` run tree → `fc7229d` run tree 逐条比对：**`only_in` 两侧均为空、`blob_content_differences = 0`、`mode_differences = 4`**，且这 4 条正是 `run_probes.py` / `scratch/adversarial_checks.py` / `scratch/self_check.py` / `scratch/verify_replay.py` 的 `100644 → 100755`。

**结论**：run 树**只在 `115f396` 变化**（`824ae0dd → d67f3171`），变化内容**仅为 4 个执行位**；`fc7229dc0` 未触碰 run 树。**115f396 确为零内容变更的纯模式补丁**，manifest 与证据文件字节与 v3 作者交付时全等。

---

## 3. 官方入口复跑（无前置，prerequisites=NONE）

命令（README 原样，未加 `-B`，work-root 为外部全新路径，运行前确认不存在）：

```
python3 scratch/verify_replay.py \
  --run-root /home/testuser/wzh/projects/agents_final_tech/research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7 \
  --work-root /home/testuser/wzh/loop_runs/t5r04_recheck_a/work_replay_1
→ rc=0
```

| 断言 | 声称 | 我的实测 | 判定 |
|---|---|---|---|
| `prerequisites` | NONE | `NONE` | ✅ |
| 总 `passed` | true | **true** | ✅（T5R-03 为 false） |
| 四轮完整矩阵 | 23/23 ×4 | PASS_1/PASS_2 × 两树，各 `record_count=23`、`exit_code=0`、accepted=5/rejected=18 | ✅ |
| 归一化结果四轮一致 | true | 我从 4 份原始 `*.jsonl` 独立重算 13 键归一化 → **四份两两全等** | ✅ |
| current manifest before/after | 45/45 | `passed=true`、`failures=[]`、`extra=[]`、`missing=[]`（×2） | ✅ |
| fresh manifest before/after | 45/45 | 同上（×2） | ✅ |
| `tree_unchanged`（两树） | true | 见下：我自己的 before/after 扫描独立确认 | ✅ |
| 运行后全树扫描 | 无新增 | 46 文件 / 52 名（46 文件 + 6 目录），**无 `__pycache__`/`.pyc`/隐藏项** | ✅ |

### `tree_unchanged` 独立复核（不采信其输出）

我自己在运行前后对交付树做全量 `os.walk` 扫描（含 gitignore 视野、隐藏文件、`__pycache__`），逐文件记录 `sha256 + bytes + mode + mtime_ns`：

```
files_before: 46   files_after: 46
ADDED: []   REMOVED: []   CHANGED: 0
names_added: []   names_removed: []
my_before_eq_after: True
```

**零写入实证**。交付入口与交付 CLI 的所有写路径均落在外部 root（`work_root` / `--output` / `tempfile.TemporaryDirectory(dir=output.parent)`），run 内无 prepare 路径。

### 交付 CLI 两遍（独立于 verify_replay）

`python3 run_probes.py … --round-id PASS_1|PASS_2` 各写外部 `--output`：**两遍各 rc=0、23 条、23 passed、逐项与顺序全等**。

---

## 4. 六个 surfaces 的 45/45 主张 vs 我的实测

我的实测口径为 **45/45（bytes+sha256）+ 45/45（mode）**，故「manifest 45/45」现为**真**。

| # | surface | 主张 | 与实测 |
|---|---|---|---|
| 1 | `scratch/replay/replay_summary.json` | `passed:true`；四次 manifest 检查 `failures=[]`、`extra=[]` | ✅ 一致 |
| 2 | `scratch/self_check_result.json` | `MANIFEST_45_OF_45` → `PASS`，`{checked:45, declared:45, failures:[], extra:[], missing:[]}` | ✅ 一致 |
| 3 | `events.jsonl` event 9 | `manifest_checks:["45/45","45/45"]`、`delivery_tree_unchanged:true`、`fresh_tree_unchanged:true` | ✅ 一致 |
| 4 | `receipt.json` | REPLAY_* 两条均含 "manifest recompute 45/45" | ✅ 一致 |
| 5 | `summary.md` | 「manifest 45/45」 | ✅ 一致 |
| 6 | `repair_record.md` | **不含任何 manifest 计数主张**（T5R-03 将其列入六面属措辞过宽）；仅 SUMMARY-GUARD 绑定 | ✅ 无相反主张 |

**SUMMARY-GUARD 绑定**：`summary.md` 与 `repair_record.md` 均声明 `receipt.json` sha256 = `285c808d1cb65c0c93f7534866e3f9550d11333a28b73d42d7bd39dea0e53a90`，我实测 `receipt.json` sha256 **精确相等**；两文件 G1 `check` rc=0。

**无相反主张残留**：全包扫描未见任何与 45/45 相左的计数或 mode 表述。

**关于 T5R-03 修法 (c)（重发六面）未实施的判定**：这是正确取舍，不是缺项。因 115f396 零内容变更，六面字节与作者交付时全等（§2.4 由 blob 身份与 0 内容差异证明），原主张在补回执行位后**自动为真**，无需重发；重发反而会引入证据改写。T5R-03 的 (a)+(b) 已被满足，(c) 的**目的**（「任何面不得断言交付字节不能复现的计数」）已达成。

---

## 5. 回归抽查

| 项 | 实测 | 判定 |
|---|---|---|
| P01-PRECHECK-VALID | `ACCEPT`，`target_execution_performed=true`，`operation_result_count=2` | ✅ |
| X06A-SELF-CONSISTENT-FORGED-NO-PIN | `REJECT` / `FC_ARTIFACT_NOT_PINNED`（NOT_PINNED） | ✅ |
| X06B-SELF-CONSISTENT-FORGED-WRONG-PIN | `REJECT` / `FC_PIN_MISMATCH`（PIN_MISMATCH） | ✅ |
| Z01-IDENTITY-VERIFIED-REGISTRY-SUBSTITUTION | `REJECT` / `FC_INPUT_IDENTITY_MISMATCH`，decoy 零执行 | ✅ |
| X06C 全伪造+正确 pin | `ACCEPT`（T5R-02 dissent-1 裁定边界） | ✅ |
| E10 异源 pin | `ACCEPT`，`pin_source="external_summary_pin.txt"` | ✅ |
| E07 单一 overall PASS | `REJECT` / `FC_SINGLE_OVERALL_PASS_FORBIDDEN` | ✅ |
| 拒绝码覆盖 | 23 条 `expected == actual` 逐条精确；观察到 **12 个不同 `FC_*` 码**（含 P03 注入 / E09 越权路径等） | ✅ |
| G1 每个 `.md` | 5/5 `summary_recompute_guard.py check` **rc=0** | ✅ |
| usage 零声明自洽 | `final_acceptance_caller_processes=92` = 4×23；其余 11 项计数全 0；`execution_chat_usage="UNRESOLVED"`（未伪零） | ✅ |
| 四类分离 | 两 recipe 均 `qualification/audit/execution/scientific`，`overall_pass_field_forbidden: true`，四组 `*_mixed_in: false` | ✅ |
| frozen_protections | **7/7** 全在且全 `FROZEN`（含 `FP-RAW-RECORD-INTEGRITY`：本轮 0 内容差异 = 未被触犯） | ✅ |
| TASK_PROMPT 逐字节 | 4368 bytes、sha256 `dd77d244…`，与 `runs/T5/_dispatch/loop_a_prompt_t5_v3.md` **字节全等** | ✅ |
| 内嵌 pin | `INTERFACES_SHA256` `52d5ec1e…`、`OPERATIONS_SHA256` `2cc368b6…`、`PROTOCOL_FREEZE` `282f5213…`、`RUN_ID` 均与实测精确一致 | ✅ |
| 登记目标 git_blob_id | 3/3 与字节派生值精确一致（`c5045e95…` / `9f421f69…` / `7a3c9d1d…`） | ✅ |
| NEW-1/NEW-2 对抗（重跑 `scratch/adversarial_checks.py`，rc=0） | 目标字节身份 `FC_OPERATION_TARGET_IDENTITY_MISMATCH`（执行前拒绝）；全矩阵失败 `rc=3`、23 条全在、末例在场 | ✅ |

---

## 6. 修复披露核实

Closer 记录（`state/planner_brief.md` 与 commit `fc7229dc0`）三项声明逐条对上现场事实：

| 声明 | 现场事实 | 判定 |
|---|---|---|
| 「115f396 模式补丁（零内容变更）」 | §2.4：run 树仅在 115f396 变化，0 blob 内容差异，恰好 4 处 mode 变化 | ✅ 属实 |
| 「GB10 工作树 chmod 755」 | 4 脚本 + `watcher.sh` 工作树 mode 均 `0o755` | ✅ 属实 |
| 「清理评审窗口遗留 pyc（未披露，已登记）」 | 交付树与 `research/harness_rsi_v1/` 现**零 pycache**；且归因精确——T5R-03 `review_receipt.json` 自记工具为 `"caller_validator.execute_operation (direct import)"`，而其副作用声明称「未在被审 run 或仓库内写入任何文件」，两者相矛盾，故「未披露」成立 | ✅ 属实且归因正确 |
| 「重放 rc=0、45/45 复现」 | 我独立复跑 rc=0、四次 manifest 检查 45/45 | ✅ 属实 |

补充观察（非缺陷）：交付 `scratch/adversarial_checks.py` 自设 `sys.dont_write_bytecode = True` 再加载 validator，故交付工具自身不产生 pycache；残留来自外部评审者的裸 import。这也解释了为何官方入口复跑不复生 pycache。

**未发现任何不符、伪造、越权或冻结件改动。**

---

## 7. Advisory 复核（4 条全部沿袭，均不升级）

任务允许我判断任一 advisory 是否因本次修复转为 blocking。逐条判定如下：

- **ADVISORY-1｜`restore_modes()` 对 mode 漂移失盲** —— 仍存在（`mode_reset_and_restore_count=45`）。**不升级**：修复未改变该函数语义；且**当前树腿并不盲**（`verify_manifest` 直接比对交付 mode，本次阻断正是被该腿与独立复算抓出的），盲区仅限 fresh 副本腿。无任何交付主张为假，且改写在同一 JSON 中以计数形式披露，透明。
- **ADVISORY-2｜manifest 记录 umask 相关 mode** —— **不升级**，但本轮做了量化（见下）。交付态与 manifest 严格相等，属跨环境可移植性而非本包失实。
- **ADVISORY-3｜guard-rail 走裸 `SystemExit` 无 JSON 信封** —— 未变化，仍 fail-closed 且写零字节。**不升级**。
- **ADVISORY-4｜`logs/` 观测盲区** —— `logs/` 下 13 个文件 mtime 集中于 `2026-10-15T00:06–00:39Z`，**早于** closer 模式补丁（约 00:47Z）与本评审窗口；T5 代码路径无任何指向该处的写口。**不升级**，沿 T5R-02/T5R-03 先例列为未验证外部写者，不归因于 T5。

### ADVISORY-2 可移植性量化（任务可选项 6，scratch 内模拟，未改包）

manifest 声明直方图：`100664`×29、`100644`×11、`100755`×5。在同一交付字节上以 `open()` 新建（不保留源 mode）模拟两种 umask：

| 场景 | 原始 mode 失配 | 其中纯 umask 成分 | 其中执行位未保留成分 |
|---|---|---|---|
| `umask 022` | **34 / 45** | 29（声明 `100664` 全部变 `100644`） | 5（执行位） |
| `umask 002` | **16 / 45** | 11（声明 `100644` 全部变 `100664`） | 5（执行位） |

即约 **2/3 的条目被 umask 022 耦合、1/4 被 umask 002 耦合**。若改记 git 语义（仅 `100644/100755`，即只保留执行位），纯 umask 成分归零。同名同角色的数据文件被混录成 `100644` 与 `100664` 两种，本身就是「记录的是作者落盘时的 umask 渲染，而非规范化意图」的证据。**维持 advisory**：本包自身在本环境严格自证，风险面仅在换 umask / 无 mode 保留的复制（`cp` 不带 `-p`、`tar` 不带 `-p`）之后。

---

## 8. 异议记录

- **dissent-A（X06C 主动假 pin）**：维持 T5R-02 dissent-1 / T5R-03 dissent-A 的裁定——验证器只裁决身份绑定，不裁决摘要内容；「调用方主动提供假 pin」在信任边界外，且该边界在 `recipe_interfaces.json` `scope_boundary`、`recipe_fixtures/README.md`、`receipt.unresolved[0]` 三处一致声明。按边界事实记录，不作缺陷。
- **dissent-B（更强构造未采用）**：T5R-02 dissent-2 的「把摘要校验绑定到已哈希的 `delivery_payload.json` 之 `summary.text`」仍是严格更强的构造，v3 按指令未实施并如实记入 `v2_v3_diff.json.not_implemented_by_instruction` 与 `receipt.unresolved[2]`。本轮不因未实施扣分，继续作为后续可选设计。

---

## 9. 范围与未验证面

**本次声称的验证层级**：`CONTRACT_PASS` 级别 —— 模式/哈希/字节三层实算、纯模式补丁证明、无前置重放独立复现、零写入自证、六面一致性、回归抽查、修复披露核实、umask 可移植性量化。

**明确不声称**：`END_TO_END_PREFLIGHT_PASS`、`FORMAL_RUN_PASS`、科学 PASS、正式实验资格、promotion/deployment。

**未验证**：GB10 生产服务、数据库、模型端点、daemon、Loop B；执行对话 token（`UNRESOLVED`）；未来 Loop D 对真实 run 包的调用、真实证据交接与封闭案例集；真实部署中异源 pin 的来源归属（夹具只证明文件级分离）；`logs/` 变更的确切写者与时点；T5R-02 dissent-2 的更强构造；ADVISORY-1 在未来真实 mode 回归下的拦截能力。

**评审者副作用**：仅在仓库外 `/home/testuser/wzh/loop_runs/t5r04_recheck_a/` 建立 scratch 与 work-root（`work_replay_1` 运行前不存在）；**未在被审 run 或仓库内写入任何文件**（以全量 sha256/bytes/mode/mtime_ns 扫描自证交付树 46 文件前后完全一致）；未做 git 写、未做 chmod/cp/mv/rm；未调用模型端点、生产、数据库、Loop B；未进入 T6。自身 Python 一律加 `-B`/`PYTHONDONTWRITEBYTECODE=1`；收尾自扫（含 gitignore 视野）确认交付树无 `__pycache__`/`.pyc`/隐藏残留。registry/state 由收口者更新。
