# Loop A 任务：T8 v2 影子执行——三个真实任务（极简版）

你是 Loop A。在 GB10 上执行。只写 `runs/T8/<新run_id>/`。

## 直接做这五步（不需要读完整个项目）

### 步骤 1：创建 run 目录
run_id = UTC时间 + _ + UUID前8位。创建 `runs/T8/<run_id>/`。

### 步骤 2：冻结三个输入的 SHA-256
```bash
sha256sum docs/datasets/tatqa_licence_record_v1.md
sha256sum research/tatqa_wp0_2026/wp1/implementation_contract.md
sha256sum research/harness_rsi_v1/state/current.json
```
记录每个的 sha256 + bytes + 冻结时间。写入 `frozen_materials.json`。

### 步骤 3：窗口 1——TAT-QA 许可记录检查
**旧流程**：
```bash
python3 -c "
import json, hashlib
raw = open('docs/datasets/tatqa_licence_record_v1.md','rb').read()
print('bytes:', len(raw), 'sha256:', hashlib.sha256(raw).hexdigest())
# 检查关键字段是否存在
text = raw.decode('utf-8')
for kw in ['license', 'permitted', 'covered', 'accepted']:
    print(kw, 'found:', kw.lower() in text.lower())
"
```
**新流程**：用 T5 v3 的 `caller_validator.py` 对同一文件做 recipe 检查。
**产出**：`shadow_task_1.json`（含旧结果、新结果、对比）

### 步骤 4：窗口 2——WP-1 合同哈希校验
**旧流程**：
```bash
sha256sum research/tatqa_wp0_2026/wp1/implementation_contract.md
cat research/tatqa_wp0_2026/wp1/implementation_contract.sha256
```
比较两者是否一致。
**新流程**：用 T5 v3 的 recipe 对同一文件做哈希绑定验证。
**产出**：`shadow_task_2.json`

### 步骤 5：窗口 3——状态一致性审计
**旧流程**：
```bash
python3 -c "
import json, os
d = json.load(open('research/harness_rsi_v1/state/current.json'))
for t in d['accepted_tasks']:
    run_dir = f'research/harness_rsi_v1/runs/{t}'
    exists = os.path.isdir(run_dir)
    print(f'{t}: run_dir={exists}')
"
```
**新流程**：用 T5 v3 的 recipe 做结构化验证。
**产出**：`shadow_task_3.json`

### 步骤 6：生成标准包件
- `shadow_comparison.json`：汇总三个窗口的对比
- `release_proposal.json`：基于结果的建议
- `rollback_receipt.json`：PASS_READ_ONLY（材料只读）
- `receipt.json`、`summary.md`、`artifacts_manifest.json`、`events.jsonl`、`TASK_PROMPT.md`（逐字复制本任务书）

## 约束
- 零模型调用、零网络；只读被检查材料；G1 守卫全绿。
- T5 v3 recipe 调用方式：读 `research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/recipe_fixtures/README.md` 了解入口。
- 停止条件：无法执行某窗口时如实记录 NOT_EVALUABLE 并继续其他窗口。

## 交付回复
- run 目录绝对路径；
- 三个窗口各自旧/新结果摘要；
- shadow_status；
- self_check；
- usage（模型 0）；
- UNRESOLVED。
