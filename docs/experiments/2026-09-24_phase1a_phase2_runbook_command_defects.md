# Phase 1a / Phase 2 执行手册的命令级缺陷：10 行文档命令中 6 行实测即失败

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代 `DATA_NO_GO` 报告与唯一执行计划；**指出两者的 GB10 命令块需要更正**（本件不改它们一个字节）
> 用途: 数据到货那天，验收人员会**逐字照抄**这两份文档里的命令块。本件把每一行**原样跑一遍**并记录真实退出码，以免验收在第二行就失败。
> 边界: 全程只读。未改 `DATA_NO_GO` 报告、未改唯一执行计划、未改任何代码或判据；未解 `DATA_NO_GO`；未启动 Phase 1a/2；未读取任何私有数据（用不存在的路径触发 fail-closed，不看内容）。

## 1 方法

在 GB10 隔离 worktree `agents_final_tech_accept_0caf6dd`（clean，HEAD `0caf6dd`）内，把两份文档命令块里的 **10 行命令逐字原样执行**，每行单独取真实退出码（**重定向后直接取 `$?`，不接管道**，以免 `head`/`tail` 的退出码冒充命令退出码——这个坑本件第一次试就踩到，已改）。

两份来源：

- `docs/experiments/2026-09-23_phase1a_data_no_go.md` 的 “GB10 acceptance after connectivity is restored” 块与 “Phase 1a learnability probe after independent acceptance” 块
- `docs/archive/2026-10-20_entry_consolidation/2026-09-22-paper-research-next-phase.md` §Phase 2 的命令块（该件自称「唯一下一阶段执行计划」）

## 2 逐行实测结果

| # | 出处 | 文档命令（逐字） | 实测 rc | 判定 |
|---|---|---|---|---|
| 1 | DATA_NO_GO / acceptance | `python3 -m py_compile research/phase1a_data_contract.py` | **0** | OK |
| 2 | DATA_NO_GO / acceptance | `PYTHONPATH=src python3 -m pytest tests/test_phase1a_data_contract.py -q` | **1** | **FAIL** — `/usr/bin/python3: No module named pytest` |
| 3 | DATA_NO_GO / acceptance | `python3 research/phase1a_data_contract.py --package-root … --output …` | **2** | **OK** — 2 正是该件自己文档化的 `DATA_NO_GO` 退出码（报告 :68 “`DATA_NO_GO` (exit 2)”），脚本正常跑完并输出 `status: DATA_NO_GO`、`endpoint_calls 0`、`socket_attempts 0`。**不是缺陷，勿误改** |
| 4 | DATA_NO_GO / learnability | `python3 -m py_compile research/phase1a_learnability_baselines.py` | **0** | OK |
| 5 | DATA_NO_GO / learnability | `PYTHONPATH=src .venv/bin/python -m pytest tests/test_phase1a_learnability_baselines.py -q` | **127** | **FAIL** — `.venv/bin/python: 没有那个文件或目录` |
| 6 | DATA_NO_GO / learnability | `env PYTHONPATH=. .venv/bin/python research/phase1a_learnability_baselines.py --package-root … --precheck-report … --acceptance-receipt … --config … --output …` | **127** | **FAIL** — 同上 |
| 7 | 计划 / Phase 2 | `python3 -m py_compile research/phase2_rule_gate_replay.py research/paper_result_views.py` | **0** | OK |
| 8 | 计划 / Phase 2 | `PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_phase2_rule_gate_replay.py -q` | **127** | **FAIL** — 同上 |
| 9 | 计划 / Phase 2 | `env PYTHONPATH=. .venv/bin/python research/phase2_rule_gate_replay.py --dataset … --config … --output …` | **127** | **FAIL** — 同上 |
| 10 | 计划 / Phase 2 | `env PYTHONPATH=. .venv/bin/python research/paper_result_views.py --phase2-report … --output …` | **127** | **FAIL** — 同上 |

**汇总：10 行中 4 行可用（3 个 `py_compile` + 1 个合同运行，其 rc=2 属正确行为），6 行失败（1×rc=1、5×rc=127）。**

两个失败类，各自都是**全类失败**：

- **全部 3 个 pytest 行都跑不起来**（1 行 rc=1 + 2 行 rc=127）。⇒ 文档所要求的「focused suite passes」这条验收前提，照文档执行**无法被满足**，验收人员会在第一步就卡住。
- **全部 5 个 `.venv/bin/python` 行都是 rc=127**。

## 3 根因（两条，互相独立）

### 3.1 `.venv` 在 GB10 上不存在；真实路径是 `venv`（无点）

```text
ls -d ~/wzh/projects/agents_final_tech/.venv        -> 不存在 (ls rc=2)
ls -d ~/wzh/projects/agents_final_tech/venv         -> 存在
ls -d ~/wzh/projects/agents_final_tech_accept_0caf6dd/venv -> 不存在（worktree 内无 venv）
.venv/bin/python --version                          -> rc=127
venv 解释器版本                                      -> Python 3.12.3
```

**附带一个必须写进更正的细节**：`venv/` **只存在于 production 检出**，隔离 worktree 内没有。而安全门文档 §6.2 已规定实验必须在隔离 worktree 内跑、且 `venv/` 用 production 解释器的**绝对路径**调用。⇒ 正确写法在 worktree 内必须是绝对路径 `~/wzh/projects/agents_final_tech/venv/bin/python`，相对写法 `venv/bin/python` 只在 production 检出内成立。文档现在两个都不对。

### 3.2 裸 `python3` 没有 pytest

```text
python3 -c "import pytest"  -> rc=1, ModuleNotFoundError: No module named 'pytest'
```

`python3` 能跑 `phase1a_data_contract.py`（该模块纯 stdlib，故第 3 行 rc=2 是正常业务退出码），但**跑不了任何 pytest 行**。同一份 `DATA_NO_GO` 报告内部还自相矛盾：acceptance 块用 `python3`，learnability 块用 `.venv/bin/python`，**两个都不是真实的 `venv/bin/python`**。

## 4 标志位是对的，别去「顺手修」（重要精度声明）

四个脚本的 argparse 与文档所写**逐一相符**，缺陷**只在解释器与环境变量**，不在标志位：

| 脚本 | 真实 CLI（`--help` 实测） | 与文档是否一致 |
|---|---|---|
| `phase1a_data_contract.py` | `--package-root`(必填) `[--manifest]`(可选) `--output`(必填) | 一致 |
| `phase1a_learnability_baselines.py` | `--package-root --precheck-report --acceptance-receipt --config --output`（全必填） | 一致 |
| `phase2_rule_gate_replay.py` | `--dataset --config --output`（全必填） | 一致 |
| `paper_result_views.py` | `--phase2-report --output`（全必填） | 一致 |

## 5 `PYTHONPATH` 的实测结论（文档三处写法互不相同，且大多不必要）

文档里出现三种写法：`PYTHONPATH=src`、`PYTHONPATH=src:.`、`PYTHONPATH=.`。实测：

```text
venv/bin/python -m pytest tests/test_phase1a_data_contract.py -q          -> rc=0, 31 passed   (无任何 PYTHONPATH)
venv/bin/python -m pytest tests/test_phase2_rule_gate_replay.py -q        -> rc=0, 22 passed   (无任何 PYTHONPATH)
venv/bin/python -m pytest tests/test_phase1a_learnability_baselines.py -q -> rc=0, 29 passed   (无任何 PYTHONPATH)
venv/bin/python research/phase1a_data_contract.py --help                  -> rc=0              (无任何 PYTHONPATH)
venv/bin/python research/paper_result_views.py --help                     -> rc=1  ModuleNotFoundError: No module named 'research'
env PYTHONPATH=. venv/bin/python research/paper_result_views.py --help    -> rc=0
```

⇒ 结论三条：

1. 三个 pytest 行与 `phase1a_data_contract.py` **完全不需要 `PYTHONPATH`**（合计 **82 passed**，零 PYTHONPATH）。
2. **只有 `paper_result_views.py` 需要 `PYTHONPATH=.`**（它在 :15 `from research.phase2_rule_gate_replay import …`）。缺了就 rc=1。
3. `src` **对这四条命令毫无作用**：`grep` 实测 `research/` 与这三个测试文件内**零处** `from src` / `import src` / `from src.`。

### 5.1 为什么建议直接删掉 `PYTHONPATH=src`（不只是「无用」）

`src/` 内是**生产代码**：`agents`、`auth`、`biz`、`main.py`、`mcp_server`、`storage`、`tabular_mcp_server`、`tools`、`utils`。把它挂上导入路径，等于在**以「零端点」为核心主张**的运行里，让生产服务模块变成可导入状态。

如实界定影响：这些脚本当前**并不 import** 它们，且 `phase1a_data_contract.py` 自带 `offline_guard()`（真发生 socket 会 `raise`），所以这是**纵深防御与卫生问题，不是现存泄漏**——本件不主张已有网络风险。但既然它对这些命令**零作用**，删掉是纯收益：既去掉一处误导性写法，也缩小「零端点」主张需要辩护的导入面。

## 6 建议的更正（**本件未落，需用户授权**）

两份文档都属权威件，故本件只给措辞、不自行改：

- `docs/experiments/2026-09-23_phase1a_data_no_go.md` — `docs/INDEX.md` :66 记 `experiments/` 为「只追加证据集」，且它是**权威门槛报告** ⇒ 建议**末尾追加更正段**（不改既有正文与 `DATA_NO_GO` 结论）。
- `docs/archive/2026-10-20_entry_consolidation/2026-09-22-paper-research-next-phase.md` — 它是**活文档**而非证据集，直接修正 §Phase 2 命令块在性质上属维护而非改判据。**但本件仍不改它**，理由具体：该文件是 Loop C 队列卡 `LC-RESEARCH-001` 的 `owned_paths` 之一，Loop D 直接改会与在队列卡的归属范围冲突。建议授权后由主线程或该卡按裁定处理。

建议的统一写法（全部已实测通过）：

```bash
# 在隔离 worktree 内：用 production venv 的绝对路径（worktree 内没有 venv/）
PY=~/wzh/projects/agents_final_tech/venv/bin/python
# 在 production 检出内：PY=venv/bin/python 亦可

python3 -m py_compile research/phase1a_data_contract.py                       # rc=0
"$PY" -m pytest tests/test_phase1a_data_contract.py -q                        # rc=0, 31 passed
"$PY" -m pytest tests/test_phase1a_learnability_baselines.py -q                # rc=0, 29 passed
"$PY" -m pytest tests/test_phase2_rule_gate_replay.py -q                       # rc=0, 22 passed
"$PY" research/phase1a_data_contract.py --package-root <pkg> --output <out>    # rc=0/2 属业务语义
env PYTHONPATH=. "$PY" research/paper_result_views.py --phase2-report <r> --output <o>
```

即：**`.venv` → `venv`（worktree 内用绝对路径）**、**pytest 行不要用裸 `python3`**、**删掉无作用的 `PYTHONPATH=src` / `src:.`**、**`PYTHONPATH=.` 只保留给 `paper_result_views.py`**。标志位一律不动。

## 7 与前两件的关系（同一类缺陷的第三次出现）

| 缺陷件 | 类型 | 后果 |
|---|---|---|
| `2026-09-24_phase1a_s7_receipt_contract_gap.md` | §7 收据 schema 与机器合同不相容 | 照 §7 填满仍 14 个 schema 级错误 |
| `2026-09-24_phase1a_supplement_contract_role_gap.md` | 补充合同写 8 角色，合同要 9 角色 | 数据 owner 到货即 `DATA_NO_GO` |
| **本件** | 执行手册的解释器路径与环境变量错误 | **10 行命令 6 行实测即失败，全部 3 个 pytest 行跑不起来** |

三者是**同一类**：人工文档与机器现实脱节，且都处在「数据到货 → 验收 → 执行」这条唯一关键路径上。三处都不需要改代码或判据，只需更正文档，但**都必须由用户授权**（两份是权威件，一份是队列卡归属件）。建议合并成**一个文档更正批**一次处理，避免分三次触碰同一批权威件。

## 8 复现与取证

```bash
ssh jinrong-dev
bash /tmp/verbatim_check.sh        # 逐行原样执行 10 条文档命令并打印真实 rc
```

| 文件（GB10 `/tmp`，仓外，不 commit） | sha256 |
|---|---|
| `verbatim_check.sh` | `77eeb73d65751f54822995fa9e1718138e53e2104db291fb2ac406c62f5ffc16` |

零端点、零模型调用、零私有数据读取：合同运行刻意指向**不存在**的包路径以触发 fail-closed，其输出仅含聚合计数与哈希（`counts` 全 0、`endpoint_calls 0`、`socket_attempts 0`、`status DATA_NO_GO`），未读任何样本内容。三个 pytest 行跑的是仓内**合成 fixture** 测试。`/tmp` 非持久，故全部 rc 与报错原文已逐字抄入本件。

## 9 红线自查

未改 `DATA_NO_GO` 报告、唯一执行计划、任何代码或判据一个字节 · 未改冻结判据/阈值/oracle/冻结 hash · 未解 `DATA_NO_GO` · 未启动 Phase 1a/2 · 未批准任何数值、未填任何 `UNSET` · 未读取任何私有数据 · 未授权训练或端点 · 零模型调用 · 未派发任何 Loop A/B/C 卡 · 未与 `LC-RESEARCH-001` 的 `owned_paths` 冲突（正因如此才不改该计划件）· 未动 `docs/33`、`docs/34` · 未 pull production（仍 `e5ab809` + 5 脏件）· 未重启 daemon `1816933` 与 `:5050` `1868428` · 未改 crontab · 四件用户资产零触碰 · 逐路径 add、无 `-A`/`--amend`/`--no-verify`。
