# F-10 严格性矩阵补档与原断言撤回

> task: `tatqa-wp2-f5d-20261014` | loop: A | date: 2026-10-14
> scope: 仅补建可核验严格性矩阵、撤回未落盘断言、记录引用文件状态
> zero-endpoint: 零模型、零 endpoint、零 judge、零网络、零数据库访问

## 1. 明确撤回

`research/tatqa_wp0_2026/wp2/F5_EXECUTION_REPORT.md` L23 的以下原句现已撤回：

> An additional 24-case strictness matrix found five changed classifications, all `wrong_period` -> `wrong`; no case flipped to a correct class.

撤回原因：原 scratch 矩阵没有落盘，仓库内没有生成器、逐例结果或重跑收据；该断言不可复现、不可独立核验。**"24-case" 不再作为事实引用。**"five changed classifications" 仅在下述新构建的 16 例矩阵中重新得到支持，不能视为对原 scratch 结果的追认。

本文件只记录撤回，不改写或覆写 `F5_EXECUTION_REPORT.md`。

## 2. 新矩阵产物

可核验产物：

- 构建器：`research/tatqa_wp0_2026/wp1/build_s0c_strictness_matrix.py`
- 收据：`research/tatqa_wp0_2026/wp1/S0C_STRICTNESS_MATRIX_RECEIPT.json`
- 收据 SHA-256：`b88c7e1cce159d8f567265d5f5a53ab650758884fee89b5418f42ec8222f115b`

构建器在临时文件中重建 pre-F-10 逻辑：从现行 `checker_v2.py` 精确删除唯一 F-10 branch C 块；未修改生产路径中的 `checker_v2.py`。post 评分直接使用现行 `checker_v2.py`。

case 空间按四个二元维度穷举，未预设总数：

| 维度 | 取值 |
|---|---|
| periods order | equivalent form `[early, late]`；direct control `[late, early]` |
| `delta_source` | 对 / 错 |
| `delta_target` | 对 / 错 |
| `unit` | 对 / 错 |

因此实际总数为 `N = 2 × 2 × 2 × 2 = 16`，其中 equivalent form 8 例、direct-form control 8 例。

## 3. 实际结果

| 指标 | 实际值 |
|---|---:|
| 总用例数 | 16 |
| changed | 5 |
| unchanged | 11 |
| `wrong_period` → `wrong` | 5 |
| 其他变更类型 | 0 |
| correct-class flip | 0 |
| direct-form control 变更 | 0 |
| 状态 | `PASS` |

5 条变更逐例均满足 `wrong_period` → `wrong`；任何其他变更类型或 `correct*` 翻转都会使构建器失败即停。两轮完整收据重跑均为：

```text
b88c7e1cce159d8f567265d5f5a53ab650758884fee89b5418f42ec8222f115b
```

两轮 `cmp` 为 byte-identical。

收据内的 provenance 标注为：

> post-hoc reconstruction；原未落盘 scratch 检查已撤回

## 4. Loop C round-3 分支差分交叉证明

交叉证据：`docs/research/WP2_F5F10_LOOP_C_AUDIT_v1.md` §2.2，SHA-256 `bfe367cb8be7b362f855c1f4a2c0dc0f0ea6fb317394a80e95a4c694cd2b420b`。

该节通过 S0B 前后哈希链隔离 F-10 branch C，并穷举等价形分支，独立证明：

- 分支 A 与直接形单位门在 F-10 之前已存在；
- branch C 仅拦截等价形中未满足既有 A/B 条件的答案；
- 可达变化仅为 `wrong_period` → `wrong`；
- 无 `correct*` 翻转、无反向翻转；
- 非等价形（含直接形控制）逐支未变。

本补档的新矩阵与该 C 层差分证明相互一致：C 层给出静态分支严格性界，本 A 层收据给出 16 例逐例 pre/post 实跑归因。

## 5. S7 建议（供 C3 备档）

1. 在 `prepare_item` / `recompute_gold` 增加 fail-closed 断言：`late != early`。该断言应在周期列元数据不合法时抛错，而不是让 gold 在退化周期上继续生成。
2. runner 应携带 pre-fix 实跑路径与逐例结果，使每个 fixture 的 `observed_pre_fix_outcome` 从 runner 收据即可自证，不再依赖未落盘 scratch 或事后重构。

以上是 S7 建议，不是本轮代码修复；未执行 S4+，未改变 item freeze 状态。

## 6. owner 授权出处

在仓授权痕迹：`research/tatqa_wp0_2026/wp2/loop_a_prompt_f5.md`，SHA-256 `0b7f126b1938f3d5e1beb9d9b4efc34df09fe89f963c42f8598b97fd97d290a4`。

该卡记录 owner 于 2026-10-13 夜授权按 Loop D 默认闭环执行，并在 L13–16 明确授权 F-10 转正修复、限定唯一类别变化为 `wrong_period` → `wrong`、禁止任何用例翻成 correct。本轮 S0d 是对该授权范围内的未落盘证据补档，不扩大 S4+ 范围。

## 7. 红线遵守

- 未覆写任何既有收据或报告；本轮只新增文件。
- 未修改现行 `checker_v2.py`。
- 未执行模型、judge、endpoint、网络或数据库调用。
- 未 git add、commit、push，也未重启或探测生产服务。
