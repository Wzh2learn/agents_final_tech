# Phase 1a §7 冻结收据 vs 数据合同 analysis_plan：实测口径缺口（Loop D 只读探针）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代 `DATA_NO_GO` 报告与同日裁定清单；**更正**裁定清单里「临界路径陷阱」的口径（该处为静态推断的 3 个键，实测为 18/14 个错误码、10 个缺失必需键）
> 用途: 用真实校验器实测「§7 冻结收据能否充当合同要求的 `analysis_plan`」，把上一轮的静态推断换成可复现证据，供用户裁定「一份工件还是两份」与「A 类数值」。
> 边界: 零端点（两次 `endpoint_calls=0` / `socket_attempts=0`）、零模型调用、不批准任何数值、不在仓内填任何 `UNSET`、不改合同代码与预注册合同、不解 `DATA_NO_GO`、不启动 Phase 1a/2。探针脚本与 JSON 报告只落 GB10 `/tmp`（仓外），不入 Git。

## 1 方法（可复现）

- 环境: GB10 隔离 worktree `agents_final_tech_accept_2ce0491`（clean，HEAD `2ce0491`），`~/wzh/projects/agents_final_tech/venv/bin/python`。production 未被 pull、未被改动。
- **驱动真实校验器** `research/phase1a_data_contract.py::validate_package`，不重新实现任何判据；合成包由 `tests/test_phase1a_data_contract.py::package` fixture 构建。
- §7 JSON 由脚本从预注册件 `## 7.` 之后的 三反引号 `json` 围栏**逐字正则提取**（非人工誊写），块 sha256 前 16 位 `df67bff4233d3d31`，24 键 / 18 个 `UNSET`。
- 交换 `artifacts/analysis_plan.json` 后**只刷新 manifest 的绑定哈希**（复用 `_artifact()`），不改写收据内容，避免真实失败被哈希绑定错误掩盖。
- 两步探针:
  - **P1** = §7 原样（18 个 `UNSET` 全部保留）。
  - **P2** = 把 18 个 `UNSET` 全部填入合成占位值，**键集与 §7 完全相同**（脚本内 `assert set(filled) == set(s7)` 实测为 `True`），不新增任何键、不改任何 token。填值一律标 `SYNTHETIC_PROBE`，**不构成任何批准**。

## 2 实测结果

基线对照（证明夹具本身有效，失败可归因于交换内容）: 未改动的 fixture 包 = `READY_FOR_INDEPENDENT_ACCEPTANCE`，`analysis_plan` 门 `PASS`，`errors []`。

| 探针 | overall | analysis_plan 门 | 错误码数 | 其余 6 门 |
|---|---|---|---|---|
| P1 §7 原样 | `DATA_NO_GO` | `FAIL` | **18** | 全 `PASS` |
| P2 §7 全填合成值 | `DATA_NO_GO` | `FAIL` | **14** | 全 `PASS` |

两次 `meta` 均为 `{'phase': 'precheck', 'endpoint_calls': 0, 'socket_attempts': 0, 'contract_version': 'phase1a-data-package-v2'}`。

### 2.1 P1 的 18 个错误码（校验器输出逐字）

```text
{"code": "analysis_plan_not_approved"}
{"code": "invalid_analysis_approval_time"}
{"code": "invalid_cluster_unit"}
{"code": "invalid_significance_level"}
{"code": "invalid_target_power"}
{"code": "invalid_risk_limit"}
{"code": "invalid_noninferiority_margins"}
{"code": "missing_primary_metric", "metric": "action_macro_f1"}
{"code": "missing_primary_metric", "metric": "harmful_map_rate"}
{"code": "invalid_threshold_selection"}
{"code": "invalid_seed_uid_aggregation"}
{"code": "invalid_holm_families"}
{"code": "invalid_one_sided_p_value_methods"}
{"code": "invalid_holm_adjustment"}
{"code": "invalid_minimum_uid_by_role_family"}
{"code": "invalid_minimum_uid_by_action"}
{"code": "invalid_mde_by_confirmatory_contrast"}
{"code": "layer_manifest_hash_mismatch"}
```

### 2.2 P2 的 14 个错误码（填满全部 UNSET 之后仍在）

```text
{"code": "analysis_plan_not_approved"}
{"code": "invalid_cluster_unit"}
{"code": "invalid_target_power"}
{"code": "invalid_noninferiority_margins"}
{"code": "missing_primary_metric", "metric": "action_macro_f1"}
{"code": "missing_primary_metric", "metric": "harmful_map_rate"}
{"code": "invalid_threshold_selection"}
{"code": "invalid_seed_uid_aggregation"}
{"code": "invalid_holm_families"}
{"code": "invalid_one_sided_p_value_methods"}
{"code": "invalid_holm_adjustment"}
{"code": "invalid_minimum_uid_by_action"}
{"code": "invalid_mde_by_confirmatory_contrast"}
{"code": "layer_manifest_hash_mismatch"}
```

P1→P2 只消掉 **4** 个: `invalid_analysis_approval_time`、`invalid_significance_level`、`invalid_risk_limit`、`invalid_minimum_uid_by_role_family`。这 4 个恰好是 §7 里「**键存在、值为 `UNSET`**」的全部字段（`approved_at`、`significance_level`、`risk_limit`、`minimum_uid_by_role_family`）。

## 3 归因：14 个剩余错误全部是 schema 级，无一能靠「填值」消除

### 3.1 合同必需但 §7 完全没有的键（10 个）

`cluster_unit`(:918) · `target_power`(:920-923) · `primary_metrics`(:936-939) · `seed_uid_aggregation`(:942) · `holm_families`(:944) · `one_sided_p_value_methods`(:946-953) · `holm_adjustment`(:954) · `minimum_uid_by_action`(:962-968) · `noninferiority_margins`(:924-935，需为嵌套对象) · `layer_manifest_sha256`(:976)

取证口径说明（避免夸大）: 用正则机械抽取 :909-977 的字面 `analysis.get("...")` 只得 9 个缺失键，因为 `significance_level / target_power / risk_limit` 是经**循环变量** `analysis.get(key)` 读取的（:920-921），正则抓不到。逐个复核这三者: `significance_level` 与 `risk_limit` 在 §7 内，**`target_power` 不在**（实测 `in_s7=False`）⇒ 真实缺失数 = **10**。

§7 与之最接近但**并不等价**的键: `delta_quality/delta_harm/delta_retention`（顶层平铺 vs 合同要求的嵌套 `noninferiority_margins`）· `rq2_holm_family`/`rq3_holm_family`（两个平铺列表 vs 合同要求的嵌套 `holm_families` 字典）· `one_sided_interval_method`（区间方法，非合同要求的逐假设 p 值方法表）· `source_manifest_sha256`/`role_split_manifest_sha256`（非 `layer_manifest_sha256`）。

### 3.2 两处 token 冲突（两边都写了值，但写的不是同一个）

| 键 | §7 的值 | 合同要求的值 | 检查行 |
|---|---|---|---|
| `status` | `FROZEN_BY_HUMAN` | 恰好 `approved` | :912 |
| `threshold_selection` | `proposal_dev_max_coverage_under_risk_then_macro_f1_then_conservative`（与 §6.3 :118 的选择规则文字一致） | 恰好 `proposal_dev_only` | :940 |

### 3.3 一处假设命名冲突（会同时打穿两道检查）

§7 `rq3_holm_family` = `H3a_uid_any_harm` / `H3a_valid_rule_retention`；合同 `REQUIRED_HOLM_FAMILIES["rq3"]` = **`H3a_cluster_any_harm`** / `H3a_valid_rule_retention`（:105-108）。且 `REQUIRED_MDE_CONTRASTS` 由这两个家族**派生**（:110-114），`one_sided_p_value_methods` 的键集也含该假设（:946-952）⇒ 同一处命名分歧同时导致 `invalid_holm_families`、`invalid_mde_by_confirmatory_contrast`（以及若补 `one_sided_p_value_methods` 时的第三处）。

P2 刻意用 **§7 自己的假设名**生成 MDE 键，仍 `FAIL` ⇒ 「照 §7 填对」也过不了合同。

### 3.4 探针脚本自带归因表的一处疏漏（如实更正）

P2 脚本的 `attribution` 段把 `invalid_target_power` 归入 "pure_value_errors (fixable by filling)"。那是脚本内手写的 `UNFILLABLE` 集合漏列该码所致，**不是实测结论**: §7 根本没有 `target_power` 键，填值无从填起（见 §3.1）。本件按实测根因把它归为 schema 级 ⇒ **14 个剩余错误 100% 为 schema 级**。

## 4 顺带查出的一处守卫缺口（只报不改）

§7 前言写「以下任一值为 `UNSET` 即禁止正式实验」，但合同**没有实现 `UNSET` 哨兵检查**。实测: P1 里 `approved_by = "UNSET"` 时，`missing_analysis_owner` **未触发**（18 个错误码内无此项），因为 :914 只判「是非空字符串」:

```python
if not isinstance(analysis.get("approved_by"), str) or not analysis["approved_by"]:
    _fail(gates, "analysis_plan", "missing_analysis_owner")
```

⇒ 字面量 `"UNSET"` 是一个非空字符串，能通过。其余 `UNSET` 字段是靠类型/范围检查**间接**拦下的（字符串 `"UNSET"` 不是 0-1 浮点、不是 ISO8601、不是 dict），并非因为有哨兵。**影响面**: 只有 `approved_by` 这一个纯字符串字段会静默放行未填状态。按纪律本件**不改合同代码**（属判据面，需用户显式授权 + 修者不自验）；如需补，建议与 A 类数值裁定同批，并补一对正反例。

## 5 对「一份工件还是两份」的意义（只给可行性，不给结论）

实测证明 §7 收据**不是** `analysis_plan` 的超集: 两者在 **10 个必需键**上完全不相交，另有 2 处 token 冲突与 1 处假设命名冲突。

- 若裁定为**同一份工件**: 在不重写 §7 schema 的前提下**不可行**——照 §7 填满仍 14 错（P2 实测）。要走这条路必须同时改 §7 的 JSON 模板（DRAFT_NOT_FROZEN 件）**或**改合同常量（判据面）。
- 若裁定为**两份工件**: §7 之外还需一份 `analysis_plan.json`。其必需键可由合同 :909-977 机械导出（§3.1 + §3.2 + §3.3 已列全），本件**不代填任何值**。
- 无论哪条路，§3.3 的 `H3a_uid_any_harm` vs `H3a_cluster_any_harm` 都必须先定谁是权威名——它不是格式问题，是两份权威件对同一个确认性假设取了不同名字。

裁定权在用户，本件不选路、不代判。

## 6 复现

```bash
ssh jinrong-dev
cd ~/wzh/projects/agents_final_tech_accept_2ce0491
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/p1a_s7_probe.py  "$PWD"   # P1
~/wzh/projects/agents_final_tech/venv/bin/python /tmp/p1a_s7_probe2.py "$PWD"   # P2
```

取证哈希（GB10 `/tmp`，仓外）:

| 文件 | sha256 |
|---|---|
| `p1a_s7_probe.py` | `94f5e5afcb32f893b12a5dea67c73c84ab54a8105adfd569a85cf196a385ceea` |
| `p1a_s7_probe2.py` | `4cfba5a48ddd0576fa28a70b9d76410a9c78c643c50adeaaff50cdce89d00998` |
| `p1a_s7_probe_report.json` | `8123a1bd1bb23763e94b0b6ed32ab6ba5f93f703e0fb0004d338a4d8d7d41b98` |
| `p1a_s7_filled_probe_report.json` | `2409f22084a21f8aba939a8449b4a4c3cafca80e7b2443f621d49f0b6b555bb1` |

`/tmp` 非持久，故 P2 探针全文附于 §7 以便任何时候重跑。

## 7 P2 探针全文（决定性那一步）

````python
"""Probe 2: fill every UNSET in the S7 receipt using S7's OWN keys/structure
(no keys added, no schema change) and re-run the real validator.
Values are SYNTHETIC_PROBE placeholders: they approve nothing and imply no
DATA_GO. Purpose is to separate 'fill the values' from 'change the schema'."""
from __future__ import annotations
import importlib.util, json, re, sys, tempfile, pathlib

REPO = pathlib.Path(sys.argv[1]).resolve()
DOC = REPO / "docs/experiments/2026-09-22_distillation_mvp_preregistration.md"
sys.path.insert(0, str(REPO))
from research import phase1a_data_contract as contract

spec = importlib.util.spec_from_file_location("tmod", REPO / "tests/test_phase1a_data_contract.py")
tmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmod)

text = DOC.read_text(encoding="utf-8")
body = text[text.index("## 7."):]
s7 = json.loads(re.search(r"```json\n(.*?)\n```", body, re.S).group(1))

H = "0" * 64
families = list(s7["rq2_holm_family"]) + list(s7["rq3_holm_family"])
filled = dict(s7)
filled.update({
    "approved_by": "SYNTHETIC_PROBE_NOT_AN_APPROVAL",
    "approved_at": "2026-09-24T00:00:00Z",
    "source_manifest_sha256": H,
    "historical_exposure_manifest_sha256": H,
    "role_split_manifest_sha256": H,
    "q3_adjudication_receipt_sha256": H,
    "model_id_revision_hash": H,
    "tokenizer_template_hash": H,
    "training_config_hash": H,
    "seed_list": [1, 2],
    "delta_quality": 0.02,
    "delta_harm": 0.02,
    "delta_retention": 0.02,
    "risk_limit": 0.1,
    "significance_level": 0.05,
    "minimum_cost_reduction": 0.1,
    "minimum_uid_by_role_family": {"proposal_train.dev/*": 2},
    "mde_by_confirmatory_contrast": {h: 0.05 for h in families},
})
assert "UNSET" not in json.dumps(filled), "some UNSET left unfilled"
print("== S7 fully filled with SYNTHETIC values, schema unchanged ==")
print("keys", len(filled), "(same key set as S7:", set(filled) == set(s7), ")")
print("mde keys use S7's own hypothesis names:", sorted(filled["mde_by_confirmatory_contrast"]))

tmp = pathlib.Path(tempfile.mkdtemp(prefix="p1a_probe2_", dir="/tmp"))
fn = getattr(tmod.package, "__wrapped__", tmod.package)
pkg = fn(tmp)
man = tmod._manifest(pkg)
art = next(a for a in man["artifacts"] if a["id"] == "analysis-plan")
p = pkg / art["path"]
p.write_text(json.dumps(filled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
art.update(tmod._artifact(p, "analysis-plan", "analysis_plan"))
tmod._save_manifest(pkg, man)

rep = contract.validate_package(pkg)
g = rep["gates"]["analysis_plan"]
errs = g.get("errors") or []
print()
print("== RESULT ==")
print("overall_status", rep["status"])
print("meta", rep["meta"])
print("analysis_plan_gate", g["status"], "remaining_errors", len(errs))
for e in errs:
    print("  -", json.dumps(e, ensure_ascii=False, sort_keys=True))
print("other_gates", {k: v["status"] for k, v in rep["gates"].items()})
````

注: P2 里 `delta_quality/harm/retention = 0.02`、`risk_limit = 0.1`、`significance_level = 0.05` 只是为了让探针跑通而取的**占位值**，与预注册件 §7 脚注「`delta_quality=0.02` 只能作讨论起点，尚未批准」同口径，**不构成批准**，也不得被引用为候选批准值。

## 8 红线自查

- 未改 `research/phase1a_data_contract.py`、未改预注册合同、未改任何冻结判据/阈值/oracle/冻结 hash。
- 未在仓内填任何 `UNSET`；合成值只存在于 GB10 `/tmp` 的临时包内，探针结束即弃。
- 未解 `DATA_NO_GO`（两次探针输出反而都是 `DATA_NO_GO`）；未启动 Phase 1a/2；未授权训练或模型端点。
- 零端点: `endpoint_calls=0`、`socket_attempts=0`，由校验器自身 `offline_guard()` 记录，非自我申报。
- 未动 `docs/33`、`docs/34`；未 pull production；未重启 daemon 与 `:5050`。
- 探针脚本与报告一律落仓外 `/tmp`，不 commit；本件为唯一入 Git 的产物。
