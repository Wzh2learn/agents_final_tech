# Stage D necessity gate report（2026-10-05）

> 状态：`PILOT_ONLY` | Goal：`ACTIVE`
> 机器产物：[`docs/datasets/2026-10-05_stage_d_necessity_gate_v1.json`](../datasets/2026-10-05_stage_d_necessity_gate_v1.json)
> 输入：[`docs/datasets/2026-10-04_b0_b4_exploratory_results_v2.json`](../datasets/2026-10-04_b0_b4_exploratory_results_v2.json)
> 风险判据：`harmful-map rate <= risk_limit = 0.10`，并同时检查 pair-cluster bootstrap 95% 上界

## 1. Gate question

本 gate 只回答一个问题：当前 B4 cheap classifier 是否已经稳定覆盖 action/target 问题，从而不需要训练专门学生；还是仍有稳定 residual，值得在七门通过后申请 A0-A2。

它不回答 RQ2 是否成立，不解除 `DATA_NO_GO`，不构成 Stage D、Stage R、RQ4 或训练结果。

## 2. Risk-constrained coverage

| Slice | B4 harmful-map rate | 95% upper | risk admissible | B4 correct-map coverage | Coverage 95% interval |
|---|---:|---:|---|---:|---|
| quarantine + LOO primary | 0.0616 | 0.0948 | PASS | 0.2603 | `[0.1963, 0.3398]` |
| whole-pair INVALID + LOO | 0.0615 | 0.0991 | PASS | 0.2538 | `[0.1753, 0.3524]` |
| quarantine + salted split | 0.1053 | 0.1250 | **FAIL** | 0.3158 | `[0.2727, 0.3750]` |

B3 在三个 slice 的 harmful-map rate 分别为 0.1781 / 0.1769 / 0.1579，均高于 0.10，因此不能作为满足风险约束的主基线。

## 3. Go / no-go

**判定：`PILOT_ONLY`。**

原因：

1. B4 在 primary 和 whole-pair sensitivity 下均满足风险上限，且 95% harmful-map 上界低于 0.10；
2. salted split 只有 2 个 test pairs / 19 columns，B4 点估计已经超过风险上限，95% 上界也跨过 0.10；
3. 因此 risk-constrained coverage 不是跨 mandatory slices 稳定的量；
4. 当前没有独立批准的 stable-residual threshold，不能在 `SIMPLE_SUFFICIENT` 与 `LEARNABILITY_SIGNAL` 之间作确认性选择；
5. 最终状态必须保留 exploratory uncertainty，不进入 A0-A2。

**结论字段**

- `stage_d_necessity = NOT_ESTABLISHED`
- `training_recommendation = DO_NOT_TRAIN_YET`
- `stable_risk_constrained_coverage = false`
- `primary_risk_constrained_coverage = 0.2602739726`
- `b5_status = DORMANT_NOT_RUN`
- `phase2_status = NOT_RUN`
- `training_status = NOT_RUN`

## 4. Auxiliary evidence

- B4 primary action macro-F1 `0.71699`，target exact / gold `map_to` `0.74510`。
- B3 primary action macro-F1 `0.57188`，target exact / gold `map_to` `0.94118`。
- B4 在 action 层更强，但在 target exact 和 coverage 上并不全面优于 B3。
- latency、token、GPU/CPU cost 均为 `NOT_MEASURED`；不从 runner wall-clock 或文件大小反推成本。

## 5. Paper route

由于 Stage D necessity gate 为 `PILOT_ONLY`，且 RQ2/RQ3 均未形成确认性证据：

- 小论文内部投稿版继续采用成熟 **Stage E 评估保底稿**；
- 不把 Q3 或 B0-B4 exploratory 数字写入主稿结果表；
- 大论文继续保留 Evaluate-Distill-Evolve 三阶段主线与后续回填位；
- B0-B4 只作为大论文的 exploratory evidence / future-work boundary。

## 6. Boundaries

`DATA_NO_GO`、`RQ2 NOT_IDENTIFIED` 保持；B5 不安装、不运行；Phase 2、4B/8B、模型派发、正式投稿、arXiv、公开代码和外发均未授权。

## 7. Validation

GB10 authoritative checks at `1fec714`:

- machine gate regeneration vs committed JSON: byte-identical, `cmp rc=0`;
- focused gate/B0-B4/adapter/Q3 tests: `34 passed`;
- full pytest: `850 passed / 13 skipped / 1 deselected`;
- `validate_paper_claims`: `PASS / 5 claims / 74 checks`;
- submission package audit: `10/10 mechanical PASS`, `NOT_READY_FOR_SUBMISSION`;
- `docs_lint`: `rc=0 / 0 fail / 4 warn`.

No model, B5, Phase 2, training, download, or external release was executed.