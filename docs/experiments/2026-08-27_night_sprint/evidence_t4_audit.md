# T4 Loop C 差分审计证据（骨架 v2.2 × 工件, 2026-08-27）

方法: differential-review + spec-to-code-compliance 口径——骨架数字逐条从原始工件重算, 不用二手转述; 判定为机械比较, 格式化差异单列。

## 1 骨架数字 × 工件（7 条全一致）

| 骨架数字 | 骨架值 | 工件复算值 | 工件源 | 裁定 |
|---|---|---|---|---|
| 两臂 holdout 终值 | 0.589048 | 0.589048 / 0.589048（gated/ungated 各自） | vgmc_exp1_results.json `arm_*[h_meas_final]` | 一致 |
| 门控拒条数与性质 | 4 条全 gain=0 泛化别名误猜 | 4 条, 全 gain=0.0=True（sales/turnover/帐号/营业收入→错误目标） | vgmc_exp1_checkpoint.json `arm_gated.sugg_log` | 一致 |
| 网格 tau=0.1 接受数 | 38/42 | 38/42 | vgmc_exp1_results.json `grid_replay["tau=0.1,eps=0.02"]` | 一致 |
| 基线 H | 0.6430/0.5581 | 0.6430/0.5581 | vgmc_exp1_results.json `meta.baseline_no_rules` | 一致 |
| K2 表级判别 | 75/95 | 75/95 | checkpoint_discrimination_tables_v2.json `properties.discrimination` | 一致 |
| K2 注入级可见 | 96/118 | 96/118（按六类求和） | 同上 `by_type` | 一致 |
| OCR 静默吸收 | 13/13 | 13/13（可见率 0.0） | 同上 `by_type.ocr_similar` | 一致 |

## 2 口径裁定: "固化代价 4/53"（骨架 §1）vs "门控拒 4/42"（昨夜汇报/commit）

**裁定: 门控拒绝口径分母 = 42（门控实际评估的建议数）; 53 = gated 臂建议总数 = 42 gate 评估 + 11 no_map（LLM 未给出映射, 未经门）。** 复算证据: `accepted=38; 未固化合计 15 = no_map 11 + gate 拒 4`。两口径数值本身都"算得出来", 但语义不同: 4/53 把"建议器没给映射"混入"门控拒绝", 稀释门控拒绝率（9.5% → 7.5%）。**建议骨架正文改注"门控拒 4/42（建议总数 53, 含 no_map 11）"**——骨架为侧线资产, 主线程只报不改, 本行即报侧线的一行裁定。

## 3 mapping 刷新状态 × git log 交叉核对

| mapping 标注 | git 实证 | 核对 |
|---|---|---|
| Gap1 closed@34c93ab | K2 工件实际引入于 **0cbced5**（git log --diff-filter=A 坐实）; 34c93ab = 其后一个 dispatch 归因提交 | 段标有效, 精确引入点 = 0cbced5（mapping 沿用用户口径不改, 此处记账） |
| Gap2 closed@ce85736 | vgmc_exp1_results.json 等工件引入于 ce85736（--diff-filter=A 坐实） | 一致 |
| Gap5 closed 同批@ce85736 | 网格重放在 vgmc_exp1_results.json 内, 同 ce85736 | 一致 |

## 4 发现逐条
1. 7 条骨架数字全部复算一致, 无漂移
2. 4/42 vs 4/53 分母口径歧义——裁定如上, 报侧线, 骨架正文未动
3. closed@34c93ab 精确引入点为 0cbced5（段标沿用不改, 记账）
4. 其余: 骨架 §4 #10 "23+53" 样本数本日实测复验（生产 23 条无实测结果字段 / 实验 53 条 42 带测）, 与台账"审计完"口径吻合
