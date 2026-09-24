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
    "label_ledger": ["independent_correctness", "PENDING"],
    "learnability_feature_ledger": ["artifact_integrity", "PENDING"],
    "licence_record": ["licence_permission", "PENDING"],
    "confidence_manifest": ["confidence_provenance", "PENDING"],
    "analysis_plan": ["analysis_plan", "PENDING"],
    "parser_contract_receipt": ["parser_contract", "PENDING"]
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
