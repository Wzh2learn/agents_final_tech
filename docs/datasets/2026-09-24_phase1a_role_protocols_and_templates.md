# Phase 1a 角色协议与模板 v1（label_ledger 复核协议 / licence_record 模板 / manifest 模板）

> 状态: 协议件（2026-09-24, Loop D）| 零数据体、零模型调用、零下载
> 目的: 把七个缺失角色中「协议先行」的三件固化成可执行模板，待数据批准后即可填充；
> 本件**不是** package，也不位于任何 package root；`research/phase1a_data_contract.py` 对其无感知，
> validator 在角色填齐前必须继续拒绝——这是设计目标，不是缺陷。
> 已填哈希于 2026-09-24 在 GB10 production 只读复核（sha256sum + wc -c），与 DATA_NO_GO 加记逐字节一致。

## 1 label_ledger 独立复核协议（生成者不得自审）

行 schema 与合同 `LABEL_FIELDS` 逐字段对齐：`sample_id / uid / col / gold_action / gold_target /
quality_grade / reviewers / adjudication`；`quality_grade` 固定 `Q3`；`gold_action` 与 reviewer/adjudicator
的 `action` 取值受合同 `_valid_choice` 约束（VALID_ACTIONS = map_to / skip / hold，target 规则同合同）。

1. **角色分离**：草案生成者（规则派生脚本或批准下载后的转录流程）不得担任 R1 或 R2；R1 与 R2 必须使用
   互不相同的判定载体（不同模型 + 不同 prompt 模板，或一人一机）；adjudicator 不得属于 reviewer_ids。
2. **分歧处理**：两审一致时 gold 必须等于该一致选择（合同 `gold_review_mismatch` 强制）；不一致时必须存在
   `adjudication = {adjudicator_id, action, target, rationale_ref}`，且裁决选择等于 gold
   （合同 `missing_adjudication` / `invalid_adjudication` / `gold_adjudication_mismatch` 强制）。
3. **留痕**：ledger meta 记录 R1/R2/adjudicator 载体标识、prompt 模板版本、逐行分歧表与总体一致率；
   一致率只作诊断统计，不作门。
4. **独立复核**：LABEL_GO 之前由未参与生成的 Loop C 证据包审计复核协议执行与抽样行（审计者只读）；
   生成者自签无效。
5. **出处**：gold 来源二选一——批准下载后的公开 gold（记录 dataset_id + revision + 下载时间 + 批准引用），
   或可追溯规则派生（记录 rule id + commit + 派生脚本 sha256）；二者都不得混用于同一行。

## 2 licence_record 模板（接受行为保留给用户）

```json
{
  "status": "PENDING_USER_ACCEPTANCE",
  "accepted_by": "PENDING_USER",
  "accepted_at": "PENDING_ISO8601",
  "permitted_uses": ["training", "tuning", "evaluation", "rule_acceptance"],
  "covered_artifact_sha256": {
    "source_tables": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    "injection_map": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
    "schema": "PENDING_ROLE_HASH",
    "label_ledger": "PENDING_ROLE_HASH",
    "learnability_feature_ledger": "PENDING_ROLE_HASH"
  },
  "license_scope_quotes": {
    "finqa": "MIT License, Copyright (c) 2021 Zhiyu Chen (verbatim excerpt in provenance doc)",
    "convfinqa": "MIT License, Copyright (c) 2022 Zhiyu Chen (verbatim excerpt in provenance doc)",
    "valentine_nyc": "Apache License Version 2.0, January 2004 (verbatim excerpt in provenance doc)"
  },
  "coverage_review": "PENDING_LEGAL_REVIEW: whether repo licences cover the data files is a legal judgement, not made here"
}
```

两个已填哈希对应 `data/research/drift_v0/input/tatqa_tables.json`（1 442 890 B）与
`data/research/drift_v0/output/injection_map.json`（36 004 B），2026-09-24 在 GB10 只读复核；
`status` 只有在用户签署后才可改为 `accepted` 并填 `accepted_at`（合同 `licence_not_accepted` /
`missing_acceptance_owner` / `invalid_acceptance_time` 强制）。

## 3 phase1a_manifest 模板（骨架，非 package）

```json
{
  "contract_version": "phase1a-data-package-v2",
  "artifacts": [
    {"id": "src_tables", "role": "source_tables", "path": "data/research/drift_v0/input/tatqa_tables.json",
     "bytes": 1442890, "sha256": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302"},
    {"id": "inj_map", "role": "injection_map", "path": "data/research/drift_v0/output/injection_map.json",
     "bytes": 36004, "sha256": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e"},
    {"id": "PENDING", "role": "schema", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"},
    {"id": "PENDING", "role": "label_ledger", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"},
    {"id": "PENDING", "role": "licence_record", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"},
    {"id": "PENDING", "role": "confidence_manifest", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"},
    {"id": "PENDING", "role": "analysis_plan", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"},
    {"id": "PENDING", "role": "parser_contract_receipt", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"},
    {"id": "PENDING", "role": "learnability_feature_ledger", "path": "PENDING", "bytes": null, "sha256": "PENDING_ROLE_HASH"}
  ],
  "bindings": {
    "label_ledger": "PENDING_ARTIFACT_ID",
    "learnability_feature_ledger": "PENDING_ARTIFACT_ID",
    "licence_record": "PENDING_ARTIFACT_ID",
    "confidence_manifest": "PENDING_ARTIFACT_ID",
    "analysis_plan": "PENDING_ARTIFACT_ID",
    "parser_contract_receipt": "PENDING_ARTIFACT_ID"
  },
  "layers": "PENDING_SPLIT_GO",
  "future_replay": null,
  "future_replay_note": "LONGITUDINAL_EVIDENCE_UNAVAILABLE until the hash-bound acquisition protocol is executed"
}
```

填充顺序受依赖约束：schema → layers(SPLIT_GO) → label_ledger(LABEL_GO) → confidence_manifest →
learnability_feature_ledger → parser_contract_receipt（GB10 实跑）→ analysis_plan（需 layers 摘要）→
licence_record（最后签署）→ 双次 deterministic precheck（byte-identical、零 connect）→ 独立复核。

## 4 红线

- 不下载数据体；不解冻 TAT-DQA；旧 TAT-QA 池仍 HISTORICAL_ONLY；不伪造任何哈希或字节数；
- 已填两项哈希仅陈述现存冻结工件，不引入新数据使用；
- 本件任何模板在填齐前不得被当作 package 传给 validator 或任何 runner。
## 5 confidence_manifest 草案（今日即可填齐的角色，2026-09-24）

零模型探针（GB10，raw.githubusercontent 于记录 head）：finqa README.md 6 518 B / sha256 前 16 位
`eb86779cfed6f0a2` / confidence 提及 0；convfinqa README.md 6 164 B / `c5f329640aaffa14` / 提及 0；
valentine README.md 14 635 B / `3d484bddcf124bca` / 提及 1（为示例代码中的匹配阈值
`high_confidence = matches.filter(min_score=0.7)`，**不是**逐行置信度字段）。
⇒ 三个选定来源均无原生逐行置信度字段；按合同唯一诚实填法即 `missing_policy = unmeasurable`。

草案件：`docs/datasets/phase1a_confidence_manifest_draft_v1.json`，五条合同条件镜像校验 5/5 通过
（field/source 非空、missing_policy=unmeasurable、gain_collateral_substitution=false、
allowed_values 集合等于 {low, medium, high}）。草案**不含任何测量置信度**，也不得被读作测量；
入 package 时须绑定 sha256 并经独立复核；未来若出现真实置信度字段，本草案整体替换并重审。
## 6 schema 角色裁定与 P1-future 草案（2026-09-24）

**当前 corpus（drift-v0，TAT-QA 派生）包的 schema 角色 = BLOCKED**。零模型探针：NExTplusplus/TAT-QA
@870accc41953dcde885aabeb963d94aabdc0fbc3 的 README.md（4 689 B，sha256
85c398173d771a2531abea5b81f3696914296642da2af78c2c34545715c14d5f）只在第 48 行记载
「We heuristicly generate the "facts" and "mapping" fields based on raw dataset, which are stored under
the folder of dataset_tagop」；逐表列级 schema 的官方记载在 ACL2021 论文与项目网站，二者均在已核验引用池外。
按「schema 只取所选公开数据源官方 schema/metadata」裁定，当前 corpus 包无法填齐该角色；
m1_table_schema 候选维持否决。

**P1-future 包（FinQA process/checkpoint 流）schema 草案 = DRAFT_COMPLETE_PENDING_PACKAGE_BINDING**：
官方字段文档取自 czyssrs/FinQA @0f16e2867befa6840783e58be38c9efb9229d742 的 README.md
（6 518 B，sha256 eb86779cfed6f0a253913761d8e4fabe032a29d9fcf2944e56c23bf007064605）第 31-47 行，逐字如下：

````markdown
The dataset is stored as json files in folder "dataset", each entry has the following format:

```
"pre_text": the texts before the table;
"post_text": the text after the table;
"table": the table;
"id": unique example id. composed by the original report name plus example index for this report. 

"qa": {
  "question": the question;
  "program": the reasoning program;
  "gold_inds": the gold supporting facts;
  "exe_ans": the gold execution result;
  "program_re": the reasoning program in nested format;
}
```
In the private test data, we only have the "question" field, no reference provided. 
````

草案件：`docs/datasets/phase1a_schema_draft_v1.json`（fields 九项、private_test 排除注记、scope 明确只属
P1-future 包）。探针只取 README/LICENSE 元数据，未取 dataset/*.json 任何数据体。
## 7 parser_contract_receipt 运行器规格（未来批实现，零模型）

- 产物须满足合同 gate `parser_contract`：`status=PASS`、`checker` 非空、`commit` 为 40-hex（运行时刻 repo HEAD）、
  `executed_at` ISO8601、`input_sha256` 覆盖 source_tables / schema / injection_map 且等于包内实际哈希。
- 检查程序（拟 `research/phase1a_parser_contract_receipt.py`）：对 95 张表逐一以生产头映射器
  （scripts/m1_statement_parser.py 的 map_headers）跑原表头与注入表头，按冻结 drop 规则
  （drop=(H_orig-H_inj)*10，阈值 2.0）记录逐表 drop 向量；与 logs/graph/eval/checkpoint_discrimination_tables_v2.json
  的 g3 不变量对账（75/95 判别、逐族计数、零 mismatch）；双跑 byte-identical。
- 零连接自证：socket 守卫仅允许本地文件 IO（镜像 w2 endpoint guard 模式），观测端口集记录为 []。
- 前置：schema 绑定存在（当前 corpus 包该角色 BLOCKED，见 §6；P1-future 包绑定后即可跑）。
- 验收：合同 gate 过 + 双跑一致 + 运行日志经独立 Loop C 审计；实现批须带正反例（篡改任一输入哈希必须
  parser_input_hash_mismatch）。

## 8 learnability_feature_ledger 派生规格（未来批实现，零模型）

- 输入：source_tables、schema、confidence_manifest、已接受的 label_ledger、层分配（proposal_train）。
- 逐样本行：sample_id 与 uid 取自层 manifest；observed_header 取源表头；canonical_fields 取 schema 映射；
  candidate_target = label_ledger 的 gold_target（action=map_to 时）否则 null；confidence 恒为 null
  （confidence_manifest 政策 unmeasurable）；family = 注入族（带注入样本）或 unperturbed。
- 九条约束镜像（addendum A）：顶层键集、contract_version=phase1a-feature-ledger-v1、三个跨角色 sha256 等于
  同包实际哈希、rows 非空、行键集 FEATURE_FIELDS、canonical_fields 非空唯一且 candidate_target 属其内、
  confidence ∈ {null, low, medium, high}、sample_id/uid 与 proposal_train 注册一致、行集恰好覆盖 proposal_train。
- 双跑 byte-identical；独立 Loop C 审计；生成者不得自审（派生脚本作者不签署验收）。

## 9 analysis_plan 模板与 PENDING 口径（2026-09-24）

模板：`docs/datasets/phase1a_analysis_plan_template_v1.json`。18 个必需键齐备；D8 批准起点值已填
（significance_level 0.05、target_power 0.80、risk_limit 0.10、delta_* 0.02、primary_metrics 两项、
cluster_unit=lineage_uid、seed_uid_aggregation 与 holm_adjustment 逐字、holm_families 含 H3a_uid_any_harm、
one_sided_p_value_methods 五键逐字引自合同 :946-953）。四处诚实 PENDING，模板在填齐前**必须**被合同拒绝：
- status/approved_by/approved_at：用户批准行为（合同要求 status 恰为 approved）；
- minimum_uid_by_role_family：PENDING_FAMILY_TAXONOMY（家族税制待 learnability 设计定稿；D11 要求与
  config min_dev_uids_by_family 去 proposal_train.dev/ 前缀后键值全等）；
- mde_by_confirmatory_contrast：PENDING_DEV_SIGMA（键集须为 REQUIRED_MDE_CONTRASTS 五假设、值域 (0,1)；
  无真实开发侧 σ 前任何取值都是伪造）；
- layer_manifest_sha256：PENDING_SPLIT_GO（须等于 manifest layers 摘要）。
另：threshold_selection_rule_note 为 D10 裁定的附加规则字段，不属于 18 必需键；legacy 键
alpha / power / noninferiority_margin 一律不出现（出现即 ambiguous_legacy_statistical_field）。
## 10 装配日检查单（phase1a_manifest 装配，一次性动作，不造运行器）

前置（缺一不可）：label_ledger 已接受（双 reviewer + 裁决 + Loop C 独立复核留痕）；licence_record 用户签署；
schema 绑定存在（P1-future 草案或裁定变更）；analysis_plan 四 PENDING 填齐并批准；
parser_contract_receipt 由运行器实跑产出；learnability_feature_ledger 由派生运行器产出。

1. 包根建于仓外；九角色文件 + layers manifest 落位；逐文件记录 bytes 与 sha256。
2. 按 §3 骨架填 manifest：artifacts 九条、bindings 六条 role→artifact-id 字符串（gate 映射在合同 REQUIRED_BINDINGS 内，不写入 manifest）、layers、future_replay（未获取则 null + 注记）。
3. `research/phase1a_data_contract.py --package-root <pkg> --output <out>` 跑两次：两次均
   READY_FOR_INDEPENDENT_ACCEPTANCE 且报告 byte-identical；strace 复核零 connect。
4. D11 交叉一致性复核（analysis_plan minimum_uid_* 与 learnability config min_dev_uids*，去前缀键值全等）。
5. 独立复核：Loop C 证据包审计（manifest + 两次运行日志 + 双跑 diff）；生成者不自签。
6. 仅在此之后重评 DATA_NO_GO；任一 gate FAIL 回对应角色修复，不得绕过、不得改冻结判据。
红线：私有数据与包根不入 Git；失败保留现场并上报；本检查单不授权任何下载。

> 更正（2026-09-24，组合测试发现）：bindings 的值是 artifact-id 字符串，不是 [gate, id] 列表；gate→role 映射由合同 REQUIRED_BINDINGS 持有。合同 :643-644 同步加 isinstance 守卫，列表形 bindings 现以 missing_or_mismatched_binding 失败而非裸 TypeError。
