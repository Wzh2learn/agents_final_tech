# T7 Loop A 强评审包：R 独立验收与回滚

## 0. 评审对象与边界

- run：`research/harness_rsi_v1/runs/T7/20261015T025839Z_c94af776/`
- 卡：`cards/T7.md` card_version=2；用户明确派发覆盖卡内 DRAFT/UNRESOLVED 占位，但没有改卡。
- 协议冻结：`282f52133a682e927c82b771fa103c27da34db7acbd8a12d2921f42a6d0bf36b`。
- 父版本：T4 v2 @`579a8cae7310ed55e969a8a09ed4ee39a8f8a8cc`；T5 v3 @`115f396af6ea461c156d91ad9148414387724eb3`；T6 @`ef5e84edbd4fcd35cc287316c0e994cf72f6faa4`。
- 候选：`cand-d44c49dec4d95741`，源状态 `PROPOSED_NOT_ENABLED`。
- 范围：只写本 T7 run；无模型、网络、远程、生产、数据库、训练、daemon、Loop B、共享注册表或 T4/T5/T6 修改。

## 1. A-1 前置修正

`candidate_amendment_A1.json` 在任何候选评估前完成，并生成 T7 本地 `amended_candidate.json`。修正把“缺收据块”拆为：

1. `MISSING_REQUIRED_EVIDENCE`：交付合同明确要求收据块但块缺失，是证据完整性缺陷；只有实际可执行且获授权的候选操作明确 `BLOCK` 才能计修复。
2. `LEGAL_UNRESOLVED`：合法不可计量保持 `UNRESOLVED`，不得填 0、不得转成严重缺陷、不得自动阻断。

T1-INC-14 本身没有被重分类为严重缺陷；其 `unverified_inference / REVIEW_REQUIRED / legal_control_design=UNRESOLVED` 保持不变。严重行为目标只隔离 T4 已独立观察到的摘要守卫静默跳过语义，避免把 token 计量缺口冒充严重漏检。

修正后的 E-03 仍使用 `FUTURE_ENUM_receipt_block_absent.md`。T5 v3 是闭合三操作注册表，没有该路径枚举或缺失收据策略的可执行操作，因此本任务没有扩展、启用或伪造该能力。

## 2. 身份与配对重放

- `identity_bindings.json` 绑定 20 件输入；跟踪输入均以 `git rev-parse HEAD:<path>` 复算 canonical git blob，并另记 run 内 SHA-256。A-1 是执行时尚未跟踪的 T7 新件，明确记 `RUN_LOCAL_UNTRACKED_AT_EXECUTION`。
- T1 v3 与 T4 v2 均为 16 案；`case_id/title/expected_category/artifact_level/applicability/legal_control_design` 逐案一致。
- T4 v2 当前树与 @579a8cae、T5 v3 当前树与 @115f396、T6 当前树与 ef5e84e 的 `git diff --quiet` 均 rc=0。
- 基线重放：11 个适用检查 × 2 轮 = 22 条日志，22/22 与 T4 声明退出码一致。派生失配只在 T7 `scratch/tmp` 产生，日志保留 hash，运行后删除；无派生失配落盘。
- T5 父调用：`ACCEPTED_WITHIN_SCOPE`，摘要正控和运行时派生失配负控行为保持。
- 候选调用：额外 E-03 在目标执行前被 T5 闭合配方契约拒绝；该 fail-closed 只证明缺少注册支持，不能计为严重缺陷检出。

## 3. 六硬门与收益/成本顺序

| 硬门 | 结果 | 依据 |
|---|---|---|
| 严重漏检=0 | `UNRESOLVED_NOT_EVALUABLE` | 合法 UNRESOLVED 已排除；缺必需证据基线静默跳过，但候选无可执行获授权操作。 |
| 合法误拦≤基线 | `PASS_AT_PARENT_CONTROLS_ONLY` | T5 父控制保持；候选全行为未建立。 |
| 证据完整=1 | `FAIL` | E-03 超出闭合路径枚举，未形成可执行覆盖。 |
| 主张越级=0 | `PASS` | 无实验/科学/C/S/部署/正式资格主张。 |
| 原始记录损失/覆盖=0 | `PASS` | T7 日志保留，源包未写；派生临时件按设计删除并留 hash。 |
| 越权或未计尝试=0 | `PASS` | 所有外部调用计数为 0，修复尝试保留。 |

先硬门后收益：计数修复漏检 0/2，收益未建立。成本不是预注册的等质量比较分支，且候选不可执行，所以不能把零模型调用解释为同质量降成本。

## 4. 选择与集合现实

- `selection_set=NOT_BUILT`，因此没有选择集选一个。
- `sealed=NOT_APPLICABLE_UNRESOLVED`，访问次数 0；没有伪造封存访问。
- 选择结论：`NO_PROMOTION`。依据是候选 `NOT_EVALUABLE`、证据完整性硬门失败、0/2 修复、成本分支不可用、集合未构建。

## 5. 回滚演练

`rollback_receipt.json` 记录 T7 本地候选态恢复为 T5 v3 父文件：

- 三个父件的字节和模式与源完全一致；
- 回滚前后父验证均为 `ACCEPTED_WITHIN_SCOPE`；
- T4/T5/T6 与 11 件旧证据的 git blob、SHA-256、字节数、模式不变；
- 共享树无需回滚，因为候选从未启用；
- 未验证：真实部署中曾启用候选后的回滚，以及不存在的选择/封存集回滚。

## 6. 修复记录

四次失败均发生在候选评估开始前，详见 `repair_record.json`：未跟踪 A-1 的 HEAD 查询、0664 adapter 直执行、T1-INC-09 复合 fixture 字符串、A-1 诊断 adapter 直执行。修复均保留失败证据，不改源包；最终基线 22/22。

## 7. 三轴与措辞纪律

本包是 `DELIVERED / UNREVIEWED / NOT_ENABLED`。Loop A 不能自行填 `ACCEPTED`。R 的收尾验收与回滚演练通过不等于实验成功、科学成功、C/S 有效、生产资格或正式实验权限。

## 8. UNRESOLVED 与未验证面

- 执行对话 token 不可计量，保持 `UNRESOLVED`。
- 缺必需收据策略的候选严重漏检和合法误拦全行为 `NOT_EVALUABLE`。
- 选择集和封存集未构建。
- 无 Loop D、Loop B、C/S、生产、数据库、模型或跨机复制验证。
- 独立 Loop C 强评审待执行；强模型请求在本包为 0。
