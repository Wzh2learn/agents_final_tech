# B0-B4 exploratory probe results v2（2026-10-04）

> 状态：`VALID_EXPLORATORY_RESULT_WITH_SENSITIVITIES` | `paper_result=false`
> 运行：GB10 CPU-only，零模型、零下载、零 Phase 2、零训练、B5 `DORMANT_NOT_RUN`
> Freeze：[`docs/datasets/2026-10-04_b0_b4_exploratory_freeze_v2.json`](../datasets/2026-10-04_b0_b4_exploratory_freeze_v2.json)

## 1. Validity and provenance

- Corrected Q3 ledger：146 rows，`map_to=51 / skip=58 / hold=37`，SHA256 `cf339cef8b7065dad05f574a1400415a7bff64b78b66e1db38f74143cc49ccb6`。
- Raw seal：`ARTIFACT_CLOSED_WITH_VISIBILITY_EXCEPTIONS`。
- Option A primary：reference-level quarantine，固定隔离 3 条 invalid action references。
- Option B sensitivity：整个 DSNY pair INVALID，9 clusters / 130 columns。
- B0-B4 主协议：leave-one-pair-out；salted group split 只作 split sensitivity。
- Bootstrap：pair-cluster，n=2000，seeds `[42,43,44]`，只作 exploratory uncertainty，不作 power 证明。

首轮运行因 salted B4 `(row_index,prediction)` 被误当 `(action,target)` 而作废，状态 `INVALIDATED_RUNNER_ALIGNMENT_BUG`。修复后 `freeze_v2` 在重跑前绑定新 runner hash。三组合 byte-identical 双跑差异均为 `0/0/0`。

## 2. Primary: quarantine + leave-one-pair-out

146 columns / 10 pairs / 730 predictions。

| ID | 方法 | action macro-F1 | accuracy | harmful-map rate | map-to risk | correct-map coverage | target exact / gold map_to | target exact / predicted map_to |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| B0 | always-skip | 0.190 | 0.397 | 0.000 | undefined | 0.000 | 0.000 | undefined |
| B1 | deterministic exact | 0.463 | 0.596 | 0.000 | 0.000 | 0.199 | 0.569 | 1.000 |
| B2 | lexical fuzzy | 0.462 | 0.603 | 0.116 | 0.315 | 0.253 | 0.725 | 0.685 |
| B3 | confidence-only | 0.572 | 0.726 | 0.178 | 0.351 | 0.329 | 0.941 | 0.649 |
| B4 | cheap classifier | **0.717** | **0.760** | **0.062** | **0.191** | 0.260 | 0.745 | **0.809** |

B4 pair-cluster 95% interval：

- action macro-F1 `[0.661, 0.757]`
- harmful-map rate `[0.035, 0.095]`
- correct-map coverage `[0.196, 0.340]`
- target exact / gold map_to `[0.582, 0.865]`

B4 的主要 macro-F1 增益来自 `hold`：B4 hold-F1=0.485，而 B3 hold-F1=0.050。B3 的 gold-map target exact 很高，但 harmful-map rate 和 map-to risk 明显更高。B1 无 harmful map，但 coverage 仅 0.199。

## 3. Mandatory sensitivity

### 3.1 Option B: whole pair INVALID + LOO

130 columns / 9 pairs / 650 predictions。

| ID | action macro-F1 | harmful-map rate | correct-map coverage | target exact / gold map_to |
|---|---:|---:|---:|---:|
| B3 | 0.580 | 0.177 | 0.338 | 0.957 |
| B4 | **0.709** | **0.062** | 0.254 | 0.717 |

B4 与主分析几乎同向：macro-F1 0.709 vs 0.717，harmful-map rate 0.062 vs 0.062。三条异常引用不是主分析 B4 表现的主要驱动。剔除 pair 后 target exact 从 0.745 降至 0.717。

### 3.2 Salted group split sensitivity

6 train / 2 dev / 2 test pairs；test 仅 19 columns / 2 pairs。

| ID | action macro-F1 | harmful-map rate | correct-map coverage | target exact / gold map_to |
|---|---:|---:|---:|---:|
| B3 | 0.588 | 0.158 | 0.368 | 1.000 |
| B4 | **0.692** | 0.105 | 0.316 | 0.857 |

B4 macro-F1 95% interval `[0.517, 0.841]`，harmful-map rate `[0.091, 0.125]`。区间宽、test 只有 2 pairs，说明 split sensitivity 不能忽略；该结果不能外推到 gate/sealed 或独立样本。

## 4. Exploratory interpretation

1. **B4 是后续必须超越的简单基线。** primary action macro-F1 比最佳非学习基线 B3 高 0.145，同时 harmful-map rate 低 0.116。
2. **尚不能据此证明需要专门 8B 学生。** B4 的 coverage 低于 B3，target exact 也低于 B3；真正问题变成：A2 是否能在相同或更低风险下提高 risk-constrained coverage，而不是只提高 macro-F1。
3. **Option A/B 的动作引用处置对 B4 主结论影响较小。** 9-pair sensitivity 与 10-pair primary 基本一致。
4. **split sensitivity 仍真实存在。** salted test 只有 2 pairs，B4 区间宽且 harmful rate 高于 LOO；不能把 LOO 点估计当稳定总体性能。
5. **不产生 gate/go-no-go。** 当前没有批准的 SIMPLE_SUFFICIENT / LEARNABILITY_SIGNAL 阈值，本报告只给探索性比较与风险-覆盖权衡。

## 5. Evidence artifacts

GB10：`/home/testuser/wzh/q3_raw_seal_20261004/derived/b0_b4/*_v2/`

| Run | report sha256 | predictions sha256 | manifest sha256 |
|---|---|---|---|
| quarantine-primary-LOO | `89fc4130151f92d052a5e001f284798b6e3a6b842bad73a016fb5ddcb12250d6` | `1a435c9e5a486ec25891f8a7cc00fecf80a5b2c8bd6b5c8dd26551f01342788d` | `1452f16c738b20044746b34d690312f4b49b3e0800b7423afc740420d2bc06f7` |
| pair-invalid-LOO | `1f49c18fff61ef70398a1959a7271c4943c24428d6515f01f096c5e5df02305f` | `f2ea514ce0802b4061fcdd7312e2fbdbe2d16bbaaf24e5800d71f57c7c1285cc` | `9b278b7d1f42ecb25157c7e4a68bc55500fabbbe33f9bea3e76dae1225d9d412` |
| quarantine-primary-salted | `3db5b3f5727fa2301e3d671cbc482c4a7052f7d792a4d112fb060e8c06dd1273` | `eb462fc0c23d09cfcc5012ccb2e4b83f6bb3402843bf4fd2d7d5684b679566d4` | `8f75a66f50393cf5f214312792ccc9227e667392d564cf8fe9acdbb4570d8b1a` |

机器摘要：[`docs/datasets/2026-10-04_b0_b4_exploratory_results_v2.json`](../datasets/2026-10-04_b0_b4_exploratory_results_v2.json)。

## 6. Boundary

Q3 与 B0-B4 仅是 exploratory learnability evidence。`DATA_NO_GO`、`RQ2 NOT_IDENTIFIED` 保持；不构成 Stage D、Stage R、RQ4 或训练结果。B5 不安装、不运行；Phase 2、4B/8B、模型派发、新下载、正式投稿、arXiv、公开代码和外发均未授权。

## 7. Validation

GB10 authoritative checks at `790e9f7`:

- focused adapter/Q3/B0-B4 tests: `31 passed`;
- full pytest: `847 passed / 13 skipped / 1 deselected`;
- result-summary-to-report assertions: `RESULT_SUMMARY_MATCH=True`;
- `docs_lint`: `rc=0 / 0 fail / 4 warn`;
- `validate_paper_claims`: `PASS / 5 claims / 74 checks`;
- submission package audit: `10/10 mechanical PASS`, `NOT_READY_FOR_SUBMISSION`;
- deterministic v2 double-run: `diff rc=0/0/0`.

The first run remains invalidated and is not used in any table or interpretation.