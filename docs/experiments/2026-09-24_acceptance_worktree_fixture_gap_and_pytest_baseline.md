# 验收 worktree 的 gitignored 夹具缺口：一次不成立的推断、一份完整账目、一条「静默降级为 skip」的新纪律

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代安全门文档；**指出其 §6.2 需要补一条清单**（建议措辞见 §7，本件未改该文档）
> 用途: ① 如实纠正本轮此前连续五轮复用的一条**不成立的验收推断**；② 给出 `312bdf7` 的**全量 pytest 权威基线证据**（此前只有 `1fd3e27` 的）；③ 记下一条新发现的验收纪律——缺夹具会**静默降级为 skip 而非 fail**。
> 边界: 只读 + 在**隔离 worktree 内**复制 gitignored 夹具（安全门 §6.2 明许，逐文件核 sha256）。未改任何代码、判据、文档；未 pull production；未解 `DATA_NO_GO`。

## 1 被推翻的推断（如实入账）

本轮此前连续五轮都以同一句话免于跑全量 pytest：

> 「自 `1fd3e27`（683 passed）以来只改了 Markdown，零非 Markdown ⇒ 按『只改 Markdown 可只跑相关检查』的规矩，pytest 不是必需的。」

**这条推断不成立。** 它隐含假设「Markdown 改动不可能影响测试结果」，而我从未验证该假设。机械扫描 69 个测试文件后：

```text
触及 文档/台账/治理 面的测试文件 = 14 / 69
  test_document_governance.py     : docs/ 路径、docs_lint、INDEX.md、paper/、memory/、experiments、治理/skill 件、台账件
  test_paper_claim_acceptance.py  : docs/ 路径、experiments
  test_research_story_assets.py   : paper/ 路径、experiments
  test_script_catalog.py          : experiments
  test_guard_sentinels.py         : memory/ 路径、治理/skill 件、台账件
  test_b4_instrumentation.py      : docs_lint、台账件
  test_status_onepage.py          : docs_lint、台账件
  test_docs_lint_registry_deprecated.py : docs_lint、治理/skill 件
  test_distillation_data_audit.py : paper/ 路径
  test_m1_schema_suggestions.py   : docs/ 路径
  test_skill_routing.py / test_sync_skills_atomic.py / test_edge_cases.py / test_restart_m1_harness.py : 目录枚举
```

⇒ 新增 `docs/experiments/*.md` 与追加 `memory/THREADS.md`、`logs/graph/dispatch_log.md` **原则上可以改变测试结果**。用「只改了 Markdown」这一**窄检查**去支撑「无回归」这一**宽结论**，属口径不匹配。**本件因此实跑了全量 pytest。**

## 2 实跑结果：第一轮 4 failed（exit 1）

新建的隔离 worktree `agents_final_tech_accept_312bdf7`（HEAD `312bdf7`，`git status --porcelain` = 0）内：

```text
第一轮（worktree 内只有 1 个 data/ 文件时）:
  4 failed, 678 passed, 14 skipped, 10 warnings in 53.02s      PYTEST_EXIT=1
  FAILED tests/test_vgmc_adversarial.py::test_adv_map_deterministic_nested_wrong_target
  FAILED tests/test_vgmc_collision_overlay.py::test_overlay_merge_adds_columns_and_entries
  FAILED tests/test_vgmc_collision_overlay.py::test_overlay_none_is_identity
  FAILED tests/test_vgmc_collision_overlay.py::test_real_overlay_artifact_loads
```

四个失败**全是同一个 `FileNotFoundError`**，且**不在测试文件里抛**，而在被测代码里：

```text
tests/test_vgmc_collision_overlay.py:42:  corpus = m.load_corpus()
research/vgmc_exp1.py:60:                 imap = json.loads((DRIFT_OUT / "injection_map.json").read_text(...))
E  FileNotFoundError: .../agents_final_tech_accept_312bdf7/data/research/drift_v0/output/injection_map.json
```

**根因 = 隔离 worktree 缺 gitignored 的 `data/` 大件目录**，与代码改动无关。这与计划件 §12 “A-2 boundary” 记录的四个测试名**完全一致**（该节当时已注明 “because `injection_map.json` is absent in the isolated worktree”），也与 `1fd3e27` 那轮踩过的同类坑一致——**但那轮只复制了报错里点名的那一个文件**。

## 3 完整账目（两轮总数守恒，逐条可追）

| 轮次 | failed | passed | skipped | 合计 | exit |
|---|---|---|---|---|---|
| 第一轮（缺 7 个夹具） | 4 | 678 | **14** | **696** | 1 |
| 第二轮（8 个夹具齐备） | **0** | **683** | **13** | **696** | **0** |

两轮合计都是 **696**，差值完全可解释：

- **4 个 failed → passed**：上述四个 VGMC 测试，补上 `injection_map.json` 后通过。
- **1 个 skipped → passed**：`tests/test_drift_inject.py:151` 有一条**条件 skip**——
  ```text
  pytest.skip("TAT-QA full input not present (data/ 为 gitignored 大件目录)")
  ```
  缺 `tatqa_tables.json` 时它**不失败、而是跳过**；补上后它实跑并通过。

⇒ `683 = 678 + 4 + 1`，**零残留未解释项**。第二轮 **683 passed / 13 skipped / exit 0**，与 `1fd3e27` 记录的基线**逐项相同**。

### 3.1 13 个 skip 逐条具名（第二轮 `-rs` 输出）

```text
[2] tests/test_core_service.py       : requires full app context with DB
[2] tests/test_e2e_browser.py        : legacy chat/KB e2e against old :5000 UI, not M1/M2 scope
[1] tests/test_hmm_memory.py         : requires HMM model configuration
[1] tests/test_web_integration.py:114/134/156/185/210/229/249  (共 7 条) : legacy chat/KB integration, not M1/M2 scope
[1] tests/test_websocket.py          : websocket tests require async server fixture
合计 2+2+1+7+1 = 13
```

全部为**既有的、有理由的**跳过，无一条与本批改动相关。

## 4 新纪律：缺夹具会**静默降级为 skip**，故「0 failed」不足以证明验收环境健康

这是本件最重要的发现，且它**不是一次性事故**：

- `test_drift_inject.py:151` 在缺 `tatqa_tables.json` 时**skip 而非 fail**。
- 于是「缺夹具的 worktree」可以报出 **0 failed**，只在 **skipped 计数上 +1**。
- 若验收只看「有没有失败」，就会**在少跑了一个真实测试的情况下判定环境正常**。

⇒ **验收基线必须同时钉住 `passed` 与 `skipped` 两个计数**，不能只钉「零失败」。任何 `skipped` 漂移都必须追因到底，不得当作无关噪声。本件因此把基线记为 **`683 passed / 13 skipped / exit 0`** 三元组，而非单个数字。

## 5 夹具清单（权威、含全量 sha256）——一次给全，避免逐个试错

production 的 `data/` 共 **8 个文件、4 159 992 字节**；隔离 worktree 新建时**一个都没有**。全部为 gitignored，故复制后 `git status --porcelain` 仍为 **0**（实测）。

| sha256 | 路径 | 字节 |
|---|---|---|
| `dfb52ee23157aad7a0384def399398643772c3fe9d5ab1651889544a0c621995` | `data/eval/m1_m2_baseline_cases.json` | 2872 |
| `16e01f7162d5cd09a01bc42984c2d43b1e0c57e629b4f5ce912bab1bd6dedc0e` | `data/eval/results/2026-07-19_mcp_opencode_stability_20/stability_summary.json` | 3583 |
| `88efd16d4c8861e5bee9abc92095bebdcb862d3e3fa8166cd1a51f5ac354530b` | `data/eval/results/2026-07-19_mcp_opencode_stability_retry/stability_summary.json` | 268 |
| `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` | `data/research/drift_v0/input/tatqa_tables.json` | 1442890 |
| `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9` | `data/research/drift_v0/output/injected_tables.json` | 2568361 |
| `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e` | `data/research/drift_v0/output/injection_map.json` | 36004 |
| `1a82f8e9c295413e8b350e345c42c2c7e29c2e24eba3522246af8b6b0f9a862f` | `data/research/drift_v0/output/report.json` | 543 |
| `58660f445983cdeeaf16a31e75bc01c1f8acc13b1d5e63b85db5e0a1b9d31317` | `data/research/drift_v0/sample_injected_tables.json` | 105471 |

本批按 §6.2 **复制（`cp -a`，不软链以免回写）并逐文件核 sha256**：**7/7 与 production 全等、0 失配**（第 8 个 `injected_tables.json` 于本轮更早复制，sha256 亦与 production 全等，且与 `1fd3e27` 那轮记录的 `827092cf6af2212a…` 相同）。复制后 worktree `data/` 文件数 = **8** = production，`git status --porcelain` = **0**。

## 6 第二条教训：按名字 grep 会**低报**依赖面

要判断「哪些测试需要这些夹具」，按文件名 grep `tests/` 只得 **1 个**命中：

```text
grep -rln "injection_map|injected_tables|tatqa_tables|m1_m2_baseline_cases|drift_v0" tests/
  -> tests/test_drift_inject.py        （仅此一个真实命中）
```

但实际因缺夹具而失败的是 **4 个 VGMC 测试**，它们的依赖是**传递的**：测试调 `load_corpus()`，由 `research/vgmc_exp1.py:60` 去读 `injection_map.json`。⇒ **按关键词 grep 只能看到直接引用，看不到经被测代码传递的依赖。**

这与上一轮 `_exact_keys` 那次「差点误报」是**同一条教训的第二次出现**（那次是按被禁字段名 grep 零命中、误以为守卫缺失，实则守卫在跨多行的调用里）。**两次都指向同一纪律：否定结论与范围结论都不能只靠关键词 grep，必须读源码或实跑。**

## 7 建议给安全门文档 §6.2 补的一条（**本件未改该文档**）

§6.2 现文已写「worktree 缺 gitignored 的 `data/`、`venv/` 时：`data/` 用**复制**（`cp -a`）并逐文件核 sha256 与 production 一致」——**该表述本身是正确且完备的**（它说的是复制整个 `data/`）。真正的失效模式是**执行时只复制报错点名的那一个文件**，`1fd3e27` 那轮与本批第一轮都犯了这个错。

故建议**追加**（不改既有正文）一条可执行清单：

1. 新建验收 worktree 后、跑任何测试前，先执行「production `data/` 全量复制 + 逐文件 sha256 核对」，并把 §5 的 8 文件清单作为核对表；
2. 基线以 **`passed` / `skipped` / `exit`** 三元组记账，**`skipped` 漂移必须追因**（理由见 §4：缺夹具会静默降级为 skip）；
3. 复制后须核 `git status --porcelain` 仍为 0，以证明所复制者确实全为 gitignored、无私有件混入版本控制。

该文档是安全门权威件、且其 §3.1/§3.2 两处口径正待用户裁定（决策 3/4），为避免与待裁项混在同一 diff 里，**本件只给措辞、不自行改**。

## 8 全量 pytest 的真实网络面（决策 46 白名单**实质不完整**）

本批为取上述基线实跑了全量 pytest，并用 `strace -f -e trace=connect` 观测其网络面。结果与决策 46 所记「只读 health 探测已知两位点（`:5050` 与 `:15432`）」**不符**：

```text
全量 pytest 一轮的 TCP connect() 计数（strace 实测）：
      6 sin_port=htons(15432)   # PG
      5 sin_port=htons(8004)    # 生产视觉/LLM 模型端点
      4 sin_port=htons(53)      # DNS
      4 sin_port=htons(22)      # SSH
      1 sin_port=htons(8007)    # VLM 模型端点
      1 sin_port=htons(5050)    # 业务服务 health
     63 AF_UNIX
```

逐文件归因（各自单独 strace 实跑，计数与全量吻合）：

| 测试文件 | TCP connect | 结果 |
|---|---|---|
| `test_m2_multiturn.py` | `:15432`×3、**`:8004`×5** | 20 passed（29.43s） |
| `test_status_onepage.py` | **`:22`×4、`:53`×4** | 18 passed |
| `test_m1_ocr_fallback.py` | **`:8007`×1** | 9 passed |
| `test_health_embeddings_count.py` | `:5050`×1 | 1 passed / 1 skipped |
| `test_m1_cli_robustness.py`、`test_m2_rag.py` | 无 | 8 / 12 passed |

### 8.1 `:8004`×5 不是探活，是**真实推理**

`tests/test_m2_multiturn.py:320-350` 的 `TestMultiTurnIntegration` 标了 `@pytest.mark.integration`，其 `test_three_turn_conversation` **三次调用 `svc.ask(...)`**（:331、:337、:344），并断言答案非空、不含「未找到」、且跨轮上下文承接（:341）。这些断言**只有在真实产出答案时才可能通过**。

而它**默认不被排除**：

- `pytest.ini` 注册了 `integration` marker，但**没有 `addopts`**（实测 `grep -rn addopts` 于 `pytest.ini`/`conftest.py`/`tests/conftest.py` 均零命中）⇒ 无默认 `-m "not integration"`。
- `tests/conftest.py:36 pytest_collection_modifyitems` 只**按文件名**跳过 `test_e2e_browser`/`test_websocket`/`test_web_integration`/`test_core_service`/`test_hmm_memory`，**从不按 `integration` marker 排除**，也不涉及 `test_m2_multiturn`。
- 实测 `--collect-only`：该文件收集 20 项，**含** `TestMultiTurnIntegration::test_three_turn_conversation`；单文件运行报 **20 passed / 0 skipped** ⇒ 该集成测试**确实执行并通过**。

⇒ **每一次全量 pytest 都会对生产 `:8004` 发起 3 次真实 RAG 推理**（外加 PG 查询）。`test_m1_ocr_fallback.py` 另有 1 次 `:8007` 连接，来源应是 `src/biz/m1_statement_parser.py:604` 的 `_vlm_server_running()` 探活——该文件 docstring 自称「All external dependencies (vision-8004, PaddleOCR, fitz) are mocked」，故这是**mock 未覆盖到的探活泄漏**。

### 8.2 三条后果（须用户裁定，本件不自行改代码或配置）

1. **决策 46 的白名单实质不完整**：它记「已知两位点」，实测为 **6 个 TCP 端口**，且其中 `:8004` 属**模型推理**而非只读探活。任何以决策 46 为依据申报「零模型调用」的批次，若跑了全量 pytest，该申报**不成立**。
2. **历史上多批的「零端点 / 零模型调用」声明需要更正**：包括 `1fd3e27` 那轮的 683 passed 验收与本批两次全量跑。本件据实更正，不掩饰。
3. **验收活动本身会扰动被监控对象**：测试直连生产 `:5050`/`:8004`/`:8007`/PG，与 Loop B 的 `qa_canary`、`agent_watchdog` 共用同一栈 ⇒ 验收与监控存在真实耦合（§9 即为一例，虽未归因成立）。

可选处置（均属代码/配置面，须授权 + 修者不自验 + 补正反例）：给 `pytest.ini` 加 `addopts = -m "not integration"`；或让 `conftest.py` 的 `pytest_collection_modifyitems` 改按 marker 排除；或用环境变量显式门控集成测试；并把 `:8007` 探活纳入 mock。**本件不实施任何一项。**

### 8.3 本批据决策 46 的如实申报

本批为取基线共执行：**全量 pytest 2 次**（第 1 次因缺夹具 4 failed、exit 1；第 2 次补齐夹具后 683 passed、exit 0，其中 1 次在 `strace` 下）、**单文件 strace 归因 6 次**、`test_health_embeddings_count.py` 单跑 1 次。故本批**确有**对 `:8004` 的真实推理调用（每次全量 3 次 `svc.ask`，共约 6 次；单文件归因另 3 次）与对 `:5050`/`:8007`/`:15432`/`:22`/`:53` 的连接。**这不是零端点批**，此前 §9 曾误写为「未触及」，现已更正。所有调用均为**既有测试自身行为**，本批未新增任何端点调用代码、未起任何 run、未做 canary、未调 judge。

## 9 Loop B 现状：新增 `qa_canary` FAIL 且 action=HALT（停手上报，未自行重置）

本批取基线期间观察到 Loop B 出现**新的**失败项：

```text
周期 2026-09-24T03:40:51 : overall=FAIL  仅 git_alignment FAIL（其余 8 项 PASS）
周期 2026-09-24T05:19:05 : overall=FAIL  git_alignment FAIL + qa_canary FAIL
                           action = "HALT: Loop A must fix before proceeding"
                           verdict_source = loop_b_verify.sh (single source), verdict_consistency = OK
canary: 3/4 at 2026-09-24 05:19:01, endpoint = http://127.0.0.1:5050/api/m2/ask
  q06_minan_cash_balance  all_pass=False  route=opencode  model=opencode:qwen38-27b-fp8  sources=0  duration_ms=28076
  adv_ocr_meta            all_pass=True   route=direct    model=Qwen3.6-35B-A3B-Q4_K_M.gguf  sources=5
  adv_cross_doc           all_pass=True   route=direct    同上  sources=5
  adv_refusal             all_pass=True   route=direct    同上  sources=5
```

失败案例细节：`q06_minan_cash_balance` 问「嘉兴民安的资金余额是多少？」，期望 `exact_numeric 3508.55` + `source_required sample_jiaxing_minan`，实际返回**拒答**（「未找到与…相关的证据，无法回答该问题，拒绝编造」）且 **`sources = []`（检索为空）**，两项 check 均 `pass=false`。

**关键判别：失败项是唯一走 `route=opencode` 的那一题**，其余三题走 `route=direct` 且各取到 5 条 sources 全过。

**是否为既有间歇故障（重要，避免误归因于本批）**：日志显示**同型故障此前已出现过并自愈**——`2026-09-23 18:50:15 → 18:52:56 FAIL: canary exit=1 | 3/4 题全过`，随后 `19:23:00 → 19:26:10 OK: 4/4` 即恢复。该次发生在本批任何 pytest 活动**之前**。故 3/4 canary 是**既有间歇失败模式**，非本批新造。

**是否由本批引起：不能排除，但不足以归因。** 本批全量 pytest 确实对同一 M2 栈发起了真实 RAG 调用（§8.1），时间上与 05:16:08 起的那轮 canary 相邻；但同型故障在本批活动前已自发出现并自愈，且 `pg_pool_guard` 全程 PASS、`:5050/health` 实测仍返回 `{"status":"ok"}`、两个受保护 PID 的 `lstart` 未变。⇒ 本件**只报事实与两种可能，不做归因结论**。

**按纪律停手上报**：`action` 已是 HALT，本批**未重置 Loop B、未改 crontab、未重启 daemon 与 `:5050`、未重试 canary**。曾起一个只读的有界等待观测下一自然周期（约 05:52）是否自愈，截至本件写成（GB10 05:48:33）**下一周期尚未产生**，故自愈与否**尚无结论**，不预写。

## 10 复现

```bash
ssh jinrong-dev
cd ~/wzh/projects/agents_final_tech_accept_312bdf7
# 1) 先按 §5 清单复制 production data/ 全量并逐文件核 sha256
# 2) 再跑全量
~/wzh/projects/agents_final_tech/venv/bin/python -m pytest -q -rs
# 预期: 683 passed, 13 skipped, exit 0
```

取证文件（GB10 `/tmp`，仓外，不 commit）: `pytest_312bdf7.txt`（第一轮，exit 1）、`pytest_312bdf7_full.txt`（第二轮 `-rs`，exit 0）、`prod_data.txt` / `wt_data.txt`（两侧 `data/` 文件清单，用于求差集）、`test_surface_check.py`（§1 的 14/69 扫描脚本）。

## 11 红线自查

- 未改任何代码、判据、阈值、oracle、冻结 hash；未改任何既有文档一个字节（§7 只给措辞）。
- 未 pull production（仍 `e5ab809` + 5 脏件）；未重启 daemon `1816933` 与 `:5050` `1868428`；未改 crontab。
- 复制的 8 个文件**全为 gitignored**，复制后 worktree `git status --porcelain` 实测为 **0** ⇒ 无私有件进入版本控制；用 `cp -a` **不用软链**，避免测试回写 production。
- 逐文件 sha256 与 production 全等（7/7 + 早先 1 个），production 侧文件**未被修改**。
- **端点申报（据决策 46，如实且已更正）**：本批**不是**零端点批。为取 pytest 基线，实跑全量 2 次 + 单文件 strace 归因 6 次 + health 单跑 1 次，其间由**既有测试自身**产生了对生产 `:8004` 的真实 RAG 推理（每次全量 3 次 `svc.ask`）、`:8007` 探活 1 次、`:5050` health 1 次、`:15432` PG 若干、以及 `test_status_onepage` 的 `:22`×4 与 `:53`×4。详见 §8 与 §8.3。本批**未新增任何端点调用代码、未起 run、未做 canary、未调 judge、未训练**。此前草稿曾误写「pytest 未触及 `:5050`/`:8004`/…」，**该句为错，已更正**；错误原因是先按 `test_health_embeddings_count.py` 一处推断全局，未做 strace 归因。
- 未解 `DATA_NO_GO`；未启动 Phase 1a/2；未批准任何数值；未填任何 `UNSET`；未授权训练；未改任何代码或配置（§8.2 的处置一律未实施）。
- Loop B 处于 HALT：**未重置、未改 crontab、未重启 daemon 与 `:5050`、未重试 canary**，按纪律停手上报（§9）。
- 未动 `docs/33`、`docs/34`；四件用户资产零触碰；逐路径 add、无 `-A`/`--amend`/`--no-verify`。
