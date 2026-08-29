---
id: TASK-20260830-01
risk: low
window: approved
premises:
  - id: P1
    claim: "GB10 drift_v0 语料在位: data/research/drift_v0/output/{injected_tables.json,injection_map.json} + sample_injected_tables.json（95 表 / 118 注入）"
    falsify: "python3 -c \"import json;d=json.load(open('data/research/drift_v0/output/injection_map.json'));print(len(d['mapping']))\" 输出 118"
  - id: P2
    claim: "四件冻结基线工件在位可读（checkpoint_discrimination_tables_v2 / checkpoint_discrimination_report / pso_weight_search_v0 / p1_correctness_backfill .json）"
    falsify: "ls logs/graph/eval/checkpoint_discrimination_tables_v2.json logs/graph/eval/checkpoint_discrimination_report.json logs/graph/eval/pso_weight_search_v0.json logs/graph/eval/p1_correctness_backfill.json"
  - id: P3
    claim: "matcher 可导入（scripts/m1_statement_parser.py map_headers/normalize_header/_best_field_for_header）"
    falsify: "cd 项目根 && python3 -c \"import sys;sys.path.insert(0,'scripts');import m1_statement_parser as mp;print(mp.normalize_header('Total Assets (元)'))\" 输出 totalassets元 的归一化结果"
  - id: P4
    claim: "臂 A 树配置与聚合参考实现在位（config/eval_checkpoint_trees.json + scripts/eval_checkpoint_aggregate.py）"
    falsify: "ls config/eval_checkpoint_trees.json scripts/eval_checkpoint_aggregate.py"
  - id: P5
    claim: "本窗零端点: 三个执行脚本无任何网络调用/模型调用"
    falsify: "grep -nE 'urlopen|requests\\.|http://|https://|:800[0-9]|:5050' research/paper_t1_eval_baselines.py research/paper_t2_visibility_sensitivity.py research/paper_t6_matching_competition.py（命中仅允许出现在注释/断言字符串）"
acceptance:
  - "复现门 G1: T1 臂 A E1.3 重算逐 mutant root_scores 与冻结报告误差 <0.01; 臂 B 表级判别 75/95 逐表一致"
  - "复现门 G2: T1 臂 A E1.4 PSO 均值分离度 1.4326±0.01, 最差（M7）0.093±0.01"
  - "复现门 G3: T2 S 档重算 = 冻结工件 75/95 + by_type 六类计数误差 0"
  - "复现门 G4: T6 贪心臂重算 = 冻结工件逐表一致; oracle 0.952381/0.597015 误差 <1e-6"
  - "python3 重算命令可复现全部数字（工件内含 payload sha256）"
rollback: "回滚 = git revert 各段 commit（工件均为新文件）; 冻结工件全程只读, 无回滚需求"
redlines:
  - "甲方数据零进入（TAT-QA 公开底座 + 合成注入）"
  - "零端点: 零网络调用零模型调用; 不得夹带 E1.5/E1.6（:8004, 归 T4 窗）"
  - "冻结节点/冻结工件零改动（frozen_hashes.txt 清单 + docs/experiments/ 已归档报告只增不改）"
  - "禁止 git add -A; 禁止 amend 已验证 commit; 只 add 本卡脚本与工件"
  - "T3/T5 不在本窗（解冻线/视觉线另行派卡）"
skills:
  - "graph-loop-rules（红线常备）"
  - "verify-before-done"
  - "executing-plans"
  - "systematic-debugging"
---

# 任务卡 W1: T1/T2/T6 零端点合并窗口（单会话三段顺序）

> 派发载体: Loop A（GB10 Codex CLI, tmux 直启, --profile loopa-exec）| 拟卡: Loop D 主线程 | 窗口: 用户已批（2026-08-30）
> 预注册设计稿（判据冻结, §1 均原样引用蓝图 §1）: 2026-08-30_t1_eval_baseline_comparison_design.md / 2026-08-30_t2_visibility_sensitivity_design.md / 2026-08-30_t6_matching_competition_design.md

## 1. 目标

按三份预注册设计稿完成 T1 E1.1-E1.4、T2 E2.1-E2.3、T6 E5.1-E5.2 全量执行: 三段各产一件日志工件（logs/graph/eval/t1_eval_baseline_comparison.json / t2_visibility_sensitivity.json / t6_matching_competition.json）+ 各段独立 commit, 复现门 G1-G4 全过, 全部数字可从工件复算。

## 1.5 Skill 装载清单

graph-loop-rules（红线常备）/ verify-before-done（完成门前证据）/ executing-plans（三段按 checkpoint）/ systematic-debugging（闸失败时根因, 不猜测式补丁）。

## 2. 前提假设清单

见 YAML premises P1-P5; 动作序第 0 步逐条证伪并记录实测结论。任一证伪 → 停下改道或报用户, 不带假设硬跑。

### 2.1 交互假设检查

| 变更对 | 共享资源/假设 | 冲突验证方式 |
|---|---|---|
| 段 T1 × 段 T2 × 段 T6 | git worktree + logs/graph/eval/ 目录 | 三段工件文件名互不重叠（t1_/t2_/t6_ 前缀, 一分钟核对: 设计稿 §5 工件名三行互异）; 顺序执行天然串行 |
| 本窗 × Loop B 30min 周期 | git worktree（Loop B pull/verify） | Loop B 只触白名单运行时文件, 不触本窗新增文件; 若 Loop B 周期 FAIL 与本窗无关（如 agent_watchdog 波动）, 只记账不处置 |

### 2.2 预注册预测（照设计稿 §4, 冻结数字汇总）

- T1: G1/G2 复现门必过（否则 = 重算实现错误, 修到过大闸）; 臂 A 四协议分离度表 + 臂 B 三协议检出表完整产出; E2E 检出率 ≥ 分层协议但定位率 = 0（预测, 违反如实报告）。
- T2: ocr_similar 全 γ 网格可见率 = 0; 类型不均匀（极差）全网格 ≥0.5; 等价变异 ≈7 条（alias 4 + prefix 3, 以实算为准）, 校正后主结论存续; 强度梯度单调性（W≤S; ocr S'=0%→≥10/13）。
- T6: 贪心臂复现冻结结果; oracle 复现 0.952381/0.597015; Hungarian vs 贪心差异双分支（差异≈0 → 竞争不可由分配层消解; 差异显著 → 列翻转清单）, 不预设分支。

## 3. 动作序

0. 前提证伪: P1-P5 逐条, 实测结论记录（全 PASS 才继续）。顺带: logs/graph/eval/pso_weight_search_v0.json 若仍未入库, 本段同批 git add 入账（既有工件入库, 非新产）。
1. 段 T1（照 t1 设计稿）: 实现 research/paper_t1_eval_baselines.py（纯 stdlib, seed=20260830, 零网络断言）→ 跑 → 工件落盘 → 过 G1/G2 → `git add research/paper_t1_eval_baselines.py logs/graph/eval/t1_eval_baseline_comparison.json`（+ pso 工件若在第 0 步未入）→ commit `feat(research): T1 评测基线对照 E1.1-E1.4 零端点执行`。
2. 段 T2（照 t2 设计稿）: 实现 research/paper_t2_visibility_sensitivity.py → 跑 → 工件落盘 → 过 G3 + §4 判据 → `git add research/paper_t2_visibility_sensitivity.py logs/graph/eval/t2_visibility_sensitivity.json` → commit `feat(research): T2 可见性敏感性 E2.1-E2.3 零端点执行`。
3. 段 T6（照 t6 设计稿）: 实现 research/paper_t6_matching_competition.py（Hungarian 纯 stdlib O(n^3)）→ 跑 → 工件落盘 → 过 G4 + 双分支记录 → `git add research/paper_t6_matching_competition.py logs/graph/eval/t6_matching_competition.json` → commit `feat(research): T6 匹配竞争控制 E5.1-E5.2 零端点执行`。
4. 收尾: 三段汇报字段（§6）写入 logs/graph/eval/w1_window_report.md 并 commit（Loop A 自报, 主线程抽验）。

段间纪律（窗口合并卡先例）: 段间不互锁——前段失败不阻后段启动; 单段闸失败 → 该段改期重跑 ≤2 次, 仍失败 → 该段标 BLOCKED 如实入账, 禁止静默跳过; 其余段照常。

## 4. 中止与退出条件

- 中止: 前提 P1-P5 任一证伪 / 发现需要端点才能完成设计稿内容（= 设计稿与冻结口径冲突）→ 停下报用户, 不擅自改设计稿。
- 成功退出: 三段工件 + 三（四）个 commit + G1-G4 全过 + §6 汇报字段齐。
- 失败退出: 单段重跑 2 次仍不过 → 该段 BLOCKED 入账, 其余段照常收口。
- pivot: 冻结工件与设计稿预期不符（如 PSO 工件结构与文档不符）→ 如实记录差异 + 按工件实况执行 + 汇报标注, 不静默改判据。

## 5. 验收证据表

| 声明 | 验证命令 | 实测值 |
|---|---|---|
| G1 臂A root_scores 误差<0.01 | 工件 payload.gates.g1_max_err | （Loop A 填） |
| G1 臂B 75/95 逐表一致 | 工件 payload.gates.g1_armb_tables | （Loop A 填） |
| G2 PSO 1.4326/0.093 | 工件 payload.gates.g2_* | （Loop A 填） |
| G3 S 档复现误差 0 | 工件 payload.gates.g3_* | （Loop A 填） |
| G4 oracle 复现 | 工件 payload.gates.g4_* | （Loop A 填） |
| 零端点自证 | grep 网络调用模式零命中（除注释） | （Loop A 填） |

## 6. 汇报格式（Loop A 收尾必填, 主线程抽验）

执行结果（三段各一行: PASS/BLOCKED + 关键数字）/ 工件路径（三件 + 报告）/ 数字摘要（G1-G4 实测 + T2 五组关键数 + T6 分支归属）/ 红线自查（五条逐项）/ commit hash ×3-4。

## 7. 红线

见 YAML redlines。另: :8006 零触碰（canary 争用源）; 甲方样本目录 ~/wzh/m1_samples/ 零进入; 专利终态件只读。

## 8. 执行节奏纪律

照模板 §8 全局规则; 本窗零端点无里程碑等待, 一气执行; 禁止 >5min sleep。

## 9. 事后复盘（Loop A 收口必填）

- 结果 / 关键洞察 / 推翻的旧判断（如有, 必带 supersede 指针）/ 喂给了什么（T4 窗 / T7 写作）。
