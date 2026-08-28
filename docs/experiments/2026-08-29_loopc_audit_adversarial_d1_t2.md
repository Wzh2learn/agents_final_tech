# Loop C 差分审计报告（对抗臂工件 / D1 前端 diff / T2 回填数字）
> 状态: 活跃 | 更新: 2026-08-29 | 取代/被取代: 无 | 性质: Loop C（claude --bare）差分审计报告, 审计边界 HEAD 4efd96ec（主线程派发, 三对象: 对抗臂工件/D1 前端 diff/T2 回填）

> 写入说明：报告目标文件 `docs/experiments/2026-08-29_loopc_audit_adversarial_d1_t2.md`（现为空占位）的写权限在本会话未获授权（Bash 重定向与 Edit 均被拒），故全文随本回复输出，主线程可直接落盘。**审计全程只读，未修改任何文件。**

**审计基线**: `/home/testuser/wzh/projects/agents_final_tech`, HEAD `4efd96ec`（其后无相关变更；47c2a90 后三前端文件零后续提交）。
**方法**: 逐数字三层对账（执行记录 ↔ curve json ↔ results/checkpoint，关键量用 jq 从 sugg_log 独立重算）；判定逻辑对照预注册文本与 `vgmc_adv_judge.py`；§6 时序用 `git diff 73ac314→b34ea26` + 工件时间戳；D1 用提交前后 ID 集合对照 + 语义读码；T2 用 ADV 工件算术复算 + `p1_correctness_backfill.json` 溯源。**边界**：本会话 python 执行需审批未获准，凡需 `map_headers`/`pool_h` 执行的复算以工件级一致性+算术自洽替代并如实标注。

---

## 对象 1 · 对抗建议器臂工件 —— **通过（带发现，含 1 HIGH）**

### 1.1 数字对账（三层全对齐）

执行记录 `2026-08-28_adversarial_arm_experiment.md:17-19` ↔ `vgmc_adv_curve.json` rows ↔ 各 results 文件 218-225 行块：

| 量 | 门控1.0 | 无门控0.5 | 无门控1.0 | 复核 |
|---|---|---|---|---|
| H 终值 / 基线 | 0.651905 / 0.594762 | 0.646190 / 同 | 0.646190 / 同 | `h_meas_final`、`meta.baseline_no_rules.h_meas` ✓ |
| ΔH | +0.057143 | +0.051428 | +0.051428 | = −`degradation_vs_baseline` ✓ |
| meas ACC | 0.28 | 0.12 | 0.12 | `collision_acc` ✓ |
| 对抗列 ACC | 0.20 | 0.0667 | 0.0667 | 与分母 \|adv_set\|=15 算术自洽（=3/15、1/15）；独立复算需执行权限——边界注记 |
| 固化率 | 0.3647 | 0.7619 | 0.7294 | `fixation_rate` ✓ |
| 对抗事件/接受 | 7/0 | 9/9 | 11/11 | **jq 从三个 checkpoint sugg_log 独立重算全等**（事件定义=adv对∧gain≠null，与 `vgmc_adv_judge.py:56` 一致）；sugg_log 总长 85/84/85 = `n_suggestions` ✓ |
| 门拒率 / Σε | 1.00 / 0 | 0 / 0.18 | 0 / 0.22 | 1−0/7=1.0 ✓；0.02×对抗接受数 ✓ |

注入映射与口径：16 条 / 有靶 15 / 空靶 1（`7a249c43::3`）/ 重复 0 / 前 8 ⊂ 前 16（0.5⊂1.0 嵌套成立）；**12 个 uid 全部 ∈ fix 切分**（对照 `ADV_results.meta.prereg.fix_uids`，not_in_fix=[]）→ §6 更正口径（fix 列非 meas 列）在工件层坐实；seed=20260829=代码 `ADV_SEED`（`vgmc_exp1.py:243`）✓；三件 split_digest 逐位一致（`47649383…`）✓；`n_active`=15/8/15 与 k×rate 逻辑一致 ✓；三臂终值与 C0/C1 **逐位同值**（0.651905/0.646190）✓；生成时间 23:48:24/23:50:37/23:53:01 全在 23:37-23:53 窗内，gated `runtime_s=659.73` → 起点≈23:37:24，与"开窗即修正重跑"自洽；工件清单与设计稿 §4 预登记逐一相符；`tests/test_vgmc_adversarial.py` 2 例在案（:20/:44），`pytest_latest.txt:53` ".." 过、尾行 401 passed ✓。

### 1.2 三预测判定忠实性 —— 忠实

- **③** 阈值 0.80、1.0≥0.8 → holds=true、failure_mode=null，与预注册文本（设计稿:24）逐字一致，PASS 机械成立（机制归因问题见 F1）。
- **①** both_negative=false（+0.051428>0）→ 字面失败，记录如实（执行记录:24）✓。
- **②** \|ΔH\|=0.057143 > Σε=0 → holds=false，"双口径并记"（执行记录:25）忠实 ✓。
- `vgmc_adv_judge.py:3-5` 逐字复述三预测，未放宽任何判据。

### 1.3 §6 更正：预测冻结机械证实；"解读前完成"与证据一致（带边界注记）

- `git diff 73ac314→b34ea26` 设计稿 = **纯追加 §6**，§0-§5 逐字节未动，三预测零改动 ✓。
- 支持"解读前"的证据链：§6 标注 23:3x 早于全部结果工件生成（23:48:24 起）；judge 判据未放宽；`vgmc_exp1.py:246-248` docstring 在案；三臂结果均出自更正后口径（若为 meas 口径事件必为 0）。**边界（N1）**：§6 与结果工件同 commit（b34ea26, 00:10）入库，git 本身无法对"撰写 §6"与"看数据"排序——结论为"与在案证据一致、无相反证据"，非独立可证。

### 1.4 发现清单

**F1 [HIGH] "全部被 collateral 分量拦截 / ε 维首次决定性激活" 与 sugg_log 矛盾（机制归因错误；判定本身不受影响）**
- 证据：门控臂 7 条对抗事件**全部** gain=0.0（<τ=0.1）且 collateral=0.0（≥−ε=−0.02）、reason=gated_fail（`vgmc_collision_ADV_checkpoint.json` arm_gated.sugg_log，jq 全量复核）；全 gated 日志 min(collateral)=0.0、collateral<−ε 事件数=0、Σε=0 → 拦截发生在 **gain 维**，ε 维从未点火。
- 与记录自设对照相矛盾：C0 checkpoint 重算 31/31 拒绝均 gain<τ（0 条 collateral）、C1 50/50 同型——对抗臂与 C0/C1 **同为增益型拦截**，而执行记录:23 把对抗臂写成 collateral 型并对照"C0/C1 增益型"，方向恰好反了。设计稿:11 机制锚预期的 collateral<−ε 路径未出现（对抗错列 gain 恰为 0，与 §0"错列仍计入映射"同根）。
- 传播面：执行记录:23；`memory/STATE.md:5`；T2:37；commit b34ea26 提交信息。
- 影响：P3 PASS（100%≥80%）为预注册机械判定，**依然成立**；失效的仅是机制叙事。正确表述 = "对抗建议全部被 gain 维拦截（与 C0/C1 同型），ε 维未激活（Σε=0）；§0 预期的 collateral 拦截未出现——这本身支持'伤害未显形'并强化 B 扩容动机"。

**F2 [LOW] 两处口径标注不足**
- a) judge:4 的 Σε="ε×门控接受的**对抗**建议数"（门控臂=0），比命题 1 原口径（全部 31 条接受×0.02=0.62，该口径下 ② 字面将成立）更严；记录取严口径+双口径并记，保守透明，但论文引用需显式。
- b) curve `P1.monotonic_decrease=true` 系弱不等式（u10==u05，judge:83 用 ≤），与记录"单调性 vacuous"并存；建议加注免误读为"单调降成立"。

**F3 [LOW] u05 对抗事件分母混入 3 条自然建议（判定无影响）**
- u05 实际注入集=映射前 8 对（n_active=8 ✓），但其 9 条"对抗事件"中 3 条（`a824b7af::4`、`f47d9a01::3`、`74509a86::6`）不在前 8 对、目标恰为真值 canonical（£m/£m/Consolidated），系自然正确建议，因 judge:46 以 rate-1.0 全量 15 对为分母而计入（σ_ε=0.18 亦含之；仅注入事件应为 0.12）。
- 影响：三预测判定全部不受影响（u05 无门控；Σε 只进 ② 门控臂；① 只看 ΔH）；引用"u05 对抗接受 9"时应注明 6 注入 + 3 自然。

**F4 [LOW] "逐位相同 / 2 列进流 / 提前解析" 三处措辞与工件不完全相符**
- 执行记录:31 与 T2:25 的"逐位相同"：H/ΔH/ACC 确逐位相同，但固化率 0.7619≠0.7294（两 results:220），应限定"H/ΔH/ACC"。
- 执行记录:31 "0.5→1.0 的 8 列中进流的 2 列"：sugg_log 显示增量 8 列中 **5 列**在 u10 有事件（`637d5671::3`、`74509a86::6`、`a824b7af::4`、`e2d0f4f9::3`、`f47d9a01::3`），其中 3 列在 u05 已有自然事件；"2"仅当读作净新进流（11−9）时成立。
- 执行记录:11 "其余被既有规则提前解析"：门控臂 15 靶列中 12 列被问过（7 进门 + 5 条 no_map），仅 3 列从未被问；no_map 列并非"被既有规则解析"。

**N1 [NOTE]** §6"解读前完成"为一致性证据（见 1.3 边界），非 git 可排序证明。
**N2 [NOTE]** 前提 P5 偏差未记账：设计稿:35 预注册"注入层 diff ≤30 行"，实际 b34ea26 对 `research/vgmc_exp1.py` **+44 行**（含串注/接线；覆写为独立分支，未字面复用 force_inject）。量级仍小、参数隔离（--adv-rate 0 = 原行为，单测守门），建议台账补记。

---

## 对象 2 · D1 前端 diff（47c2a90）—— **通过**

范围：仅 47c2a90 中 m1.html / m1.js / m1.css（该提交其余文件属 T1-T4，不在 D1 范围）。47c2a90 后三文件零后续提交。

1. **§4.5 选择器全保留 ✓**：当前 m1.html 中 19 个显式 ID 各恰 1 处（`m1.html:21` preciseParseChk / `:70` m2ChatLog / `:80` fileInput / `:81` sampleBtn / `:82` runBtn / `:87` suggBtn+suggCount / `:93` m2Question / `:108` m2AskBtn / `:109` m2NewChatBtn / `:110` m2Meta / `:128` tableCount / `:132` kvCount / `:136` reviewBadge / `:138` unmappedSection / `:139` reconcileSection / `:141` confirmBtn / `:156` suggList / `:158` suggApplyBtn / `:159` suggRejectBtn）；`#cmp*` 8 个（cmpDateA/B、cmpDateWrap、cmpDiffBtn、cmpMeta、cmpPosBtn、cmpProduct、cmpResult）提交前后集合逐位一致。diff 仅移除 suggModal、suggCloseBtn 两个**非 §4.5** ID，且 m1.js/tests 无悬空引用（`m1.js:894` 留显式墓碑注释）。
2. **无后端/API 改动 ✓**：47c2a90 --stat 中 src/web 下仅三前端件，零 routers/服务文件；前端新增消费仅 GET `/api/health/full`（既有端点，`src/web/routers/pages.py:55`）与既有 `/api/m1/schema-suggestions` 复用；无端点删除（diff 负侧零 fetch）、无新 POST、无任务历史服务端持久化——合 `docs/27:148` §6 红线"API 不动"。
3. **建议映射交互语义保留 ✓**：`#suggList/#suggApplyBtn/#suggRejectBtn` 在位（`m1.html:156-159`），接线不变（`m1.js:997-999`：apply→POST `/api/m1/schema-suggestions/apply`、reject→…/reject；候选行含原列名/目标下拉/置信度/理由+勾选，`m1.js:932-960`；回归门禁在后端 apply 端点 `m1.py:442`，未动）；容器 modal→右栏 tab 正是 §4.4"改版只改容器"（`m1.js:913-914` wbOpenTab('sugg')）。
4. **localStorage 键与口径 3 一致 ✓**：任务历史仅走 localStorage（`m1.js:1006` WB_STORE_KEY='m1v2_tasks'，`:1011/:1014` 读/写、上限 40 条、超配额静默降级），无任何服务端任务持久化——与口径 3（"接受 localStorage，服务端持久化=触发项 D13"）逐字相符（出处：`memory/THREADS.md:566`、`memory/STATE.md:12`、`docs/27:58/:149`、`contracts.md:98` 谓词②）；routeMode/routeHint 为纯文本只读指示（`m1.js:1208-1212`），合 §4.2 诚实设计。

**发现（均 INFO）**：
- I1：键名 'm1v2_tasks' 仅 `m1.js:1006` 定义，未在任何文档登记（契约未约定键名，不构成违约；建议补登记）。
- I2：`/api/health/full` 60s 轮询为新增只读消费者，合红线，建议验收单明示。
- I3：验收谓词⑦"13 测试绿"本次未重跑（只读审计）；`pytest_latest.txt` 尾行 401 passed 为后续提交态，供参考。

---

## 对象 3 · T2 回填数字 —— **通过（带发现）**

| 数字（位置） | 复算 | 判定 |
|---|---|---|
| §1 行 24：0.651905 / 0.594762 / −0.057143 / 0.3647 / 0.28 | `ADV_results` h_meas_final / baseline_no_rules.h_meas / degradation_vs_baseline / fixation_rate / collision_acc（220-225 行块） | ✓ 命中 |
| §1 行 25：0.646190 / 0.594762 / −0.051428 / 0.7294 / 0.12 | `ADV_u10_results` 同位字段 | ✓（"u05 逐位同值"例外见 F5） |
| §2 行 37：ΔV(H)=+0.005715 | 0.651905−0.646190（两 ADV results） | ✓（尾差注记见 I4） |
| §2 行 37：CI95[0, 0.0171] | `p1_correctness_backfill.json` dV_bootstrap["ADV_g10_vs_u10"].dV_H_ci95=[0, 0.017143]（seed 20260827, n=2000, 表级配对） | ✓ 工件级溯源（bootstrap 独立重放需执行权限，未获准） |
| §2 行 37：ΔV(ACC)=+0.16 | 0.28−0.12（两 ADV results collision_acc） | ✓ |
| §2 行 37：配对 +0.083、CI95[0, 0.167]、n=12 | backfill 件 dV_ACC=0.083333 / [0, 0.166667] / n_tables_ACC=12 | ✓ |
| §2 行 37：门拒 100% | curve P3 gate_reject_rate=1.0（≥0.8） | ✓（"ε 维决定性激活"字样承继 F1，见 F7） |
| §4 行 52：+0.005715 / +0.16 / 门拒 100% / 伤害显形仍欠 | 同上 + curve P1 both_negative=false | ✓ |

**发现**：
- **F5 [LOW] T2:25 "（u05 逐位同值）" 对固化率不成立**（0.7619≠0.7294）——与 F4 同根，建议改注"u05 H/ΔH/ACC 同值，固化率 0.7619"。
- **F6 [LOW] T2:37 "acc_meas 全体制恒定 0.1791 实锤" 的"全体制"过强**：backfill per_regime 显示 0.1791 仅普适于碰撞体制各臂（C0/C1/ADV 全臂 ✓），而 exp1/L1s42/L1s43/L2/三基线为 0.2143、L3 为 0.1667。数据实际支持"同一语料底座内 acc_meas 跨臂恒定（门控/无门控/对抗不可分）"；数字 0.1791 本身可溯（per_regime.ADV_g10.gated.acc_meas 等）。
- **F7 [承 F1] T2:37 "ε 维决定性激活"** 承继对象 1 的机制错误，供数件入图/入论文前需随 F1 一并更正。
- **I4 [INFO] ΔV(H) 尾差**：表显 +0.005715（舍入后 H 之差）vs backfill 全精度 0.005714——与既有 C0/C1 行同口径（47c2a90 起），非本次回填引入，建议表注"ΔV 为未舍入 H 之差"。
- **I5 [INFO] T2:24 "k=16 对抗靶"**：采样 16 列、有靶 15；执行记录:9 已写明，建议 T2 同步。

---

## 总体结论

| 对象 | 判定 | 要点 |
|---|---|---|
| 1 对抗臂工件 | **通过（带发现）** | 数字链三层全对齐、判定忠实预注册、§6 预测冻结机械证实；**1 HIGH**（F1 机制归因：拦截在 gain 维非 ε 维，四处传播待更正）+ 3 LOW + 2 NOTE |
| 2 D1 前端 diff | **通过** | 四项核心检查全过；仅 3 INFO |
| 3 T2 回填数字 | **通过（带发现）** | 每个数字均可在 ADV 工件（或其派生件 backfill）命中复算；2 LOW + F1 承继项 |

本审计**未修改任何文件**；重算口径（事件=adv对∧gain≠null；Σε=0.02×对抗接受数；ΔV=门控−无门控）与登记脚本 `vgmc_adv_judge.py` 完全一致。唯一需要主线程动作的是 F1 的一次性措辞更正（执行记录:23 / STATE.md:5 / T2:37，P3 PASS 判定本身不动）。
