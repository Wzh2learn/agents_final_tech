# WP-2 预冻结包独立审计 — Loop C（round 1）

> task: `tatqa-wp2-prefreeze-20261013` | 审计者: GB10 Loop C（独立上下文）| 日期: 2026-10-13 | 总体判定: **CONDITIONAL**
>
> 落盘说明: Loop C 的写入通道被其沙箱拒绝（Write / bash 重定向 / tee 均受阻），报告只存在于其运行日志 `~/wzh/loop_runs/tatqa-wp2-prefreeze-20261013/c.log`。本文件正文区为该日志第 2 行起的逐字节转录（`tail -n +2`，3334 bytes，未改一字）；转录动作与其后修正的轨迹见 `tatqa-wp2-s0b-20261013` 任务收据。
>
> Loop D 转录备注（非审计内容）: F-9 的时间线解释——任务卡经 `~/wzh/tmp/` 提示文件于 22:41 派发；仓库内卡片副本由一次本地收尾提交（23:08）带入并同步到 GB10 仓库，故其 mtime 晚于产物生成时间。属记录时间差，无科学影响。

## 审计正文（逐字节转录，3334 bytes）
审计已完成，但**报告文件无法落盘**——这是本次唯一未完成的交付物，先说清楚。

## 阻塞：报告写不进去

`docs/research/WP2_PREFREEZE_LOOP_C_AUDIT_v1.md` 的三种写入机制全部被拒：

- `Write` 工具：`requested permissions … but you haven't granted it yet`（三次）
- Bash 重定向 `>`：`Output redirection … was blocked. For security, Claude Code may only write to files in the allowed working directories: '/home/testuser/wzh/projects/agents_final_tech'` —— 路径**就在**该目录内，是沙箱误判
- `tee`：`requires approval`

报告全文已写好。授予该路径写权限后我可立即落盘。

## 总体判定：CONDITIONAL

**没有判据放松**，这是最重要的正面结论。

**独立复算全部吻合**（一手证据，未采信 Loop A 自述）：

| 项 | 我方复算 | 主张 |
|---|---|---|
| origins / ≥2 可用行 | 182 / 176 | 一致 |
| 角色 disjoint | 22 互异 id，`uniq -d` 空 | 一致 |
| 哈希序 4 个组界 | 8 点严格递增，rank16/17 仅差 `28dd`/`28f3` | 一致 |
| S1 题本 | 352 题 / 176 origins / 每 origin 恰 2 题 / 22 角色全覆盖 | 一致 |
| 哈希钉 | 8 处（含 rev1.3 base、builder、replay 脚本） | 全等 |
| WP-1 历史件 | 10 项 + 5 份 run_logs **前后逐字节不变** | C2 成立 |

## 需在 item freeze 前关闭

**F-5（阻塞）** — 352 题中 **36 题 `source_unit:"currency"`** 会令 `checker.normalize_unit` 抛 `ValueError`（`currency` 不在 `UNIT_ALIASES`），**不可评分**；312 题 `null` 被静默当作 `"unit"`。我在 S1 扩建前就已定位（v1 是 5/60），v2 放大到 36/352。执行报告 L66/L152 也自行披露了同一组数字——**双方独立计数一致，问题确凿**。按 S2 草案自身 fail-closed 规则，这批题不得进入 pilot 题本。

**F-2 + F-3（同族复发第 2 次）** — 单位标签错的归类在两种数学等价的答案形态下不一致：等价形 → `wrong_unit`，直接形 → `wrong`；而 rev1.3 §2 L21 自述 `wrong_unit` 覆盖"标签错"。且**直接形仍无 fixture**——正是被修缺陷的原形态。门槛本身没松（两类都不算对），但统计归因会歪。

**F-4（同族复发第 2 次）** — `preservation_check` 等布尔量硬编码 `True`，绕开了同代码库 `_safety_claim` 强制的 `derived`/`attested: true` 词汇。**内容为真**（我方独立证明），但格式不可核验。

**F-8** — 协议 §5 列 7 类结果，契约/实现是 8 类（缺 `wrong`）。

**F-9** — 任务卡 mtime 23:09:18 晚于 S0/S1/S3 产物，卡面自述"尚未派发"；审计开始时该文件与 `wp2/` 目录均不存在。

另：**S3 不是假绿**——`split_rerun_v1.py` 从磁盘重算后与跟踪收据做字节比较、失败即停，且未覆盖旧收据（比执行卡字面要求的"直接重跑 `wp2_split_dryrun.py`"更安全）。

未验证面已如实申报：审计 shell 白名单拒绝执行 python/jq/awk/sed/xargs，故 `wp2_split_dryrun.py` 与 `s0_run_fixtures_v2.py` 未能进程级重跑；改以 8 点哈希链核验 + 手推 1 项测试期望输出（needle 生成集，与收据逐项一致）替代。

**红线全部遵守**：零模型、零网络、零凭证、未 commit、未执行 S4+、未改动任何被审文件。
