# T4 R 适配器与基线

## 结论

- 交付 4 个只读路由适配器，未修改旧工具、git index、冻结清单或 T3 runner。
- T1 v3 的 16 个案例均已建立案例→检查映射；仅构造 11 个可离线、只读、最小复盘组合。
- 两轮回放 11/11 组合退出码一致；实际适配器检查 22 次，自动重试 0。
- 案例画像：detected 6、missed 2、not_applicable 2、unverified 6；两个合法对照均未被误拦。
- 旧流程画像：dispatch precheck 覆盖 3/16；summary guard 覆盖 7/16；MD5 清单核验覆盖 1/16。未覆盖不等于通过。

## 自检

| 断言 | 结论 | 级别与范围 |
|---|---|---|
| A1 | PASS | `CONTRACT_PASS`：仅 T4 包内模型/环境/案例/评价器身份完整性 |
| A2 | PASS | `CONTRACT_PASS`：仅 T4 本地 11 组适用组合的两轮退出码一致性 |
| A3 | PASS | `CONTRACT_PASS`：仅 B0 计数与写入边界；无科学、在线或 Loop B 执行 |
| A-common | PASS | `CONTRACT_PASS`：JSON、字段、证据存在性、声明哈希与边界 |

修复记录：自检先因 T1 可选 source-ref 元数据比较过严而失败；改为精确比较 path/hash/domain。随后发现 22 条证据路径为未记录猜测，已全部替换为 `events.jsonl` 对应的真实工具输出路径并复验存在。

## 未验证与阻断

- 未验证：预算超限、覆盖拒绝、导入冒烟、在线参数顺序、原始证据清单、双哈希域裁决。
- `formal_experiment_preflight.py` 未运行：没有获准 FinQA/formal manifest，且不把专用资格泛化为通用资格。
- 执行对话 token 不可计量，保持 `UNRESOLVED`；T4 包为 `DELIVERED / UNREVIEWED / NOT_ENABLED`。
- 无执行阻断；后续仅进入独立 Loop C 评审，不进入 T5。
