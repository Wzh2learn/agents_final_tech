# K3 schema 漂移注入器 v0 — 注入数据集 + 统计报告（VGMC 实验 1 输入）

> 状态: 活跃 | 更新: 2026-08-18 | 类型: K3 科研探索产出（纯确定性脚本, 不调用任何 LLM/推理/Web 端点）
> 依据: docs/33 §9 K3 任务卡 + §5 数据集策略（公开底座: TAT-QA 首选）
> 红线遵守: 独立 venv `~/wzh/venvs/k3_drift`（只装 pandas/pytest）; 未触碰生产 venv、:5050/:8004/:8006/:8007、甲方样本与 `config/m1_table_schema.json`（仅作注入类型灵感, 只读）

## 1 交付物

| 文件 | 说明 |
|---|---|
| `scripts/research/drift_inject.py` | 注入器（确定性, 6 类分类学, CLI + 库 API） |
| `data/research/drift_v0/sample_injected_tables.json` | 注入样本（95 表, 含 original/injected 对照, 105 KB, 已 commit） |
| `data/research/drift_v0/output/{injected_tables,injection_map,report}.json` | 全量输出（gitignored, 复现命令见下） |
| `data/research/drift_v0/input/tatqa_tables.json` | TAT-QA 归一化输入（gitignored, 1.4 MB） |
| `tests/test_drift_inject.py` | 8 项测试: 确定性复现 + 6 类各至少 1 例 + 映射一致性 |

## 2 数据源（按序尝试）

- **首选: TAT-QA raw JSON 成功**（GitHub `NExTplusplus/TAT-QA` master, dataset_raw 的 train + dev）。
- 归一化: 2201 (train) + 278 (dev) = **2479 表**（每表首行表头, 其余为数据行）; 无重复 uid; 列数 3–9。
- 未使用 FinTabNet（TAT-QA 表小量轻, 已满足; 下载即止, 不恋战）。失败项: `NextOpenSource/TAT-QA`（404, 仓库已迁移/改名为 NExTplusplus）——如实记录, 不影响结果。

## 3 注入类型分类学（6 类, 每类有种子可复现）

| 类型 | 含义 | 词库/策略 | 注入数 (ratio=0.3, seed=42) |
|---|---|---|---|
| `alias_variant` | 别名变体（简称/全称/中英行业术语） | 21 组语义键 × 多候选项, 命中词匹配 | 47 |
| `date_variant` | 日期变体（对账日期/期末日期/净值日期/交易日/报表明细日期） | date 命中列 + 年份池 (2016–2021) × 4 模式 | 17 |
| `mixed_lang` | 中英混写 | 10→13 组双向混写模板 | 20 |
| `unit_suffix` | 单位后缀（元/万元/份额/股/手） | 8→13 组单位键 | 5 |
| `ocr_similar` | OCR 形近错认 | 12 组形近替换（按列内容匹配首个可替换对） | 13 |
| `prefix_noise` | 前后缀噪声（①②/序号/空格/标点） | 4 组装饰器 ×2 嵌位模式 | 16 |
| **合计** | | | **118**（95/2479 表被注入, 注入率 ≈3.8%） |

- 唯一熵源 = seed 派生的 LCG（跨 Python 版本稳定）; 每表一个独立流（uid+表序派生种子）。
- 注入映射清单字段: `uid / row / col / original / injected / type / source_key / variant / seed_component`（可逐条追溯）。

## 4 确定性契约（单测证明）

- 同 seed 同输入 → 输出字节级一致（`injected_tables.json / injection_map.json / report.json` 三文件）。
- 全量输出 sha256: `ebefc6f1a94b9c2679811c5db16c4c3b1f7aceeb59afeba15dc6444a1bc22555`（见 `output/report.json`）。
- 样本集 sha256: `58660f445983cdeeaf16a31e75bc01c1f8acc13b1d5e63b85db5e0a1b9d31317`。
- 测试覆盖: 同进程复现、跨 seed 必不同、6 类各 ≥1 例、注入必变化、映射↔输出一致性、未注入列零漂移。

## 5 VGMC 实验 1 用法说明（注入表 → LLM 建议 → 门控 → 规则落库 → --no-llm 复测）

1. **注入表**: 本数据集（或任意 TAT-QA/FinTabNet 子集）作为 `--input` 输入注入器。
2. **LLM 建议**: 对注入表调用 schema 自学习端（M1 候选建议管线, 只读; 本项目 :5050 侧, 实验侧另行实例化）。
3. **门控**: 建议被接受当且仅当 `ΔH(s) ≥ τ_acc` 且基线无退化（docs/33 §4 固化门公式）。
4. **规则落库**: 被接受建议写回 schema 规则表（实验侧），下一轮注入↔gating 复用。
5. **--no-llm 复测**: 对同一注入表跑确定性规则映射, 对比命中率提升与 LLM 介入次数衰减（学习曲线 λ(t) vs H(t)）; 本数据集即该复测的固定输入。

复现命令（在 k3_drift venv 内）:
```
~/wzh/venvs/k3_drift/bin/python scripts/research/drift_inject.py \
  --input data/research/drift_v0/input/tatqa_tables.json \
  --out data/research/drift_v0/output --ratio 0.3 --seed 42
```

## 6 边界与后续

- 种子样本 = 95 表（全量注入表子集, 含 original/injected 对照）; ≤2MB 约束满足（105 KB）。
- 词库稀疏面: 单位后缀在 TAT-QA v0 全量仅命中 5 例（表小、数值单位多在元组内）; 后续版本可提高 ratio 或扩键。
- 原始大表与全量输出不入 git（gitignore 显式规则 + 负向豁免 report/sample）; 复现即得。
- 甲方样本/配置零进入; 所有词库为公开行业术语与 OCR 形近对。

**验收自检**: pytest 全绿; 同 seed 复跑输出一致（测试证明）; 映射清单字段完整; 统计数字与样本一致。
