---
id: TASK-20260901-DR4
risk: low
window: zero-endpoint-anytime
status: 定稿（预注册后执行）
premises:
  - id: P1
    claim: "D1 工件冻结在位（all_pass=true）且含 item 级证据（uid / type / mechanism / canonical_keyset_identical / carriers）"
    falsify: "python3 读 gates.all_pass + payload 键存在"
  - id: P2
    claim: "逐实例 mutation 定义可取（D1 工件 / 注入语料 / T2 等价更正工件）, 覆盖 118 注入"
    falsify: "执行时枚举抽样 5 例核对字段完整"
  - id: P3
    claim: "零端点（自证口径承 D1: AST 作用域检索 + ports 自证 + 冻结件只读）"
    falsify: "运行时断言 + 静态检索"
acceptance:
  - "118 注入逐实例 Step 1 oracle 判定（E/H 标签 + 三项判据逐条证据）"
  - "与现行分类（H85/E7/HI26, E 集 = T2 冻结 7 uid）的 diff 全表"
  - "工件 logs/graph/eval/dr4_d1_reclassification_review.json + 报告（SUMMARY-GUARD 收据）"
rollback: "git revert; 冻结件只读零改动"
redlines:
  - "零端点; D1/T2 工件只读; 不溯及（产出 = 更正记录 + 未来输入, 不改写 D1 报告）"
  - "甲方标识零进入; 禁 git add -A / amend"
skills:
  - "graph-loop-rules（红线常备）"
  - "verify-before-done"
  - "executing-plans"
---

# 任务卡 DR-4 复核: D1 现行分类按 Step1/2 标准复核（零端点）

> 派发载体: Loop A（GB10, --profile loopa-exec）| 单窗零端点 | 依据: DR-4 重写（D1 autopsy 决策记录, 09-01）+ 专家第 2 轮 §5（独立 oracle / instance-level）
> 窗口类型: 零端点窗（不限时段）。与 D3 重派并行, 工件域不相交（本卡只读 D1/T2, 产出独立件）。

## 1. 目标

按 DR-4 重写后的 Step 1 标准（独立 oracle, 运行前冻结等价）对 D1 现行三分类做逐实例复核, 输出实例级 E/H 标签与现行分类的 diff。零端点, 只读。

## 2. 预注册（冻结, 执行后不溯及; 推导门/经验预测分列）

- **G-1（推导门）**: 复现现行分类 H85/E7/HI26 + E 集 7 uid == T2 冻结集（alias4+prefix3）; D1/T2 工件 sha 前后等。失配 → 停报。
- **G-2（推导门）**: 零端点自证（ports=[] / 无模型调用 / AST 检索）+ 冻结件只读。
- **E-1（经验）**: 实例级 oracle 复核与现行分类的 diff 为零或非零皆合法; 非零 → 逐条列 item 级证据。
- **E-2（经验）**: diff 改变 E 集成员 → 更正记录 + D3 检出分母（111, 按现行分类冻结）敏感性注记（不溯及）; 不改变 → 稳健性检查入账。

**Step 1 oracle 判据（冻结, 复核前定死; 输入只允许 mutation 定义 + 规范真值映射 + 下游语义事实, 禁止输入任何检测/吸收结果——absorption 是 outcome 不是 criterion）**:
对每个注入实例, E(m)=1 当且仅当三条全真:
1. mutation 属预定义语义等价算子（设计意图 = 不改变标准字段集的变换: 同义别名 / 不改变字段集的前缀噪声等）;
2. 独立规范真值映射不变（gold 字段集 + 取值在变换前后一致）;
3. 下游目标语义不变（该表应抽取的字段值/问答语义不受影响）。
任一不真 → H（有害）。判定按实例, 不按类型一刀切。

## 3. 动作序

0. 前提一分钟证伪（P1-P3）。
1. 读 D1 item 级证据 + 逐实例 mutation 定义（含 T2 等价更正工件）。
2. 逐实例 Step 1 oracle 判定（确定性规则, 三项判据逐条证据入工件）。
3. 与现行分类 diff（含 26 HI 中是否有实例级应判 E 者, 及 85 H / 7 E 中反向者）。
4. 更正记录（diff 明细 + 机制）→ 工件 `logs/graph/eval/dr4_d1_reclassification_review.json` + 报告 + SUMMARY-GUARD 收据 + commit（逐路径）+ 汇报。

## 4. 中止与退出

- 中止: G-1 失配 → 停报; 逐实例 mutation 定义缺失 → 停报（不得自造）。
- 成功退出: 工件 + 报告 + 收据 + commit + 汇报（执行结果/工件路径/数字摘要 = 复核 118 实例 + diff 数与明细/红线自查/commit）。

## 5. 红线

零端点; D1/T2 工件只读; 不溯及（不改写 D1 报告, 只出更正记录）; 甲方标识零进入; 禁 -A / amend。
