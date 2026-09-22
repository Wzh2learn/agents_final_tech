"""DPO 偏好对 v0 生成器（设计稿 2026-08-28_dpo_pairs_v0_design.md）。

机械生成零端点; synthetic 标记经 force_inject 同 RNG 确定性重构
（建议流水未携带该字段, 重构口径与 research/vgmc_exp1.py force_inject 逐行一致）。
"""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
import random
import re
import socket
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
GEN_SEED = 20260828
FORCE_RATE, FORCE_SEED = 0.5, 20260827
SOURCES = [("noise_L3", "vgmc_noise_L3_checkpoint.json", None),
           ("collision_C1", "vgmc_collision_C1_checkpoint.json", "vgmc_collision_overlay.json")]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def synthetic_target(m, corpus, uid, c):
    rec = corpus[uid]
    rng = random.Random(f"{FORCE_SEED}:{uid}:{c}")
    if rng.random() > FORCE_RATE:
        return None
    e = next((e for e in rec["entries"] if e["col"] == c), None)
    true_c = next((x for x in rec["canonicals"] if e and
                   m.mp.normalize_header(x) == m.mp.normalize_header(e["original"])), None)
    wrong = [x for x in rec["canonicals"] if x != true_c]
    if not wrong:
        return None
    return rng.choice(wrong)


def main() -> int:
    m = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    events, corpora = [], {}
    for regime, fn, ovl in SOURCES:
        overlay = json.loads((EVAL / ovl).read_text(encoding="utf-8")) if ovl else None
        corpus = m.load_corpus(overlay)
        corpora[regime] = corpus
        ck = json.loads((EVAL / fn).read_text(encoding="utf-8"))
        for arm in ("gated", "ungated"):
            for s in ck["arm_" + arm]["sugg_log"]:
                synth = synthetic_target(m, corpus, s["uid"], s["col"])
                events.append({**s, "regime": regime, "arm": arm,
                               "synthetic": synth is not None and s.get("target") == synth})
    pairs: dict[tuple, dict] = {}

    def add_pair(uid, col, chosen, rejected, ptype, ev, flag=None):
        key = (uid, col, json.dumps(chosen, ensure_ascii=False),
               json.dumps(rejected, ensure_ascii=False))
        p = pairs.setdefault(key, {"uid": uid, "col": col, "chosen": chosen,
                                   "rejected": rejected, "types": set(), "sources": [],
                                   "gate_fooled": False})
        p["types"].add(ptype)
        p["sources"].append(f"{ev['regime']}/{ev['arm']}/r{ev['round']}")
        p["gate_fooled"] = p["gate_fooled"] or bool(flag)

    gated = {(e["regime"], e["uid"], e["col"]): e for e in events if e["arm"] == "gated"}
    for e in events:
        if e["arm"] == "gated" and e["reason"] == "gated_fail":
            add_pair(e["uid"], e["col"], {"action": "skip"},
                     {"action": "map_to", "target": e["target"]}, "A", e)
        if e["synthetic"]:
            add_pair(e["uid"], e["col"], {"action": "skip"},
                     {"action": "map_to", "target": e["target"]}, "C", e,
                     flag=(e["arm"] == "gated" and e["reason"] == "gated_pass"))
    for (r1, uid, col), e1 in gated.items():
        for r2 in ("noise_L3", "collision_C1"):
            if r2 <= r1:
                continue
            e2 = gated.get((r2, uid, col))
            if not e2:
                continue
            acc, rej = (e1, e2) if e1["reason"] == "gated_pass" and e2["reason"] == "gated_fail" else \
                       (e2, e1) if e2["reason"] == "gated_pass" and e1["reason"] == "gated_fail" else (None, None)
            if acc and acc.get("target") != rej.get("target"):
                add_pair(uid, col, {"action": "map_to", "target": acc["target"]},
                         {"action": "map_to", "target": rej["target"]}, "B", acc)
    all_cols = {(e["uid"], e["col"]) for e in events}
    paired_cols = {k[:2] for k in pairs}
    by_type = {}
    for p in pairs.values():
        p["types"] = sorted(p["types"])
        for t in p["types"]:
            by_type[t] = by_type.get(t, 0) + 1
    out = {"meta": {"name": "dpo-pairs-v0", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "design": "docs/experiments/2026-08-28_dpo_pairs_v0_design.md",
                    "gen_seed": GEN_SEED, "endpoint_calls": 0,
                    "sources": [f"{r} ({f})" for r, f, _ in SOURCES],
                    "synthetic_reconstruction": "force_inject 同 RNG 重构（种子 20260827, rate 0.5）"},
           "summary": {"n_pairs": len(pairs), "by_type": by_type,
                       "gate_fooled_n": sum(1 for p in pairs.values() if p["gate_fooled"]),
                       "coverage": {"columns_total": len(all_cols),
                                    "columns_paired": len(paired_cols),
                                    "rate": round(len(paired_cols) / len(all_cols), 4)},
                       "source_distribution": {r: sum(1 for p in pairs.values()
                                                      if any(s.startswith(r) for s in p["sources"]))
                                               for r, _f, _o in SOURCES}},
           "pairs": sorted(pairs.values(), key=lambda p: (p["uid"], p["col"]))}
    (EVAL / "dpo_pairs_v0.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False))
    return 0


def stable_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(stable_json(value).encode()).hexdigest()


@contextmanager
def offline_guard():
    attempts = [0]

    def forbidden(*args, **kwargs):
        attempts[0] += 1
        raise RuntimeError("network access forbidden during data audit")

    targets = [(socket.socket, "connect"), (socket.socket, "connect_ex"),
               (socket.socket, "sendto"), (socket, "create_connection"), (socket, "getaddrinfo")]
    originals = [(obj, name, getattr(obj, name)) for obj, name in targets]
    try:
        for obj, name in targets:
            setattr(obj, name, forbidden)
        yield attempts
    finally:
        for obj, name, original in originals:
            setattr(obj, name, original)


def audit_data(eval_dir=EVAL):
    with offline_guard() as attempts:
        result = _audit_data(Path(eval_dir).resolve())
        result["meta"]["socket_attempts"] = attempts[0]
        if attempts[0]:
            raise RuntimeError("network attempted during data audit")
        return result


def _audit_data(eval_dir):
    inputs, issues, events, source_splits, ledger_checks = {}, [], [], [], []
    lineages, group_events = defaultdict(list), defaultdict(list)
    borrowed = set()

    def read(name):
        path = (eval_dir / name).resolve()
        if path.parent != eval_dir or path.suffix != ".json":
            raise ValueError("audit inputs must be JSON files in the supplied evaluation directory")
        raw = path.read_bytes()
        inputs[name] = hashlib.sha256(raw).hexdigest()

        def invalid(value):
            raise ValueError(f"invalid JSON constant: {value}")

        def unique(pairs):
            obj = {}
            for key, value in pairs:
                if key in obj:
                    raise ValueError(f"duplicate JSON key: {key}")
                obj[key] = value
            return obj

        value = json.loads(raw, parse_constant=invalid, object_pairs_hook=unique)
        if not isinstance(value, dict):
            raise ValueError(f"JSON object required: {name}")
        return value

    tables_doc = read("checkpoint_discrimination_tables_v2.json")
    tables = {table["uid"]: table for table in tables_doc["tables"]}
    if len(tables) != len(tables_doc["tables"]):
        raise ValueError("duplicate source-table uid")
    pair_doc = read("dpo_pairs_v0.json")
    checkpoint_names = sorted(path.name for path in eval_dir.glob("vgmc*_checkpoint.json"))
    if not checkpoint_names:
        raise ValueError("no checkpoints found")
    for name in checkpoint_names:
        checkpoint = read(name)
        regime = name.removeprefix("vgmc_").removesuffix("_checkpoint.json")
        result_name = name.replace("_checkpoint.json", "_results.json")
        if (eval_dir / result_name).is_file():
            source_result = read(result_name)
        else:
            source_result = {}
            issues.append({"source": name, "issue": "missing_result"})
        meta = source_result.get("meta", {})
        prereg = meta.get("prereg", {})
        fix, meas = prereg.get("fix_uids", []), prereg.get("meas_uids", [])
        if not fix or not meas:
            issues.append({"source": name, "issue": "missing_historical_split"})
        overlap = set(fix) & set(meas)
        if overlap:
            issues.append({"source": name, "issue": "split_overlap", "uids": sorted(overlap)})
        if len(set(fix)) != len(fix) or len(set(meas)) != len(meas):
            issues.append({"source": name, "issue": "duplicate_split_uids"})
        if set(fix + meas) != set(tables):
            issues.append({"source": name, "issue": "historical_split_universe_mismatch"})
        historical_digest = hashlib.sha256(json.dumps(
            {"fix": fix, "meas": meas}, ensure_ascii=False).encode()).hexdigest()
        if prereg.get("split_digest_sha256") not in (None, historical_digest):
            issues.append({"source": name, "issue": "historical_split_hash_mismatch"})
        source_splits.append({"source": name, "fix": fix, "meas": meas,
                              "sha256": historical_digest, "overlap": sorted(overlap)})
        references = {(uid, e["col"]): {"header": e["injected"], "canonical": e["canonical"],
                                       "artifact": "checkpoint_discrimination_tables_v2.json"}
                      for uid, table in tables.items() for e in table["injections"]}
        overlay_spec = meta.get("collision_overlay")
        overlay_name = None
        if overlay_spec:
            overlay_path = overlay_spec["path"]
            overlay_name = Path(overlay_path).name
            if overlay_path not in (overlay_name, f"logs/graph/eval/{overlay_name}"):
                raise ValueError("unrecognized overlay path")
            overlay = read(overlay_name)
            for uid, table in overlay["tables"].items():
                if uid not in tables:
                    issues.append({"source": name, "issue": "overlay_uid_missing", "uid": uid})
                    continue
                for offset, col in enumerate(table["cols"]):
                    references[uid, tables[uid]["n_cols"] + offset] = {
                        "header": col["header"], "canonical": col["true_canonical"], "artifact": overlay_name}
                    donor = col.get("source_uid")
                    if donor in tables and donor != uid:
                        borrowed.add((overlay_name, uid, donor, col["header"],
                                      (uid in fix) != (donor in fix)))
        for arm_key, state in sorted(checkpoint.items()):
            if not arm_key.startswith("arm_"):
                continue
            arm, rules = arm_key[4:], {}
            for index, event in enumerate(state["sugg_log"]):
                if (not isinstance(event, dict) or not isinstance(event.get("uid"), str)
                        or type(event.get("col")) is not int or event["col"] < 0
                        or type(event.get("round")) is not int or event["round"] < 0
                        or type(event.get("accepted")) is not bool
                        or not isinstance(event.get("injected"), str)
                        or not isinstance(event.get("reason"), str)):
                    raise ValueError(f"invalid event identity/label in {name}/{arm}/{index}")
                scored = event.get("gain") is not None and event.get("collateral") is not None
                if scored and any(type(event[key]) not in (int, float) or not math.isfinite(event[key])
                                  for key in ("gain", "collateral")):
                    raise ValueError("non-finite or non-numeric gate score")
                action = event.get("action", "map_to" if scored else "unknown")
                if scored and (action != "map_to" or not isinstance(event.get("target"), str)
                               or not event["target"]):
                    raise ValueError("scored event lacks a mapping target")
                uid, col = event["uid"], event["col"]
                if uid not in fix:
                    issues.append({"source": name, "issue": "event_outside_historical_fix", "index": index})
                ref = references.get((uid, col))
                if ref and ref["header"] != event["injected"]:
                    issues.append({"source": name, "issue": "reference_header_mismatch", "index": index})
                    ref = None
                row = {**event, "action": action, "action_inferred": "action" not in event,
                       "event_id": f"{name}/{arm}/{index}", "source": name, "regime": regime,
                       "arm": arm, "rule_state_before_sha256": digest(rules),
                       "overlay_sha256": inputs.get(overlay_name),
                       "reference": ref, "independent_correctness": None,
                       "recorded_target_match": event.get("target") == ref["canonical"]
                       if ref and action == "map_to" else None,
                       "scored": scored}
                events.append(row)
                lineages[regime, arm, event["round"], uid, col].append(row)
                if arm == "gated" and scored:
                    group_events[uid, col, event["target"]].append(row)
                if event["accepted"]:
                    if not scored or not event.get("target"):
                        raise ValueError("accepted event without valid gate scores and target")
                    values = rules.setdefault(event["target"], [])
                    if event["injected"] not in values:
                        values.append(event["injected"])
            ledger_ok = rules == state["rules"]
            result_rules = source_result.get(arm_key, {}).get("rules")
            result_ok = result_rules == state["rules"] if result_rules is not None else None
            ledger_checks.append({"source": name, "arm": arm, "reconstructed_from_empty": ledger_ok,
                                  "result_matches_checkpoint": result_ok, "final_sha256": digest(rules)})
            if not ledger_ok or result_ok is False:
                issues.append({"source": name, "arm": arm, "issue": "rule_ledger_mismatch"})

    raw = [e for e in events if e["arm"] == "gated"]
    scored = [e for e in raw if e["scored"]]
    conflicts = [{"key": list(key), "event_ids": [e["event_id"] for e in group],
                  "accepted": sum(e["accepted"] for e in group),
                  "rule_states": sorted({e["rule_state_before_sha256"] for e in group}),
                  "overlay_versions": sorted({e["overlay_sha256"] or "plain" for e in group}),
                  "regimes": sorted({e["regime"] for e in group}),
                  "resolution": "QUARANTINED"}
                 for key, group in sorted(group_events.items())
                 if len({e["accepted"] for e in group}) > 1]
    targets = defaultdict(set)
    for event in scored:
        targets[event["uid"], event["col"]].add(event["target"])
    observations = [stable_json({k: v for k, v in e.items() if k not in (
        "event_id", "source", "regime", "arm")}) for e in scored]
    counts = {"checkpoint_files": len(checkpoint_names), "all_arm_events": len(events),
              "raw_gated_events": len(raw), "scored_events": len(scored),
              "scored_uids": len({e["uid"] for e in scored}),
              "scored_uid_cols": len(targets), "scored_uid_col_targets": len(group_events),
              "accepted": sum(e["accepted"] for e in scored),
              "rejected": sum(not e["accepted"] for e in scored),
              "conflicting_groups": len(conflicts),
              "multi_target_columns": sum(len(v) > 1 for v in targets.values()),
              "exact_duplicate_observations": len(observations) - len(set(observations)),
              "excluded_reasons": dict(sorted(Counter(e["reason"] for e in raw if not e["scored"]).items())),
              "raw_actions": dict(sorted(Counter(e["action"] for e in raw).items())),
              "inferred_actions": sum(e["action_inferred"] for e in raw),
              "reference_matches": sum(e["recorded_target_match"] is True for e in scored),
              "reference_mismatches": sum(e["recorded_target_match"] is False for e in scored),
              "reference_unknown": sum(e["recorded_target_match"] is None for e in scored),
              "accepted_reference_mismatches": sum(e["accepted"] and e["recorded_target_match"] is False for e in scored)}
    family_counts = {}
    source_families = {e["type"] for table in tables.values() for e in table["injections"]}
    for family in sorted(source_families | {e.get("type") or "unknown" for e in raw}):
        group = [e for e in raw if (e.get("type") or "unknown") == family]
        family_counts[family] = {"events": len(group), "scored": sum(e["scored"] for e in group),
                                 "uids": len({e["uid"] for e in group})}

    declared_sources = {}
    for source in pair_doc["meta"]["sources"]:
        match = re.fullmatch(r"([^ /]+) \((vgmc[^/]+_checkpoint\.json)\)", source)
        if not match or match[2] not in checkpoint_names:
            raise ValueError("unknown DPO source declaration")
        declared_sources[match[1]] = match[2].removeprefix("vgmc_").removesuffix("_checkpoint.json")
    pairs = pair_doc["pairs"]
    pair_details, directions, types = [], Counter(), Counter()
    for index, pair in enumerate(pairs):
        if (not isinstance(pair.get("uid"), str) or type(pair.get("col")) is not int
                or pair["col"] < 0 or type(pair.get("gate_fooled")) is not bool):
            raise ValueError("invalid DPO pair identity/flag")
        for choice in (pair["chosen"], pair["rejected"]):
            if choice.get("action") not in {"skip", "hold", "map_to"}:
                raise ValueError("invalid preference action")
            if choice["action"] == "map_to" and (not isinstance(choice.get("target"), str) or not choice["target"]):
                raise ValueError("missing preference target")
        if pair["chosen"] == pair["rejected"]:
            raise ValueError("identical chosen and rejected actions")
        if not pair.get("sources"):
            issues.append({"pair": index, "issue": "missing_pair_sources"})
        directions[f"{pair['chosen']['action']}>{pair['rejected']['action']}"] += 1
        types.update(set(pair["types"]))
        matched = []
        for source in pair["sources"]:
            match = re.fullmatch(r"([^/]+)/(gated|ungated)/r([0-9]+)", source)
            candidates = lineages.get((declared_sources.get(match[1]), match[2], int(match[3]),
                                       pair["uid"], pair["col"]), []) if match else []
            candidates = [e for e in candidates if e.get("target") in {
                pair["chosen"].get("target"), pair["rejected"].get("target")}]
            if not candidates:
                issues.append({"pair": index, "issue": "orphan_pair_source", "source": source})
            matched.extend(candidates)
        refs = {e["reference"]["canonical"] for e in matched if e["reference"]}
        pair_details.append({"pair_index": index, "uid": pair["uid"], "col": pair["col"],
                             "event_ids": sorted({e["event_id"] for e in matched}),
                             "reference_targets": sorted(refs), "independent_preference_correctness": None,
                             "rejected_reference_match": pair["rejected"].get("target") in refs})
    dpo = {"pairs": len(pairs), "uids": len({p["uid"] for p in pairs}),
           "uid_cols": len({(p["uid"], p["col"]) for p in pairs}),
           "directions": dict(sorted(directions.items())), "by_type": dict(sorted(types.items())),
           "gate_fooled": sum(p["gate_fooled"] for p in pairs),
           "rejected_reference_matches": sum(p["rejected_reference_match"] for p in pair_details)}
    historical_uids = sorted(tables)
    manifest = {"historical_sources": source_splits,
                "proposal_train": {"status": "HISTORICAL_ONLY", "uids": historical_uids,
                                   "assigned_train_dev": False},
                **{layer: {"status": "MISSING", "uids": []}
                   for layer in ("gate_validation", "sealed_test", "future_replay")}}
    manifest["sha256"] = digest(manifest)
    common = ["full_source_rows_and_candidate_schema_not_loaded",
              "independent_labels_and_licence_not_verified", "no_new_unseen_splits",
              "power_and_noninferiority_parameters_not_approved"]
    views = {
        "action_sft": {"verdict": "DATA_NO_GO", "candidate_events": len(scored),
                       "uids": counts["scored_uids"], "reasons": common, "training_export": []},
        "risk_prescreen": {"verdict": "DATA_NO_GO", "candidate_events": len(scored),
                           "uids": counts["scored_uids"], "reasons": common + ["gate_label_is_not_harm_label"],
                           "training_export": []},
        "dpo": {"verdict": "PILOT_ONLY" if pairs and not any("pair" in issue for issue in issues) else "DATA_NO_GO", "candidate_pairs": len(pairs),
                "uids": dpo["uids"], "reasons": common + ["historical_preferences_not_independently_verified"]
                + (["one_way_preference"] if len(directions) < 2 else []), "training_export": []}}
    for name in ("action_sft", "risk_prescreen"):
        views[name]["audit_event_ids"] = [e["event_id"] for e in scored]
    views["dpo"]["audit_pair_indices"] = list(range(len(pairs)))
    checkpoint_manifest = "".join(f"logs/graph/eval/{name}:{inputs[name]}\n" for name in checkpoint_names)
    power = [{"uids": n, "assumed_paired_difference_sd": sd,
              "illustrative_mde": round((1.96 + 0.84) * sd / math.sqrt(n), 4)}
             for n in sorted({counts["scored_uids"], dpo["uids"]}) if n
             for sd in (0.25, 0.5, 1.0)]
    return {"meta": {"phase": "audit", "endpoint_calls": 0, "socket_attempts": 0,
                     "purpose": "existing-fact audit; no training or new experimental verdict",
                     "label_scope": "exact match to stored canonical, not independent correctness",
                     "rule_scope": "accepted-event ledger reconstructed from empty; no gain/collateral recomputation"},
            "hashes": {"checkpoint_manifest": hashlib.sha256(checkpoint_manifest.encode()).hexdigest(),
                       "dpo": inputs["dpo_pairs_v0.json"], "all_inputs": digest(inputs)},
            "inputs": dict(sorted(inputs.items())), "counts": counts, "families": family_counts,
            "conflicts": conflicts, "events": events, "ledger_checks": ledger_checks,
            "dpo": dpo, "pair_provenance": pair_details, "manifest": manifest, "views": views,
            "overlay_lineage": {"versioned_borrowed_edges": len(borrowed),
                                "unique_borrowed_edges": len({edge[1:4] for edge in borrowed}),
                                "unique_historical_cross_split_edges": len({edge[1:4] for edge in borrowed if edge[-1]}),
                                "scope": "header variants borrowed, not source-table row copies; shared synthetic EXPAND2 variants are separate"},
            "power": {"status": "SENSITIVITY_ONLY", "method": "normal paired-mean approximation; alpha=.05, power=.80; hypothetical SD, not measured macro-F1 power",
                      "rows": power}, "issues": issues}


def audit_cli():
    parser = argparse.ArgumentParser(description="Audit existing records without loading a corpus or model")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--eval-dir", type=Path, default=EVAL)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.audit:
        if args.output or args.eval_dir != EVAL:
            parser.error("--output/--eval-dir require --audit")
        return main()
    if not args.output:
        parser.error("--audit requires --output in a local untracked location")
    output = args.output.resolve()
    if output.is_relative_to(REPO) and not output.is_relative_to(REPO / "data"):
        parser.error("audit output inside repository must be under ignored data/")
    if output.is_relative_to(args.eval_dir.resolve()):
        parser.error("audit output must not overwrite the input directory")
    if output.exists():
        parser.error("audit output already exists; use a new output path")
    result = audit_data(args.eval_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(stable_json(result) + "\n")
    print(json.dumps({"counts": result["counts"], "dpo": result["dpo"],
                      "views": {k: v["verdict"] for k, v in result["views"].items()},
                      "issue_count": len(result["issues"]), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(audit_cli())
