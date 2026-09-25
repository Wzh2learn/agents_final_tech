# FinQA 步级 checkpoint 语料 v1（构建实测，2026-09-25）

> 状态: 证据件（Loop D）| 构建 head = `cff0a26c60dd755b4020f9d4dc6f2a084599b5ef` | 零模型、零端点、零下载
> 仪器: `research/finqa_step_checkpoint_adapter.py`（17 例合同测试）+ `research/phase1a_split_assign.py`（15 例）
> 产物位置: GB10 `/tmp/step_ckpt_20260925/`（仓外；语料与数据体永不入 Git）
> 设计约束: `docs/datasets/2026-09-25_finqa_process_structure_and_checkpoint_semantics.md`

## 1 结论摘要

1. 步级故障注入语料 v1 已在 GB10 构建完成，两个宇宙各一份，双跑逐字节相同，`observed_ports = []`。
2. 本件不发布任何检出率、定位率或分数。`measurement_status = CORPUS_ONLY_SCORER_NOT_PREREGISTERED`，
   `fault_spec.scorer = NOT_PREREGISTERED`，且单测机械断言摘要内不出现
   detection / localization / accuracy / f1 / tpr / precision / recall 任何键。
   语料先冻结、检测器后预注册，顺序不可颠倒。
3. 语料只覆盖已授权层：M=1 时层内 4 881 行全部来自 `proposal_train`（train + dev），
   另有 2 253 行因注册表 `role_fit` 未授权 gate/sealed 被分层仪器扣住
   （`ROWS_WITHHELD_PENDING_RULING:2253`），不在语料内。该状态由仪器逐字写入语料摘要的
   `inputs.layers_reasons`，不被掩盖。
4. 关键取舍实测：M=8 会丢掉 10 个 op 族中的 5 个（仅剩 divide / minus / add / multiply / sum；
   compare_larger、average、exp、max、min 全部为 0）。由于设计件要求按 op 族分层且稀有族单列，
   故 M=1 为主语料；M=8（286 UID，落在 D12 的 250-500 带内）只作规模受限的对照宇宙，
   不能承担族级分层结论。这是「UID 功效带」与「op 族覆盖」之间的真实冲突，如实入账。

## 2 输入与绑定

| 项 | 值 |
|---|---|
| 源文件 | `finqa/train.json` sha `49f237eb…`、`finqa/dev.json` sha `a847fb7e…`（运行时断言等于 SOURCE_GO 在案值） |
| 层工件 | 由 `phase1a_split_assign.py --namespace finqa --commit cff0a26…` 当场生成，非手填 |
| 层摘要校验 | 适配器运行时用合同 `_digest_object` 重算并与工件自报值比对；不符即 `layers_manifest_sha256_mismatch` |
| `layers_manifest_sha256` | M=1 `94379823654a6e75a925e65b367a802e29cd4016a2d85e6a949849b32a6d760b` · M=8 `9fc84f2bc627e63d8bf462d6104f23d20698675ec3422e92b1be481636d056a6` |
| seed | 42（显式必填参数，写入摘要；改 seed 即改选择，不改故障定义） |
## 3 实测计数（构建于 head `cff0a26`）

| 量 | M=1（主语料） | M=8（对照宇宙） |
|---|---|---|
| 层内行数 | 4 881 | 556 |
| 注入例数 = 语料记录数 | 1 970 | 212 |
| 单步例（计数不注入） | 2 911 | 344 |
| `no_admissible_fault` | 0 | 0 |
| 三项合计 = 层内行数 | 1 970 + 2 911 + 0 = 4 881，对账通过 | 212 + 344 + 0 = 556，对账通过 |
| 注入例内步数合计 | 4 583 | 498 |
| 故障族 | `res_scale` 1 235 · `arg_swap` 735 | `res_scale` 152 · `arg_swap` 60 |
| 按步数 | 2:1 564 · 3:253 · 4:74 · 5:74 · 6:5 | 2:163 · 3:31 · 4:12 · 5:5 · 6:1 |
| 按 op 族（步数） | divide 1 812 · minus 1 463 · add 961 · multiply 321 · compare_larger 8 · average 5 · sum 5 · exp 4 · max 2 · min 2（10 族全在） | divide 202 · minus 144 · add 87 · multiply 63 · sum 2（仅 5 族） |
| 按 partition | train 1 389 / dev 581 | train 131 / dev 81 |
| 语料字节 | 1 488 209 | 160 015 |
| 语料 sha256 | `03cf47c3576b7c42f4fddebc31dc4b3be1ee6cb9b38a9fa8b15850e80a900d3f` | `7f3ad6043b2bc0eceaf3ffe94859defb8435c62808db4879685d6080c384ed04` |
| 摘要件 sha256 | `b6a522cab1b0ed8cf30976b3f9db53df5d635385be3a493ac0aecaf320f76302` | `0bd322a59f187f5d049169a3026be435aeb145164fe585607371699c66da17f3` |

自校：M=1 按 op 族求和 1 812+1 463+961+321+8+5+5+4+2+2 = 4 583，等于注入例内步数合计；
M=8 为 202+144+87+63+2 = 498，同样对账通过。故障族求和等于注入例数（1 235+735 = 1 970；152+60 = 212）。

## 4 构建期发现并修复的一处实现缺陷（如实入账）

首次构建（head `e77be4d`）在 M=1 上给出 `injected = 1 967`、`no_admissible_fault = 3`。
根因：可用性是单步属性，而原实现只在盐化桶选中的那一步上判定，于是「选中步恰为交换族且
`res` 非数值」的例被整例丢弃，即使该例其他步完全可注入。这与规格「每个多步例恰一个故障」不符，
也与探针的例级可用性 2 893 / 2 894 属不同口径（探针 = 存在某步可用；原实现 = 选中步可用）。

修法（commit `cff0a26`）：起始索引仍由盐化桶决定、故障族偏好仍由独立盐化奇偶位决定，
可用性判定改为自起始索引按确定性环绕顺序扫描，取第一个可注入步；仅当全例无任何步可用时才记
`no_admissible_fault`。确定性、标签盲与预注册性质不变（扫描顺序固定，不依赖任何结果或分数）。
`fault_spec` 同步增补两个自描述字段：`index_selection = salted_bucket_then_deterministic_wraparound_scan`、
`admissibility_scope = per_candidate_step`。

修复效果实测：M=1 `injected` 1 967 → 1 970、`no_admissible_fault` 3 → 0；M=8 语料 sha256
逐字未变（`7f3ad604…`），即该修复只影响 M=1 上被误丢的 3 例，未扰动其他任何记录，这本身是
修复面收敛的一致性证据。新增 2 例单测直接锁住该行为：构造「第 0 步交换族 + 非数值 res + 两 arg
相等（两族皆不可用）、第 1 步非交换族 + 数值 res（两族皆可用）」的样本，断言 12 个不同 seed 下
均仍被注入且 `step_index == 1`；全例不可用时对 6 个 seed 均返回 None。
## 5 本语料不能支持的主张（写死）

- 不给出任何检出率、定位率、AUC、F1 或分数；无检测器即无指标。
- 不得被称为对冻结 Stage E 口径的「复现」「重算」或「替代」：那是表头注入族判别，本件是推理步
  检查点，两者是不同测量对象（见设计约束件 §2）。冻结数字 `85 / 7 / 26`、`drop_threshold = 2.0`、
  `τ_min`、分母 `111`、`TPR`、六族计数零改动、不溯及。
- 不得用于动作标签或可学性结论（`action_label_fit = PROGRAMS_ARE_NOT_MAP_HOLD_SKIP_LABELS`）、
  Stage D 蒸馏、学生模型或 RQ2 确认性证据（同样本桥不存在，RQ2 维持 `NOT_IDENTIFIED`）。
- 语料覆盖范围只到已授权层；被扣住的 2 253 行（M=1）不在其中，任何按「全量 FinQA」口径的陈述
  都不成立。

## 6 下一步（需先预注册，本批不执行）

1. scorer 预注册：在语料 v1 冻结后单独成件，先写死检测器定义、判定阈值、分层报告口径与正反例，
   再运行。候选类别须显式区分「确定性重执行型」（零模型）与「模型型」；模型型受调用预算硬上限
   约束（<200 含 canary 与重试），故必须自带有界抽样预注册，不得对 1 970 例逐例调用。
2. 独立 Loop C 审计本件与语料构建链（生成者不自验）。
3. 若 G-A..G-E 裁定改变了层的授权范围，语料须按新 layers 重建并重编版本（v2），不原位改写 v1。

## 7 红线自查

- 零模型、零端点、零下载；`observed_ports = []`；connect 即抛（守卫在两套运行器内均生效）。
- 数据体与语料不入 Git：产物在 GB10 `/tmp/step_ckpt_20260925/`（合计 5.6 MB），本件只记计数与哈希。
- 未改冻结判据 / 冻结 hash / 冻结 Stage E 口径与数字；未改协议、注册表、合同与任何守卫逻辑。
- 未覆盖 production 脏件（GB10 脏件仍为原五件）；未重启 daemon 与 :5050。
- 逐路径 add，无 `-A`、无 `--amend`、无 `--no-verify`、无破坏性命令；不外发、不上 arXiv、不公开代码。

## 8 复现

```bash
# GB10，仓库根；STAGE=~/wzh/phase1a_staging_20260925
venv/bin/python -m pytest tests/test_finqa_step_checkpoint_adapter.py tests/test_phase1a_split_assign.py -q  # 32 passed
venv/bin/python research/phase1a_split_assign.py --namespace finqa --staging-root "$STAGE" \
  --sha256-manifest "$STAGE/sha256_manifest.txt" --m-universe 1 --commit "$(git rev-parse HEAD)" \
  --out /tmp/layers_m1.json
venv/bin/python research/finqa_step_checkpoint_adapter.py --staging-root "$STAGE" \
  --sha256-manifest "$STAGE/sha256_manifest.txt" --layers /tmp/layers_m1.json --seed 42 \
  --commit "$(git rev-parse HEAD)" --out /tmp/summary_m1.json --out-corpus /tmp/corpus_m1.jsonl
# 再跑一次到另一路径：摘要与语料均应逐字节相同（产物无墙钟字段）
```
