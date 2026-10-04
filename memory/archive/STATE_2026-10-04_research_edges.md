# STATE 2026-10-04 research edge historical addenda

> Archived from `memory/STATE.md` to preserve append-only history while restoring the navigational 100-line limit.

## Q3 result and B5 addendum

## 2026-10-04 Q3 result and B5 addendum (append-only)

- User confirmed Q3 review by three independent experts (R1/R2/ADJ). This supersedes the intermediate statement that one expert served as both R1 and R2. Local checkout head observed as `d62420e`; this update performed no git operation and did not re-verify origin/GB10 alignment.
- Exploratory Q3 summary: 146/146 adjudicated labels; R1/R2 exact agreement 119/146 (81.51%); action Cohen's kappa approximately 0.727; 41/41 target exact agreement when both chose `map_to`; 27 disagreements all at the action boundary; final `map_to=52 / skip=58 / hold=36`.
- Raw R1/R2/ADJ outputs, adjudication ledger, final label ledger, gold-isolation receipt, and hashes remain to be sealed. These numbers are recorded as a user-confirmed expert-output summary, not as a complete artifact audit.
- Evidence boundary unchanged: exploratory learnability evidence only. It does not lift `RQ2 NOT_IDENTIFIED / DATA_NO_GO`, and must not be written as Stage D closure, RQ2 confirmation, training evidence, or RQ4 closure. The 146 columns contain only 10 lineage/table-pair clusters.
- B5 candidate registered as `Jev-like typed-decision baseline`, status `PROPOSED_EXPLORATORY / NOT_RUN`. Input is strictly `source_header + canonical headers + LABEL semantics`; action is selected first, then target only for `map_to`. B5 does not replace or modify frozen B0-B4. `open-alternative-jev` and `jevos-v2` remain unverified candidates and must not be installed or run before licence, provenance, version, dependency, and output-capability checks.
- Next order: seal the three expert outputs and hashes, run the existing B0-B4 exploratory probe, then audit and decide whether to run B5 as a single frozen zero-shot probe. Any tuning or calibration must use a table/lineage-UID group-aware split.
- 2026-10-04 full delivery: the 10-file expert package is stored at `logs/graph/q3_raw_seal_20261004/` and GB10 `/home/testuser/wzh/q3_raw_seal_20261004/inbox/q3_raw_seal_20261004/`. All 9 manifest hashes match. R1/R2/ADJ/final synthesis was mechanically verified: 119/146 agreement, 27 ADJ rows, kappa 0.7265, zero derivation errors; corrected ledger is `map_to=51 / skip=58 / hold=37` with only line 61 changed to `hold|null`. Status is `SEALED_WITH_VISIBILITY_EXCEPTIONS` / `seal_complete=true`; R1 saw lineage/table grouping and R2/ADJ lack separately signed visibility receipts.

## Later append-only addenda

## 2026-10-04 research edge batch（append-only）

- 当前批准基线 = `f2adaf1be13cd641ca0993c8e2d20a16ad717cfc`；本批实际工作起点 = `e44c3c3d3922bc8b3c6f11d6a7cd50526ad6ebc0`。上文仍写 f2adaf1 的 Git 行是前批快照，本段为当前更正，不回改历史。
- 新增 `docs/datasets/2026-10-04_rq2_identification_and_acquisition_card.md`：RQ2 同样本 identification 与 Route V/F 数据、许可、split、power 申报，状态 `DECISION_APPLICATION / NO_EXECUTION`。
- 新增 `docs/experiments/2026-10-04_q3_b0_b4_execution_plan.md`：Q3 专家摘要状态注记与 B0-B4 执行合同；Q3 raw 未封存，B0-B4 `NOT_RUN`。
- 边界不变：`DATA_NO_GO`、`RQ2 NOT_IDENTIFIED`；146 列已有用户确认的 exploratory 摘要但 raw 未封存；MIMO `READY_FOR_CONFIG_ONLY`、V2-3 关闭、G-A/G-B/G-C 不批准。零模型、零下载、不启动 Phase 1a/2/训练、不外发。

## 2026-10-04 boundary clarification and blocker closure (append-only)

- Goal remains ACTIVE; Stage E fallback remains valid; RQ2 stays NOT_IDENTIFIED / DATA_NO_GO; Q3 remains exploratory learnability evidence only.
- Q3 raw artifacts are still MISSING in the checked local and GB10 scopes: R1 output, R2 output, ADJ output, final label ledger, expert visibility/gold-isolation receipt, and output manifest/hash. Empty input templates and historical /tmp/r1.json,/tmp/r2.json are explicitly not sealed raw outputs.
- Three invalid action references remain pending user disposition: turn 12 record_match, turn 13 revoke_match, turn 31 batch_record_match in City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments all reference mgp_curb_pri_boro. Options are reference-level quarantine or whole-pair INVALID; no option has been selected.
- B0-B4 exploratory split protocol is DRAFT_NOT_FROZEN / NOT_RUN at docs/datasets/2026-10-04_b0_b4_exploratory_split_protocol_v1.md. The frozen runner is not run because proposal_train.dev=0.
- B5 remains PROPOSED_EXPLORATORY / NOT_RUN. Offline audit found no local source checkout, licence, version, dependency, import, or typed-output evidence for open-alternative-jev / jevos-v2.
- Stage R, RQ4, training, formal submission, external release, arXiv, and public code remain incomplete or prohibited.

## 2026-10-04 ruling landing (append-only)

- Raw originals delivery target is /home/testuser/wzh/q3_raw_seal_20261004/inbox/ (created empty, mode 700), with exact GB10 paths preferred. No reconstruction from summary.
- Invalid action references: Option A reference quarantine is primary for turn 12/13/31 with invalid_action_reference_count=3; Option B whole-pair INVALID is mandatory sensitivity. Preserve the 146-column summary and report a 9-cluster / 130-column sensitivity subset.
- B0-B4: LOO is primary, salted split is sensitivity; bootstrap 2000 and seeds [42,43,44] are exploratory uncertainty only. Protocol is user-selected but not frozen/running.
- B5 remains dormant / NOT_RUN; metadata-only audit is the maximum next step and execution needs separate authorization.

## 2026-10-04 Q3 raw seal correction (append-only)

- Raw audit package is sealed at logs/graph/q3_raw_seal_20261004/ and GB10 /home/testuser/wzh/q3_raw_seal_20261004/inbox/q3_raw_seal_20261004/; 10 files, 9/9 manifest hashes, secret scan 0.
- Authoritative corrected ledger SHA256 cf339cef8b7065dad05f574a1400415a7bff64b78b66e1db38f74143cc49ccb6; corrected counts map_to=51 / skip=58 / hold=37. The earlier 52/58/36 is pre-correction only.
- Evidence level is ARTIFACT_CLOSED_WITH_VISIBILITY_EXCEPTIONS: R1 saw lineage/table grouping; R2/ADJ lack separately signed visibility receipts.

## 2026-10-04 B0-B4 exploratory v2 result (append-only)

- Option A/B process variants passed on real staging: primary 10 pairs / 146 columns / 3 quarantined references; sensitivity 9 pairs / 130 columns / the same 3 references.
- Frozen B0-B4 v2 ran on GB10 with zero model calls. Primary B4 action macro-F1=0.71699, harmful-map rate=0.06164, coverage=0.26027; B3=0.57188 / 0.17808 / 0.32877. Pair-invalid B4=0.70931 / 0.06154 / 0.25385. Salted B4=0.69150 / 0.10526 / 0.31579 on only 2 test pairs / 19 columns.
- B4 is the current simple baseline to beat. A dedicated student is `NOT_ESTABLISHED` as necessary; no go/no-go threshold was approved and no training is authorized.
- The first probe run is invalidated by a salted B4 alignment bug; `freeze_v2` and `*_v2` outputs are the only valid exploratory evidence. Double-run diff rc=0/0/0.
- DATA_NO_GO / RQ2 NOT_IDENTIFIED / B5 dormant / no Phase 2 / no training boundaries remain.
