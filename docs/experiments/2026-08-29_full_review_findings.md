# 全盘复审发现清单（独立自审五路, 锚定防护, 08-29）

> 状态: 活跃 | 更新: 2026-08-29 | 审计边界: HEAD ea993d8（含 B 窗结果）| 方法: 五路并行审, 子代理只拿工件路径+声明清单, 结论自行复算
> 执行方式如实注记: Loop C（claude --bare 修复后）承担 S4 三对象（对抗臂工件/D1 前端/T2 回填）; 其余路由主线程代行独立复算（Codex 子代理机制本环境不可用, 按卡"卡死换人工代行"纪律处理）

## 子代理装载清单（路由立法首次实战记录）

| 路 | 装载（发卡人定, ≤5） | 执行者 |
|---|---|---|
| S1 数字审 | verify-before-done + paper-review-check | 主线程代行（独立复算脚本 /tmp/s1_number_audit.py） |
| S2 治理审 | jinrong-docs-sync + neat-freak + governance_drift_scan.py | 主线程代行 |
| S3 论文审 | paper-review-check + evaluator-calibration | 主线程代行（对位表全量脚本复算） |
| S4 代码审 | differential-review + spec-to-code-compliance | **Loop C（claude --bare, 修复后首次成功交付, 报告 2026-08-29_loopc_audit_adversarial_d1_t2.md）** + 主线程补审脚本族 |
| S5 技能审 | skill-doctor + skill-map | 主线程代行（sync_skills --check + docs_lint [5]） |

## 发现分级清单

### blocking（3, 已修 + 复审通过; 计数 2→3 为 08-29 元复审顺修）

**B-1 [S4/Loop C F1, HIGH] 对抗臂机制归因错误**: 执行记录/STATE/T2 写"全部被
collateral 拦截 / ε 维决定性激活", 实测 7 条对抗事件全为 gain=0.0(<τ)∧collateral=0.0
——拦截在 **gain 维**（与实验 1/C0/C1 同为增益型）, ε 维从未点火（Σε=0）。
修复: 三处措辞更正（执行记录 §3③ / STATE / T2:37）, P3 PASS 机械判定不动;
设计稿 §0 预期的 collateral 拦截未出现 = 支持"伤害未显形"叙事, 强化 B 扩容动机。
复审: 更正文本与 sugg_log 复算一致（jq 口径承 Loop C 独立重算）。

**B-2 [S1 C7b, 自发现] vgmc_adv_injection_map.json 被 EXP 跑批覆写（工件溯源断裂）——状态: 已修复（二次, 08-29 元复审重开）**: 首轮声称的写保护未落码（元复审实查: grep collision_ADV 于 vgmc_exp1.py 零命中, 报告声称≠代码事实）; 二次修复实现位点 = `research/vgmc_exp1.py:246`（_should_write_adv_map 守卫）+ `:551`（写入分支调用）, 回归测试 `tests/test_vgmc_adversarial.py::test_adv_map_write_guard`（EXP 类标签全断言只读, 3/3 过）。原文修复三步记录保留如下:
vgmc_exp1.py 在 adv_rate≥1.0 时无条件写正典射表, EXP 三跑批（扩容语料）覆写了
ADV 窗的射表（k=16 采样池变化）。修复三步: ① 确定性重建验证（重建列与提交版
逐位一致, 证可复现）② 磁盘工件恢复提交版内容 ③ 写保护（仅 label=collision_ADV
写正典表）④ EXP 实跑覆写版留档为 _EXP_snapshot 供溯源 ⑤ 扩容判定用恢复射表重跑,
**E1-E4 判定不变**（E3 仍 0.05 [0,0.1056] 未触发, 版本 B 维持; EXP_g10 对抗事件
5→6 为射表口径变化, 判定免疫）。复审: git diff 工件零差异 + 判定重放一致。

**B-3 [S3, 自发现] 方法章对位表 gain 实测域二次错误**: 首查（4 检查点）得 [0.0,1.0]
仍偏窄, 全检查点复算 = **[−0.25, 1.0]**（碰撞/基线检查点含负 gain）。修复: 对位表
域更正 + 两次更正过程注记。教训升级: 同一项两次编造/偏窄——"实测域"类数值必须
全工件域复算, 抽样检查不可代全域声明。

### polish（7, 已修/登记）

- P-1 [Loop C F2a] judge Σε 口径注记（对抗窗口径更严; 命题 1 原口径下 ② 字面将成立）→ 已加脚本头注
- P-2 [Loop C F2b] P1 monotonic_decrease 为弱不等式（≤含等号）→ 已加注
- P-3 [Loop C F3] u05 对抗事件分母含 3 条自然建议（6 注入+3 自然）→ 执行记录已注
- P-4 [Loop C F4/F5] "逐位相同"限定为 H/ΔH/ACC（固化率 0.7619≠0.7294）; "2 列进流"更正为"5 列有事件, 净新进流 2"; "提前解析"更正为"12/15 被问过含 no_map" → 执行记录+T2 已更正
- P-5 [Loop C F6] "acc_meas 全体制恒定"过强 → 更正为"同一语料底座内跨臂恒定"（STATE/T2）
- P-6 [Loop C N2] P5 注入层预算偏差（≤30 行 → 实际 +44）→ 设计稿补记
- P-7 [Loop C I1] localStorage 键名 'm1v2_tasks' 未登记 → 登记于本件（D1 实现细节: 键名/上限 40 条/超配额静默降级, m1.js:1006-1014）

### 遗留（NOTE, 如实注记）

- N-1 [Loop C N1] §6"解读前完成"为一致性证据非 git 可排序证明（§6 与结果同 commit 入库）
- N-2 [S2] INDEX 行路径省略子目录前缀为既有体例（experiments/ 与 governance/reference/ 两级）, 非漂移; 本次三路径核查全文件存在
- N-3 [Loop C I4/I5] ΔV(H) 尾差口径（未舍入 H 之差）与"有靶 15/采样 16"建议表注, 低优先

### 通过项（五路汇总）

- **S1**: C1 ΔV(ACC) 0.05 [0,0.1056] n=15 / C2 L3 ACC 0.3898/0.3644 Δ2.5pp / C3 acc_meas 0.2143/0.1791/0.1667 / C4 oracle 0.952381 vs 0.597015（H 双 1.0）/ C5 门拒 7/7 / C6 walkthrough 13/13 / C7a 基线 ΔH 逐位 0 —— **7/8 PASS（C7b 见 B-2）**
- **S2**: 漂移扫描 11 命中 0 新登记（全在案）; INDEX↔文件三方核查全存在; backlog 卡片条目全登记（A16/A17/D14/暂缓区白名单/漂移待核节）; STATE 与实况抽查对齐（版本/测试数/Loop B）
- **S3**: 盲锥章数字全命中 S1 复算（78.95/CI/0.1864/13 引文实查）; 定位双版本判据冻结核实; 相关工作 13 条引文待复核清零核实; 对位表常量（τ=0.1/ε=0.02）与代码一致; **唯 gain 域一项不合格（B-3 已修）**
- **S4**: Loop C 三对象全通过（带发现, 见上）; 主线程补审: expansion judge E 判据与卡片逐字一致（card_trigger 式）/ drift scan 设计↔实现一致（扫描面/白名单/登记逻辑）/ walkthrough 选择器接线 14 处在位
- **S5**: sync_skills --check **PASS（77 件两端一致）**; docs_lint [5] 注册表↔分发零漂移; SKILL_ROUTING.md + 任务卡 skills 字段 + AGENTS 指针三件在位; verification-before-completion DEPRECATED 标记在案（735813b 先例, 路由法冗余裁决表一致）

## 教训入账（同步侧线手递件抽验手册, effde3b）

1. **修复项验证必查实现位点**（报告声称 ≠ 代码事实）: grep 代码 + git show --stat + 必要时重跑回归; 声称无实现 = 重开（B-2 即此教训的现形）
2. **"实测域"类数值全域复算不可抽样**（B-3 同一项两次偏窄）

## 修复记录

| # | 修复 | 复审方式 | 结果 |
|---|---|---|---|
| B-1 | 三处机制归因更正 | 文本与 sugg_loop 复算对照 | 通过 |
| B-2 | 射表恢复+快照留档+判定重放（首轮）→ **写保护二次补实现（元复审重开, 位点 vgmc_exp1.py:246/:551 + 回归测试 3/3）** | git diff 零差异 + E1-E4 重放不变 + 守卫实查在位 + 回归过 | 通过（二次） |
| B-3 | gain 域 [−0.25,1.0] 二次更正 | 全检查点脚本复算 | 通过 |
| P-1~P-7 | 措辞/注记/登记 | 文本核对 | 通过 |
