# G3 证据复用策略开发报告 v1

日期：2026-10-23  
状态：`DEV_ONLY_MECHANISM_RESULT_NOT_THESIS_CONTRIBUTION`

## 1. 问题与边界

本报告核对 `REUSE_POLICY_RESULTS_V1.json` 和 `reuse_policy_experiment.py`，回答：
在观察新的输入 regime 之前，透明策略能否根据旧证据、依赖变化、输入范围和精确输入匹配，在
`REUSE / PARTIAL_CHECK / FULL_CHECK / DEFER` 之间作出可复核选择，同时不增加错误迁移？

这是同一 Partridge 行为合同下的开发机制探针。结果不等于自然任务分布、修复成功率、Memory
学习收益或论文贡献。`20` 个 transition 是 `5` 个候选模块与 `4` 个开发场景的笛卡尔积，不是
`20` 个自然 family。

## 2. 证据粒度修复与动作合同

修复点是限制旧证据的使用粒度，而不是把 aggregate 结果伪装成逐输入结果：

- `REUSE`：精确输入匹配、依赖未变，且旧证据明确为 `per_input`；不执行新 probe。
- `PARTIAL_CHECK`：输入 regime 未变但输入不是旧的精确输入；只检查当前三个新输入。
- `FULL_CHECK`：依赖改变或输入 regime 改变；检查当前全部可用输入。
- `DEFER`：scope fingerprint 缺失，或旧证据只有 aggregate 粒度而无法支持精确输入复用；输出 `UNRESOLVED`。

因此，旧的 aggregate PASS 不能触发 exact-input `REUSE`。只有实际绑定到该输入的
`per_input` 证据才允许无检查复用；这条规则由 `test_aggregate_evidence_cannot_support_exact_input_reuse`
覆盖。

## 3. 实验单位与参考

- 候选：`partridge_parent`、`partridge_gold`、`partridge_source_fallback`、`partridge_alias`、
  `partridge_audit_counterexample`。
- 场景：`unchanged_exact_fixture`、`same_regime_new_fixtures`、`short_input_regime`、
  `missing_scope_fingerprint`。
- 总行数：`5 × 4 = 20` 个 development transitions。
- 行为参考：parent 派生的 decoded text 与候选 decoded text 比较；它不是新的人工 gold。
- 旧证据状态来自既有行为结果；exact-input 场景另外计算并绑定 `per_input` 旧证据。
- 隐藏 outcome 仅用于事后分类 `CORRECT / FALSE_ACCEPT / FALSE_REJECT / ABSTAIN`，
  不进入策略输入。

## 4. 结果

| 策略 | CORRECT | FALSE_ACCEPT | FALSE_REJECT | ABSTAIN | probe 数 | 非 REUSE 动作 | probe 动作 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `never_revalidate` | 12 | 2 | 1 | 0 | 0 | 0 | 0 |
| `dependency_change_only` | 12 | 2 | 1 | 0 | 0 | 0 | 0 |
| `exact_input_reuse_only` | 5 | 0 | 0 | 15 | 0 | 15 | 0 |
| `scope_policy` | 15 | 0 | 0 | 5 | 30 | 15 | 10 |
| `always_full_check` | 15 | 0 | 0 | 5 | 35 | 20 | 15 |

`scope_policy` 的动作分布是 `5 REUSE / 5 PARTIAL_CHECK / 5 FULL_CHECK / 5 DEFER`。
`always_full_check` 对可用输入总是 `FULL_CHECK`，在缺 fingerprint 时仍 `DEFER`。

因此，在这组开发 transition 上：

1. `scope_policy` 与 `always_full_check` 的正确、误放行、误拒和弃权计数完全相同；
2. `scope_policy` 少执行 `5` 个 probe（30 对 35，约少 14.3%），少执行 `5` 个非复用动作；
3. 节省来自 exact-input `REUSE`，不是来自跳过依赖改变或输入 regime 改变后的检查；
4. 单次 wall-clock 不用于稳定成本排序。`0.00232s` 对 `0.002968s` 只记录开发单次运行，
   不是性能结论。

## 5. 解释与限制

`never_revalidate` 和 `dependency_change_only` 的 2 个 `FALSE_ACCEPT` 都发生在短字节
输入 regime；这支持“只看依赖身份不足以判断旧证据是否仍适用”。`exact_input_reuse_only`
没有误放行，但 15/20 选择 `DEFER`，在缺少精确输入证据时过度保守。

新策略把旧的两 regime 结果推进为可执行的动作合同：同一依赖、同一输入的逐输入证据可以复用，
同 regime 新输入需要局部检查，条件改变需要全量检查，缺 fingerprint 则明确弃权。它减少了
无意义的全量重验，但没有证明真实修复决策、下游结果收益或经验学习机制。

必须保留以下限制：

- 5 个候选中只有 parent/gold 是自然模块对照，其余是真实仓库上的控制实现；
- 20 个 transition 不是自然 family，不能作为独立样本数；
- parent-derived decoded text 是本探针的行为参考，不是外部人工 gold；
- `DEFER` 计为 `ABSTAIN`，不能改写成成功或错误；
- 该探针不评估 repairer 是否采纳结果，也不评估 Memory 更新、检索或学习策略；
- 要升级为第三贡献，仍需第二个自然模块、独立变化轨迹以及真实下游修复/结果收益。

## 6. G3 与 G4 正文衔接

G3 第 5 章应写成“透明证据复用动作与 probe 成本的开发观察”，复杂 planner 保持暂停；
不能用本结果恢复旧 planner，也不能把 20 transition 写成自然任务规模。

G4 第 6 章可把当前材料组织为：

1. 旧证据必须携带输入粒度；
2. `REUSE / PARTIAL_CHECK / FULL_CHECK / DEFER` 是可审计的证据生命周期动作；
3. scope policy 在同等开发正确率下减少 probe，但只证明透明规则存在可利用的作用空间；
4. 机制成立还需要自然模块和下游结果，不应提前写成已验证的学习型 evidence expiry。

## 7. 证据绑定

- 结果：`REUSE_POLICY_RESULTS_V1.json`，SHA-256
  `0593d31c23cebb6fb40d602dadb44a3543cdb7fd32b58e88026bd9e4548697cb`。
- 实现：`reuse_policy_experiment.py`，SHA-256
  `4050337fc0e0d42498c02f2f845c26a165bc32357a38256c71071d3e224b9691`。
- 测试：`test_reuse_policy_experiment.py`，SHA-256
  `c84108f58b3b8e494ad67bc876dc377db4a13844abbcf90e8aedc3b653f59de5`。

本报告是分析和写作产物；本轮未运行新模型、未修改冻结结果，也未把开发结果登记为独立科学验证。
