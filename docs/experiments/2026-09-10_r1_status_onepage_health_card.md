---
id: TASK-20260910-R1
risk: low
window: none
status: 定稿（决策 19=A 批准立即拟卡并派发; 与 A4/A5/A4w 批并行; 验收方 = 侧线, 修者不自验）
premises:
  - id: P1
    claim: "scripts/graph/status.sh 现为 115 行, 输出为人读文本; :111 调 ./venv/bin/python scripts/docs_lint.py（默认 --json 落 logs/graph/docs_lint_report.json ⇒ 查看命令有写副作用, 即审计 A20 所指）; :113 调 sync_skills.sh --check"
    falsify: "wc -l + sed -n '108,115p' 逐行核对; 与卡内描述不符 → 停报并按实况重写动作序"
  - id: P2
    claim: "docs_lint.py 支持 --json <path>（main() 内 ap.add_argument(\"--json\", default=REPO_ROOT/logs/graph/docs_lint_report.json)）⇒ 只读副作用可用「重定向到仓外」消除, 无需改 docs_lint.py 本体"
    falsify: "grep --json 参数定义; 若不支持则需改 docs_lint.py（范围扩大, 停报 Loop D 追认）"
  - id: P3
    claim: "sync_skills.sh --check 为纯只读（不写任何文件）"
    falsify: "跑一次 --check 前后对 ~/.codex/skills 与 ~/.claude/skills 取 sha 清单对比; 若有写入 → 一并纳入本卡范围或停报"
  - id: P4
    claim: "一页健康所需六项数据均可零端点取得: 三方 HEAD（git + git ls-remote + ssh 本地侧）/ 端口与进程（ss 或 lsof, 只列不连）/ Loop B 最近 PASS（logs/graph/loop_b_last_status 与 verify-report.json）/ B4 两列口径（b4_checkpoint 产物）/ crontab 现行条目（crontab -l）/ GB10 脏件清单（git status --porcelain）"
    falsify: "逐项一条命令试取; 任一项取不到 → 该项在输出中显式标 UNAVAILABLE, 不得静默省略（承 A20「坏输入失败」精神）"
  - id: P5
    claim: "端口清单只列举不连接 ⇒ 不构成端点调用（:8004/:8006/:8008 零推理请求）"
    falsify: "跑一次前后比对 GB10 侧模型服务日志的请求计数; 若计数增加 → 立即停报, 该实现违反零端点"
acceptance:
  - "一条命令输出一页健康, 且与手工核验逐项相符（六项全覆盖; 取不到的项显式标 UNAVAILABLE）"
  - "--json 输出可被机器解析（python -c json.load 通过）且字段名稳定（含 schema_version）"
  - "只读模式确实不再覆盖 logs/graph/docs_lint_report.json（跑 status.sh 前后该文件 sha256 相同）"
  - "零端点自证: 输出内含 endpoint_calls = 0; 且 :8004/:8006/:8008 无新增推理请求"
  - "pytest 全量基线在 GB10 不回归 + docs_lint exit 0 / fails []（--json 落仓外）"
  - "与 A4/A5/A4w 批提交路径不重叠（本卡只动 scripts/graph/status.sh 及其新增测试）"
rollback: "git revert 该提交; status.sh 改前备份（备份路径入汇报）; 不回滚 A4/A5/A4w 批的提交"
redlines:
  - "零端点: 不碰 :8004/:8006/:8008, 无 canary、无 judge、无模型调用, 不起任何 run; 端口只列举不连接"
  - "零重跑: 不执行 paper_d3_autopsy_recompute.py 与 paper_d3_stage_b_closeout.py, 不铸 v2 收据; 两份收据 sha 与 SUMMARY-GUARD 块零改动"
  - "判据 / oracle / 阈值 / 协议 / 分类底表 85·7·26 / S-2 分母 111 与 TPR 0.810811 零改动且不溯及"
  - "查看命令不得改任何仓内文件（这是本卡的正题, 不是附带要求）"
  - "不动 frozen_hashes.txt; 不动 GB10 /tmp 下 watcher 与 dispatch 及其 0664 权限; 不动 archived_sessions 原件; 不改任何 Codex 应用配置（决策 15=A）"
  - "不碰两份 side_handoff; 不 commit 三件残件与 logs/graph/docs_lint_report.json"
  - "不动 paper/draft_v0_s1_s2_s6.md、蓝图、blind_cone 骨架（决策 16=B 授权已用毕）"
  - "禁 git add -A / --amend; commit/push 禁接截断管道, 结果以 git log 为准; 报行数以 --numstat 为准并标明口径"
  - "修者不自验: 验收方 = 侧线; 实施方不得自行签署「输出与手工核验相符」"
  - "与 A4/A5/A4w 批各自 pull 前先提交自身; 不得互相 reset / stash / checkout"
skills:
  - "graph-loop-rules（红线常备）"
  - "verify-before-done"
  - "codebase-map（先读懂 status.sh 现状再改）"
  - "broken-window-check（改前先跑一次现状, 记录既有失败项）"
---

# 任务卡 R1: L1 `status.sh` 一页健康 + `--json` + 消除只读副作用（决策 19=A）

> 派发载体: Loop A（GB10, `codex exec --profile loopa-exec`）| 主线程拟卡与抽验 | **验收方 = 侧线（修者不自验）**
> 依据: `docs/archive/2026-10-19_29_graph_engineering_roadmap.md` :19 起 L1（0.5d, **★★★ 推荐先做**）+ :69 L3 前提 ⑤（「稳定运行 2 周 + 加 `--json` 输出模式供编排器消费」）+ 审计 F09/A20（`status.sh` 自称只读但 `:111` 调 docs_lint 覆盖报告件）+ **用户 09-10 夜 loop 路线圈选 = R1 先做**（Loop A 实施、侧线验收、零端点、0.5 天）
> 窗口类型声明: **零端点窗**（只读汇总, 无模型调用）⇒ 不限时段。**不需实验窗**, 只需一次 GB10 提交-拉取回合。
> 与论文线的冲突面: **几乎为零**（不抢端点、不抢窗、不碰判据）。唯一交集 = 若同批处理 `logs/graph/docs_lint_report.json` 的口径, 须与 neat 卡合并处置, 避免两批各改一次（用户已裁定该件口径 = **落仓外**, 本卡即为该裁定的机械落地）。

## 1. 目标

把辅助线的 ad hoc 核验固化为**一条命令出一页健康**, 并消除「查看命令有写副作用」这一 A20 缺陷。量化验收 = 六项数据全覆盖且与手工核验逐项相符 + `--json` 可机器解析 + **跑 `status.sh` 前后 `logs/graph/docs_lint_report.json` 的 sha256 相同** + 零端点自证。

## 1.5 Skill 装载清单

`graph-loop-rules`（红线常备）/ `verify-before-done`（完成门）/ `codebase-map`（先读懂现状）/ `broken-window-check`（改前先跑一次记录既有失败项, 免得把既有红灯算成本卡回归）。收口回报「装了没用 / 没用装」。

## 2. 前提假设清单（同 YAML, 执行前逐条填实测结论）

| # | 假设 | 一分钟证伪方式 | 实测结论（执行前填） |
|---|------|----------------|----------------------|
| P1 | `status.sh` 115 行, `:111` 调 docs_lint（默认落仓内报告件）, `:113` 调 sync_skills --check | `wc -l` + `sed -n '108,115p'` | ☐ |
| P2 | `docs_lint.py` 支持 `--json <path>` ⇒ 副作用可用重定向消除, 无需改其本体 | grep `--json` 参数定义 | ☐ |
| P3 | `sync_skills.sh --check` 纯只读 | 跑前后对两个 skill 目录取 sha 清单对比 | ☐ |
| P4 | 六项数据均可零端点取得 | 逐项一条命令试取; 取不到则显式标 UNAVAILABLE | ☐ |
| P5 | 端口只列举不连接 ⇒ 不构成端点调用 | 跑前后比对模型服务请求计数 | ☐ |

> 主线程拟卡时已代核（Loop A 须自行复核, 不得凭本卡转述）: `status.sh` = **115 行**; `:111` = `DL=$(./venv/bin/python scripts/docs_lint.py 2>&1 | head -1)`（**无 `--json` 参数 ⇒ 走 default = `logs/graph/docs_lint_report.json`, 即写副作用**）; `:113` = `SS=$(bash scripts/graph/sync_skills.sh --check 2>&1 | tail -1)`; `scripts/docs_lint.py` `main()` 内确有 `ap.add_argument("--json", default=os.path.join(REPO_ROOT, "logs", "graph", "docs_lint_report.json"))` ⇒ **P2 成立, 修法是加 `--json` 重定向而非改 docs_lint.py**; `:96-108` 为 frozen_hashes 的 md5 逐行核对（`grep -vE "^[[:space:]]*(#|$)"` + `md5sum`）, 属只读, 本卡不动。

### 2.1 交互假设检查（承模板 §2.1 与开工卡 §四.1）

| 变更对 | 共享资源/假设 | 冲突验证方式 |
|---|---|---|
| **R1 批 × A4/A5/A4w 批**（两卡并行） | 同在 GB10 改**同一仓库**且都可能触发 commit ⇒ 冲突面 = **GB10 工作树与提交序** | **提交路径不重叠**: 本卡只动 `scripts/graph/status.sh` 及其新增测试; A4/A5/A4w 动 `scripts/graph/hooks/*`、`scripts/graph/loop_b_verify.sh`、定标脚本与抽验脚本族。**各自 pull 前先提交自身**（既有先例）; **不得互相 reset / stash / checkout**; push 前 `git fetch` + `merge-base --is-ancestor` 确认可快进。若两卡同时收口, **以先 push 者为准, 后者 pull --ff-only 后再 push** |
| R1 的 `--json` × A4/A5/A4w 的 `docs_lint` 调用点 | 两卡都可能触碰 `docs_lint` 的调用方式（A4 修复包 ④ 涉及抽验脚本纪律, 若其中含 lint 调用则重叠） | 本卡**只改 `status.sh` 内的调用点**; 若发现 A4/A5 批也需改同一调用点 → **停下报 Loop D 定归属**, 不得两批各改一次（用户已明示避免此项重复） |
| `--json` 输出 × L3 编排器（远期消费方） | L3 前提 ⑤ 要求字段名稳定; 若本卡随意命名字段, L3 落地时又要改 | 输出含 **`schema_version`** 字段, 字段名一次定死并在卡内列出; 后续变更须升 `schema_version` 且按更正注记处理 |

## 2.2 预注册预测（推导门与经验预测分列）

**推导门**

- G-1: 跑 `status.sh` 前后 `logs/graph/docs_lint_report.json` 的 **sha256 相同**（本卡正题, 失配 = 未修好）。
- G-2: `--json` 输出可被 `json.load` 解析, 且含 `schema_version` 与六项数据各自的键（取不到的项值为 `"UNAVAILABLE"` 而非缺键）。
- G-3: 人读输出与 `--json` 输出**同源**（同一份数据结构渲染两种形态, 不得各算一遍——承 A4 修复包 ② 的「单一 verdict 同源」原则）。
- G-4: 零端点自证 = 输出含 `endpoint_calls = 0`, 且跑前后 GB10 模型服务请求计数不增。
- G-5: 六项数据逐项与手工核验相符（三方 HEAD / 端口与进程 / Loop B 最近 PASS / B4 两列口径 / crontab 现行条目 / GB10 脏件清单）。
- G-6: GB10 `pytest` 不回归 + `docs_lint` exit 0 / fails []（`--json` 落仓外）。

**经验预测**

- E-1: 若三方 HEAD 对齐检查能纯只读完成, 则它不需要 ssh 回本地侧（本地 → GB10 单向即可, 用 `git ls-remote origin` 取 origin、`git rev-parse HEAD` 取 GB10）; 若实测发现必须双向 ssh 才能拿到本地 HEAD, 则该页在 GB10 侧无法自足, 须如实标注「本地 HEAD 需由调用方传入」, 不得伪造对齐结论。
- E-2: 若 `sync_skills.sh --check`（`:113`）实测**有写副作用**, 则本卡范围需扩到它（P3 证伪）; 预期是纯只读, 若证伪则如实入账并停报 Loop D 确认扩范围。

## 3. 动作序

1. **改前基线**: 跑一次现状 `status.sh`, 全文输出入汇报（`broken-window-check`: 记录既有红灯, 免得算成本卡回归）; 同时记录 `logs/graph/docs_lint_report.json` 的 sha256 与 mtime。
2. 备份 `scripts/graph/status.sh`（备份路径入汇报）。
3. **范围 ③（先做, 因为它是缺陷）**: 把 `:111` 的 docs_lint 调用改为 `--json` 落**仓外**临时路径（如 `${TMPDIR:-/tmp}/docs_lint_status_$$.json`）或纯 stdout 模式; 确保**查看命令不改任何仓内文件**。同批核 `:113` 的 `sync_skills.sh --check`（P3）。
4. **范围 ①**: 把输出重组为**一页健康**, 六项齐全 = 三方 HEAD 对齐 / 端口与进程（**只列举不连接**）/ Loop B 最近 PASS / B4 两列口径 / crontab 现行条目 / GB10 脏件清单。任一项取不到 → 显式标 **UNAVAILABLE**, **不得静默省略**。
5. **范围 ②**: 新增 `--json` 输出模式, 含 `schema_version`; **与人读输出同源**（G-3）。
6. 新增或更新测试（若有 `tests/` 对应用例则更新; 无则加一个最小用例覆盖「跑完不改仓内文件」这一断言）。
7. 自验 G-1..G-6, 逐条留实测输出。
8. 通知验收方（侧线）: **一条命令输出与手工核验逐项相符 + `--json` 可机器解析 + 只读模式确实不再覆盖报告件（前后 sha 对比）**。实施方不得自行签署。
9. 逐路径 commit（禁 `-A`、禁 `--amend`）→ push（若 origin 领先先 `pull --ff-only`）→ 汇报。

## 4. 中止与退出条件

- **中止**: P1/P2 证伪（`status.sh` 结构与卡内描述不符, 或 docs_lint 不支持 `--json`）→ 停报, 重写动作序或报 Loop D; P5 证伪（端口列举导致端点请求计数增加）→ **立即停**, 该实现违反零端点; 与 A4/A5/A4w 批出现路径重叠 → 停下报 Loop D 定归属。
- **成功退出**: 六项全覆盖 + G-1..G-6 全过 + 侧线验收通过 + commit/push + 汇报。
- **失败退出**: 若「一页健康」中 ≥2 项数据在 GB10 侧结构性不可得（非临时故障）→ 缩为可得项 + 显式 UNAVAILABLE 列表, 如实记账, 不硬凑。
- **pivot**: 若修 `:111` 的正确解法其实是给 `docs_lint.py` 加一个「纯 stdout 不写文件」模式（A20 原建议）而非重定向 `--json` → 属**改 docs_lint.py 本体**, 范围扩大, 须停报 Loop D 追认后再做（本卡默认走重定向, 不动 docs_lint.py）。

## 5. 验收证据表

按 `templates/acceptance_checklist_template.md` 填写（声明 → 验证命令 → 实测值三列, 实测值粘贴原始输出）。逐项标注证据级别; 恒真项与 detail-only 项不入 PASS 分母。

## 6. 汇报格式

改前基线输出全文 / 备份路径 / 三项范围各自的改动与 `--numstat`（标明口径）/ G-1..G-6 逐条实测（**尤其 G-1 的前后 sha256 对照**）/ E-1 与 E-2 结论 / `--json` 的字段清单与 `schema_version` / 六项数据逐项「命令 → 输出 → 与手工核验是否相符」/ `pytest` 与 `docs_lint` 结果 / 红线自查 / commit hash。

## 7. 红线（同 YAML redlines）

零端点（端口只列举不连接）; 零重跑（两份收据 sha 与 SUMMARY-GUARD 块零改动）; 判据·oracle·阈值·协议·底表零改动不溯及; **查看命令不得改任何仓内文件**; 不动 `frozen_hashes.txt` / GB10 `/tmp` 0664 现场 / `archived_sessions` 原件 / 任何 Codex 应用配置; 不碰两份 side_handoff; 不 commit 三件残件与 `docs_lint_report.json`; 不动 draft / 蓝图 / blind_cone 骨架; 禁 `-A` / `--amend`; commit/push 不接截断管道; 报行数以 `--numstat` 为准并标明口径; **修者不自验**; 与 A4/A5/A4w 批路径不重叠、不互相 reset/stash/checkout。

## 8. 执行节奏纪律

沿用 `templates/task_card_template.md` §8 全局规则。本卡为零端点窗故不限时段; 无里程碑等待需求（0.5d 单批完成）, 故不需 cron one-shot。

## 9. 事后复盘（收口必填）

- **结果**: 成功 / 失败 / 部分成功（三项范围分列）
- **关键洞察**: <尤其 E-1 三方 HEAD 能否 GB10 侧自足、E-2 的 sync_skills --check 是否真只读>
- **推翻的旧判断**: <supersede 指针; 更正不涂改>
- **喂给了什么**: <docs/29 L3 前提 ⑤ 的第 2 项（`--json`）就此满足, 第 1 项「稳定运行 2 周」开始计时; A20 只读副作用销账; `docs_lint_report.json` 落仓外裁定的机械落地>

## 附: 本批未纳入范围的已获批顺手项（如实声明, 非遗漏）

用户 09-10 夜已批准「8 份陈旧文档合并为一个 neat 批」（5 份刷元数据 = docs/17·32·33·CLAUDE.md·m1_coldstart_candidates + 3 份状态翻牌 = docs/19 快照件·30 被取代·31 日期件, 执行后 GB10 复跑 docs_lint 确认 8 warn 清零）。主线程判定**不并入本卡**, 理由 = ① 验收方不同（R1 由侧线验收脚本行为, 文档元数据批由主线程抽验即可）, 混在一批会让验收标准不可分; ② 本批令牌余量需优先保 n 表与两张卡的完整性（开工卡 §交付优先序明示 neat 批可整项顺延）。⇒ **该项顺延为独立一批**, 已记 THREADS 与总账 §9.2, 不算未完成项。
> **范围收紧注记（09-10 夜, 用户补充指令; 只增不改, 上节原文逐字保留作轨迹）**: 上节「附」所依据的开工卡「任务 3」第 3 点（*已获批可同批或紧邻批执行的顺手项: 8 份陈旧文档 neat 批*）**已整段作废**。现行口径四条 = ① **本批对 `docs/17`、`docs/19`、`docs/30`、`docs/31`、`docs/32`、`docs/33`、`docs/CLAUDE.md`、`docs/m1_coldstart_candidates` 八份文档零改动**; ② **该 neat 批与「是否与 R1 同批」的顺序安排一并顺延**, 待本批（决策 17/18/19）交付回来之后**再议** ⇒ 上节所记「顺延为独立一批」这一**顺序结论本身亦已撤回**, 不再作为既定安排; ③ **不为清 warn 而在 GB10 复跑 docs_lint 追求 8 warn 清零**——8 条既有 `[2]` 陈旧 warn **保持现状即可**, 属已知且已获批的待办, 归下一批; ④ GB10 权威复核要求相应调整 = `docs_lint` 须 **exit 0 / fails []** 且**本批触及文档零新增 warn**, **8 条既有 `[2]` warn 不计入本批验收**。**对 Loop A 的执行约束不变且更硬**: 派发指令第 11 条「不在本卡范围、不要顺手做」**继续生效**, 且现在**连「紧邻批」的口径也不再成立** ⇒ 本卡执行期间**不得以任何理由触碰上述八份文档**, 亦**不得为使其 warn 消失而改动任何文档元数据或状态头**（含 `更新:` 日期与 `状态:` 翻牌）。**本注记为范围收紧, 不扩大本卡范围、不改本卡三项范围（一页健康 / `--json` / 修 A20 只读副作用）与验收标准, 亦不重新派发**（原派发指令已含禁止项, 重派会打断正在执行的代理并造成重复工作）。
