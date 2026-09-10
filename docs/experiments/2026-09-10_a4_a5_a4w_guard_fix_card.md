---
id: TASK-20260910-A4A5A4W
risk: high
window: none
status: 定稿（决策 17=A 批准立即拟卡并派发; 与 R1 并行; 验收方 = 侧线, 修者不自验）
premises:
  - id: P1
    claim: "四个缺陷在当前 HEAD 可复现（不是历史已修）: ① summary guard 对缺失/空哈希放行 ② 冻结清单被删或不可读时 pre-commit 不 FAIL ③ Loop B 存在双 verdict 路径（PG-only 分叉 + 报告写入失败与判定失败未区分）④ 抽验脚本含恒真项与 detail-only 项"
    falsify: "各一条最小复现命令（构造缺陷工件 / 临时改名清单 / grep verdict 赋值点 / grep 恒真断言）; 任一缺陷已不存在 → 该项从范围移除并记账, 不硬修"
  - id: P2
    claim: "钩链现状 = scripts/graph/hooks/pre-commit 用 --diff-filter=ACMR（无 D）; summary-recompute-guard.precommit.sh 用 --diff-filter=ACM（无 D 无 R）; install_hooks.sh 为安装入口; GB10 侧安装态与本地一致"
    falsify: "grep 两个钩子的 diff-filter 字面值 + GB10 上 ls -l .git/hooks/pre-commit 与 sha 对照; 不符即停报（说明现状与本卡假设不同, 需重写动作序）"
  - id: P3
    claim: "定标契约的现行实现可从冻结工件复现: logs/graph/eval/d2_cross_matcher_embed.json 的 threshold_calibration 块 + 产生它的脚本（候选 research/paper_d2_cross_matcher_embed.py / research/paper_d3_matched_fpr_stage_a.py）"
    falsify: "读键在位 + 以现行脚本重跑定标（零端点、只读输入）能复现冻结阈值; 不能复现 → 停报, 不得改历史工件来对齐"
  - id: P4
    claim: "七个反例工件可由验收方（侧线）独立构造, 实施方不自造自验"
    falsify: "派发前确认验收方已接指令; 若验收方不可用 → 停下报 Loop D, 不得由实施方代构造"
  - id: P5
    claim: "修复期间钩子不得处于半装状态, 且任何缺陷工件都不得真实进入 main"
    falsify: "反例验证一律在临时分支或 --no-verify 干跑 + 事后 git log 核 main 无缺陷提交; 发现半装或污染 → 立即回滚并停报"
acceptance:
  - "七个反例逐一被拒: ① 错哈希 ② 纯 LF 与 raw 失配 ③ 缺哈希字段 ④ 删冻结件 ⑤ 删清单 ⑥ PG-only 失败 ⑦ 缺 rho 键"
  - "正常样本仍通过（修复不得把合法提交挡掉; 至少含一个改 docs 与一个改 scripts 的正常提交）"
  - "GB10 hook 安装态一并核对（审计 E14 仅核过本地）"
  - "A5: 更换评估折标签或分数不能改变已冻结定标输出"
  - "A4w: 执行位实证 + 首次 tick 实证已写进常备派发前置检查（文档或脚本二选一, 须可被后续窗口继承）"
  - "scripts/graph/frozen_hashes.txt 的既有哈希内容零改动（A4 修守卫逻辑, 不是改冻结清单）"
  - "pytest 全量基线在 GB10 不回归（权威口径 = GB10）+ docs_lint exit 0 / fails []"
rollback: "改前备份现有钩子与 frozen_hashes.txt（备份路径入汇报）; 任一反例未被拒或正常样本被挡 → git revert 该提交并停报; 不回滚他人提交"
redlines:
  - "零端点: 不碰 :8004/:8006/:8008, 无 canary、无 judge、无模型调用, 不起任何 run"
  - "零重跑: 不执行 paper_d3_autopsy_recompute.py 与 paper_d3_stage_b_closeout.py, 不铸 v2 收据; 两份收据 sha 与 SUMMARY-GUARD 块零改动"
  - "判据 / oracle / 阈值 / 协议 / 分类底表 85·7·26 / S-2 分母 111 与 TPR 0.810811 零改动且不溯及"
  - "不动 frozen_hashes.txt 既有哈希内容; 不动 GB10 /tmp 下 watcher 与 dispatch 及其 0664 权限; 不补 done 件; 不清 /tmp"
  - "不动 ~/.codex/archived_sessions 原件; 不改任何 Codex 应用配置（决策 15=A 仍生效）"
  - "不碰两份 side_handoff（只读、不提交）; 不 commit 三件残件与 logs/graph/docs_lint_report.json（本地 lint 一律 --json 落仓外）"
  - "不动 paper/draft_v0_s1_s2_s6.md、蓝图、blind_cone 骨架（决策 16=B 授权已用毕）"
  - "禁 git add -A / --amend; commit/push 禁接截断管道, 结果以 git log 为准; 报行数以 --numstat 为准并标明口径"
  - "修者不自验: 七个反例由验收方构造与判定; 实施方不得自造自验"
  - "与 R1 批的提交路径不得重叠（本卡动守卫与定标代码, R1 动 status.sh）; 各自 pull 前先提交自身; 不得互相 reset / stash / checkout"
skills:
  - "graph-loop-rules（红线常备）"
  - "verify-before-done"
  - "systematic-debugging"
  - "security-best-practices（守卫与钩子属安全面）"
  - "receiving-code-review（审计 F01-F10 反馈的技术性验证）"
---

# 任务卡 A4/A5/A4w 合并批: 四守卫修复包 + 定标契约版本化 + watcher 机制常备化（决策 17=A）

> 派发载体: Loop A（GB10, `codex exec --profile loopa-exec`）| 主线程拟卡与抽验 | **验收方 = 侧线（修者不自验）**
> 依据: `docs/experiments/2026-09-06_harness_audit_response.md` §1 F01-F10 裁定（全部接受）+ §2 A4/A5/A4w 行 + :32-33 验收条件 + 决策 7B（时点钉死）+ **决策 17=A（立即拟卡并派发, 与 R1 并行）**
> 窗口类型声明: **零端点窗**（纯代码与文档修复 + 本地/GB10 只读验证, 无模型调用）⇒ 不限时段（承模板 §8 窗口时段规则）
> **时点合规声明（入卡, 承决策 7B）**: 7B 把本批时点钉死为「**D4 拟卡之后、D4 执行之前**」; D4 卡已于 09-10 拟稿（`docs/experiments/2026-09-10_d4_transfer_preregistration_card.md`, `TASK-20260910-D4`）⇒ **时点条件已满足**, 本批合法启动, 无需对 7B 解冻。
> **裁定理由（用户 09-10 夜, 逐字入账）**: A4 修的是**守卫本身**（summary guard 对缺失值放行 / 冻结清单被删时双层守卫检不出 / Loop B 双 verdict / staged 与工作树对象漂移）, 而 **D4 会产出一份新收据与新的 SUMMARY-GUARD 块**; 先跑 D4 再修守卫, 等于**用一把已知有毛病的尺子量数据**, 量完还要在论文里解释该收据产出于守卫缺陷期。决策 7B 当初把时点钉成「D4 拟卡之后、执行之前」防的就是这个。

## 1. 目标

把审计 F01-F05 对应的四处守卫缺陷修掉并版本化定标契约, 使 D4 产出的收据与 SUMMARY-GUARD 块**产出于守卫已修复的状态**; 同时把 watcher 的双实证要求常备化, 供后续所有窗口继承。量化验收 = **七个反例逐一被拒 + 正常样本仍通过 + GB10 hook 安装态核对 + A5 换折不改冻结输出 + pytest 与 docs_lint 在 GB10 不回归**。

## 1.5 Skill 装载清单

`graph-loop-rules`（红线常备）/ `verify-before-done`（完成门）/ `systematic-debugging`（根因追溯）/ `security-best-practices`（守卫与钩子属安全面）/ `receiving-code-review`（对审计反馈做技术性验证而非照单全收）。收口时回报「装了没用 / 没用装」。

## 2. 前提假设清单（同 YAML, 执行前逐条填实测结论）

| # | 假设 | 一分钟证伪方式 | 实测结论（执行前填） |
|---|------|----------------|----------------------|
| P1 | 四个缺陷在当前 HEAD 仍可复现 | 各一条最小复现命令 | ☐ |
| P2 | 钩链现状 = pre-commit 用 `ACMR`（无 D）、summary-guard 钩子用 `ACM`（无 D 无 R） | grep 两处 `--diff-filter` 字面值 + GB10 `.git/hooks/pre-commit` sha 对照 | ☐ |
| P3 | 定标契约现行实现可复现冻结阈值 | 读键在位 + 零端点重跑定标比对冻结值 | ☐ |
| P4 | 七个反例由验收方独立构造 | 派发前确认验收方已接指令 | ☐ |
| P5 | 修复期钩子不半装、缺陷工件不入 main | 反例走临时分支或 `--no-verify` 干跑 + 事后 `git log` 核 main | ☐ |

> 主线程已代核 P2 的一半（拟卡时实测）: `scripts/graph/hooks/pre-commit` 用 `git diff --cached --name-only --diff-filter=ACMR`（**含 R 不含 D**）, 且 `[ -z "$CHANGED" ] && exit 0`、`if [ -f "$MANIFEST" ]` 两处使「全为删除」与「清单缺失」都静默放行; `summary-recompute-guard.precommit.sh` 用 `--diff-filter=ACM`（**无 D 无 R**）。**这正是 F05 与 F02 的代码级落点**, Loop A 须自行复核后再改（不得凭本卡转述）。

### 2.1 交互假设检查（承模板 §2.1 与本轮开工卡 §四）

| 变更对 | 共享资源/假设 | 冲突验证方式 |
|---|---|---|
| **A4/A5 批 × R1 批**（两卡并行, 开工卡 §四.1） | 两者同在 GB10 改**同一个仓库**且都可能触发 commit ⇒ 冲突面 = **GB10 工作树与提交序** | **提交路径不重叠**（本卡动 `scripts/graph/hooks/*`、`scripts/graph/loop_b_verify.sh`、定标脚本与相关测试; R1 只动 `scripts/graph/status.sh`）; **各自 pull 前先提交自身**（既有先例）; **不得互相 reset / stash / checkout**; 每次 push 前 `git fetch` + `merge-base --is-ancestor` 确认可快进 |
| **A4 守卫修复 × 现有 pre-commit 钩链**（开工卡 §四.2） | **A4 改的就是钩子本身** ⇒ 修复期间钩子可能处于半装状态, 且反例验证会真实触发钩子 | ① **改前备份**现有钩子与 `scripts/graph/frozen_hashes.txt`（备份路径入汇报）; ② 修复期间**不得让钩子处于半装状态**（要么旧版完整、要么新版完整, 用 `install_hooks.sh` 原子安装, 承 A19 的「暂存校验后交换安装目录」姿势）; ③ **七个反例验证过程中不得把任何缺陷工件真实提交进 main**——一律走临时分支或 `--no-verify` 干跑, 事后以 `git log --oneline main` 核实无污染 |
| A5 定标版本化 × 既有冻结工件 | 新旧定标输出若共用路径会互相覆盖, 且「修实现」易被误读为「改历史判据」 | **旧工件冻结、新旧版本分列**（不同文件名与不同键）; 版本化后以「更换评估折标签/分数不改变已冻结输出」为验收; 不改任何历史工件字节 |

## 2.2 预注册预测（跑前落盘; 推导门与经验预测分列）

**推导门**（失配 = 实现/口径问题 → 查实现或停报）

- G-1: 七个反例**逐一被拒**（每个都返回非零并给出可读理由）。
- G-2: 正常样本**仍通过**（至少一个改 `docs/` 的正常提交 + 一个改 `scripts/` 的正常提交）。
- G-3: `scripts/graph/frozen_hashes.txt` 的**既有哈希内容零改动**（`git diff` 对该文件为空; 若 A4 需要新增保护条目, 只能**追加行**且须在汇报中单列, 不得改既有行）。
- G-4: A5 验收 = **更换评估折标签或分数不能改变已冻结定标输出**（改输入后重跑, 冻结输出字节不变）。
- G-5: 两份既有收据 sha 与 SUMMARY-GUARD 块零改动（`summary_recompute_guard.py check` 对 autopsy 记录与 closeout 记录仍 exit 0）。
- G-6: GB10 `pytest` 全量基线不回归 + `docs_lint` exit 0 / fails []。

**经验预测**（真会被反驳; 两方向皆合法）

- E-1: 若 F05 的双层守卫缺口是**唯一**的删除绕过路径, 则补上 `D` 过滤 + 清单缺失即 FAIL 后, 「删冻结件」与「删清单」两个反例都应被拒; 若仍有一个被拒失败, 说明**存在第三条路径**（如 rename 到仓外、或经 `--no-verify`）, 须如实入账为残余风险, 不得宣称「守卫已完备」。
- E-2: 若 F03 的双 verdict 真是分叉而非表述问题, 则单一 verdict 同源改造后, PG-only 失败反例应被 Shell 总判定捕获; 若改造后仍捕获不到, 说明 PG 池检查本身不在总判定路径上, 属更深缺陷, 停报不硬修。
- E-3: A5 版本化后, 现行冻结阈值应**仍可复现**（P3）; 若不能复现, 说明现行实现与冻结工件之间存在未记录的口径差, 属 F01 家族, 如实上报并按更正注记处理, **不得改历史工件来对齐**。

## 3. 动作序

**阶段 0（取证, 零改动）**

1. 逐条复现 P1 的四个缺陷, 各留一份最小复现记录（命令 + 输出摘要）; 任一缺陷已不存在 → 该项移出范围并记账。
2. 备份: 现有 `scripts/graph/hooks/pre-commit`、`summary-recompute-guard.precommit.sh`、`install_hooks.sh`、`scripts/graph/frozen_hashes.txt`、`scripts/graph/loop_b_verify.sh`（备份路径逐条入汇报）。
3. 记录 GB10 `.git/hooks/` 安装态（`ls -l` + sha）作为「改前」基线。

**阶段 1（A4 四守卫修复包, 逐项独立提交）**

4. **修复包 ①（F02）summary guard**: 只比较**有效非空哈希** + 校验对象绑定**待提交 staged blob**（不是工作树文件）。反例 = 错哈希 / 纯 LF 与 raw 失配 / 缺哈希字段。落点 = `scripts/graph/hooks/summary_recompute_guard.py` + `summary-recompute-guard.precommit.sh`（后者 `--diff-filter` 需补 `D`/`R` 语义或显式说明为何不需要）。
5. **修复包 ②（F03）Loop B 单一 verdict 同源**: JSON、日志、状态位、退出码**消费同一结果**; PG 池检查纳入 Shell 总判定; **报告写入失败与判定失败区分**; daemon 与单次退出语义分开。反例 = PG-only 失败。落点 = `scripts/graph/loop_b_verify.sh`（20 177 B）。
6. **修复包 ③（F05）冻结清单删除的双层守卫**: pre-commit 覆盖**删除与重命名**（`D` 过滤修正）+ **清单缺失/不可读/空条目 = FAIL**（不再静默放行）+ **清单独立保护**; 并修 `[ -z "$CHANGED" ] && exit 0` 使「全为删除」不被当作「无变更」。反例 = 删冻结件 / 删清单。落点 = `scripts/graph/hooks/pre-commit`。
7. **修复包 ④（F04）抽验脚本纪律**: 按新纪律改造抽验脚本族——**缺键即失败 / 删恒真项 / 观察项 INFO 不入 PASS 分母 / 失败返回非零 / 证据级别逐项标注 / 微型错误工件自验**。反例 = 缺 rho 键。落点 = `research/` 下 spotcheck/recompute 脚本族（候选: `paper_d3_stage_b_closeout.py`、`paper_d2_phase_b_spotcheck_recompute.py`、`paper_w2_spotcheck_recompute.py`、`paper_d3_spotcheck_recompute.py`; 具体范围由 Loop A 按 P1 复现结果确定并在汇报中列明）。

**阶段 2（A5 定标契约版本化）**

8. 新定标函数**只接受训练折 clean 分数 + 预冻结候选网格**; **clean 恒零不得取 θ=0**（`score ≥ θ` 判阳下经验 FPR = 1）, 须显式正阈值边界规则或按卡面 pivot 条款; **S1 自证由输入集合断言生成、禁硬编码**; **旧工件冻结、新旧版本分列**, 不混淆「修实现」与「改历史判据」。验收 = G-4。

**阶段 3（A4w 剩余范围 = 常备化, 不是为 D4 再做一遍）**

9. 把**执行位实证 + 首次 tick 实证**写进**常备派发前置检查**供后续所有窗口继承（落点二择一并在汇报中说明: 文档层 = `docs/experiments/2026-09-06_harness_audit_response.md` §2.1 第 2 项的操作化细则, 或脚本层 = 派发前置检查脚本）。**A4w 的 D4 侧实例已由 D4 卡 BG-7 完整承载**（`bash /tmp/x_watcher.sh` 注册或创建即 `chmod +x`, 加两项实证）⇒ **本项不重复实现 D4 的 watcher**, 只做「让下一个窗口自动继承」这一层。
10. **不动** GB10 `/tmp` 下 watcher 与 dispatch 及其 0664 权限、**不补** done 件、**不清** `/tmp`（F-0907-1 证据现场）。

**阶段 4（验收与收口）**

11. 通知验收方（侧线）构造并投放**七个反例**; 实施方**不得自造自验**。逐例记录「反例 → 期望被拒 → 实测结果」。
12. 正常样本回归（G-2）+ GB10 hook 安装态核对 + `pytest` 全量 + `docs_lint`（`--json` 落仓外）。
13. 逐路径 commit（禁 `-A`、禁 `--amend`）→ push → 汇报（含备份路径、七反例逐例结果、G-1..G-6 与 E-1..E-3 结论、`--numstat` 数字并标明口径）。

## 4. 中止与退出条件

- **中止**: P1 任一缺陷无法复现且无替代证据 → 该项移出范围并记账（不硬修）; P2/P3 证伪 → 停报, 重写动作序或报 Loop D; 反例验证导致 main 被污染 → 立即回滚并停报; 钩子处于半装状态且无法原子恢复 → 停报。
- **成功退出**: 七反例全被拒 + 正常样本通过 + GB10 安装态核对 + G-1..G-6 全过 + commit/push + 汇报, 且 `frozen_hashes.txt` 既有哈希零改动。
- **失败退出**: 任一修复包无法在不改动历史工件与判据的前提下完成 → 该包**方向关闭并如实记账**, 不硬撑、不改历史来对齐。
- **pivot**: 若修复包 ④ 的抽验脚本族范围过大（>6 个文件）导致单批不可控 → 缩为「新增抽验一律按新纪律 + 存量只改 D4 会用到的那几个」, 并在汇报中显式声明缩范围与理由, 交 Loop D 追认。

## 5. 验收证据表

按 `templates/acceptance_checklist_template.md` 填写（声明 → 验证命令 → 实测值三列, 实测值粘贴原始输出）。逐项标注证据级别（L1 字段存在 / L2 存值一致 / L3 独立复算 / L4 运行证据）; **恒真项与 detail-only 项不入 PASS 分母**（这正是修复包 ④ 要落地的纪律, 本卡自身先遵守）。

## 6. 汇报格式

执行结果 / 四个缺陷的复现记录 / 备份路径清单 / 逐修复包改动文件与 `--numstat`（标明口径）/ **七个反例逐例结果（反例 → 期望 → 实测 → 谁构造）** / 正常样本回归结果 / GB10 hook 安装态前后对照 / A5 的 G-4 实测 / A4w 常备化落点与形式 / G-1..G-6 与 E-1..E-3 逐条结论 / `pytest` 与 `docs_lint` 结果 / 红线自查 / commit hash。每个声明字段必须在 §5 有对应证据行。

## 7. 红线（同 YAML redlines）

零端点; 零重跑（两份收据 sha 与 SUMMARY-GUARD 块零改动）; 判据·oracle·阈值·协议·底表 85·7·26·分母 111·TPR 0.810811 零改动不溯及; 不动 `frozen_hashes.txt` 既有哈希内容; 不动 GB10 `/tmp` 0664 现场; 不动 `archived_sessions` 原件与任何 Codex 应用配置; 不碰两份 side_handoff; 不 commit 三件残件与 `docs_lint_report.json`; 不动 draft / 蓝图 / blind_cone 骨架; 禁 `-A` / `--amend`; commit/push 不接截断管道; 报行数以 `--numstat` 为准并标明口径; **修者不自验**; 与 R1 批提交路径不重叠、不互相 reset/stash/checkout。

## 8. 执行节奏纪律

沿用 `templates/task_card_template.md` §8 全局规则（禁 >5min 阻塞 sleep; 里程碑等待 = cron one-shot + 工件 + 结 turn; cron 闸不达标 = 改期至多 2 次、**禁 SKIP**; UTF-8 字节截断必须字符安全 `| iconv -f utf-8 -t utf-8 -c`; 本卡为零端点窗故不限时段; 人类决策不排在 22:00 后）。**本卡补充**: 反例验证**必须**走临时分支或 `--no-verify` 干跑, 严禁把缺陷工件提交进 main。

## 9. 事后复盘（收口必填）

- **结果**: 成功 / 失败 / 部分成功（逐修复包分列）
- **关键洞察**: <尤其 E-1 是否存在第三条绕过路径、E-2 的 PG 池是否真在总判定路径上>
- **推翻的旧判断**: <supersede 指针; 更正不涂改>
- **喂给了什么**: <D4 派发前置第 3 项「A4/A5 验收通过」的满足度 + D4 收据的可信度基础 + A18（收据外裸数字机械核验）的方案输入>
