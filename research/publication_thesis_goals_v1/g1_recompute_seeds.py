#!/usr/bin/env python3
"""Post-hoc source-table clustered reanalysis of W2 E1.6 injection seeds."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import shutil
import socket
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path(__file__).with_name("G1_SEED_REANALYSIS.json")
DEFAULT_SCRATCH = Path("/tmp/loop_d_g1_seed_reanalysis")
SEEDS = [42, 20260831, 20260832]
RATIO = 0.3
BOOTSTRAP_SEED = 20261021
N_BOOT = 20_000
PROTOCOL_KEYS = {
    "E1.1_end_to_end": "E1.1_detected",
    "E1.2_flat": "E1.2_detected",
    "E1.3_hier_expert": "E1.3_detected",
}


def install_zero_network_guard() -> None:
    real_socket = socket.socket

    class BlockedSocket(real_socket):  # type: ignore[misc]
        def connect(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("ZERO_ENDPOINT: outbound socket blocked")

        def connect_ex(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("ZERO_ENDPOINT: outbound socket blocked")

        def sendto(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("ZERO_ENDPOINT: outbound socket blocked")

    def blocked(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("ZERO_ENDPOINT: outbound socket blocked")

    socket.socket = BlockedSocket  # type: ignore[assignment]
    socket.create_connection = blocked  # type: ignore[assignment]
    socket.getaddrinfo = blocked  # type: ignore[assignment]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def cluster_bootstrap(
    rows: list[dict[str, Any]], key: str, n_boot: int = N_BOOT
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["uid"])].append(row)
    uids = sorted(grouped)
    rng = random.Random(BOOTSTRAP_SEED)
    run_weighted: list[float] = []
    uid_equal: list[float] = []
    for _ in range(n_boot):
        sampled = rng.choices(uids, k=len(uids))
        sampled_rows = [row for uid in sampled for row in grouped[uid]]
        run_weighted.append(
            sum(int(row[key]) for row in sampled_rows) / len(sampled_rows)
        )
        uid_equal.append(
            sum(
                sum(int(row[key]) for row in grouped[uid]) / len(grouped[uid])
                for uid in sampled
            )
            / len(sampled)
        )
    return {
        "replicates": n_boot,
        "seed": BOOTSTRAP_SEED,
        "unit": "source_table_uid_cluster",
        "run_weighted_rate_ci95": [
            round(percentile(run_weighted, 0.025), 6),
            round(percentile(run_weighted, 0.975), 6),
        ],
        "uid_equal_rate_ci95": [
            round(percentile(uid_equal, 0.025), 6),
            round(percentile(uid_equal, 0.975), 6),
        ],
    }


def summarize_protocol(
    rows: list[dict[str, Any]], key: str, n_boot: int = N_BOOT
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["uid"])].append(row)
    per_uid = {
        uid: sum(int(row[key]) for row in group) / len(group)
        for uid, group in grouped.items()
    }
    run_weighted = sum(int(row[key]) for row in rows) / len(rows)
    uid_equal = sum(per_uid.values()) / len(per_uid)
    return {
        "table_runs": len(rows),
        "detected_table_runs": sum(int(row[key]) for row in rows),
        "run_weighted_rate": round(run_weighted, 6),
        "unique_source_table_uids": len(grouped),
        "uid_equal_rate": round(uid_equal, 6),
        "source_table_cluster_bootstrap": cluster_bootstrap(rows, key, n_boot),
    }


def uid_overlap_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    seeds_by_uid: dict[str, set[int]] = defaultdict(set)
    runs_by_uid: Counter[str] = Counter()
    for row in rows:
        seeds_by_uid[str(row["uid"])].add(int(row["seed"]))
        runs_by_uid[str(row["uid"])] += 1
    overlap = Counter(len(value) for value in seeds_by_uid.values())
    return {
        "unique_source_table_uids": len(seeds_by_uid),
        "uid_seed_overlap_counts": {
            f"seen_in_{count}_seed(s)": overlap.get(count, 0)
            for count in sorted(overlap)
        },
        "source_table_run_count_distribution": dict(
            sorted(Counter(runs_by_uid.values()).items())
        ),
    }


def leave_one_seed_out(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for omitted in SEEDS:
        subset = [row for row in rows if int(row["seed"]) != omitted]
        output[f"omit_{omitted}"] = {
            "table_runs": len(subset),
            "detected": sum(int(row[key]) for row in subset),
            "rate": round(
                sum(int(row[key]) for row in subset) / len(subset), 6
            ),
        }
    return output


def inject_seed(
    seed: int,
    scratch: Path,
    repo: Path,
    drift_input: Path,
) -> Path:
    output = scratch / f"seed_{seed}"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    sys.path.insert(0, str(repo / "scripts" / "research"))
    import drift_inject

    return_code = drift_inject.main(
        [
            "--input",
            str(drift_input.relative_to(repo)),
            "--out",
            str(output),
            "--ratio",
            str(RATIO),
            "--seed",
            str(seed),
        ]
    )
    if return_code != 0:
        raise RuntimeError(f"injector failed seed={seed} rc={return_code}")
    return output


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--scratch", type=Path, default=DEFAULT_SCRATCH)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    install_zero_network_guard()

    drift_input = REPO / "data" / "research" / "drift_v0" / "input" / "tatqa_tables.json"
    frozen = REPO / "data" / "research" / "drift_v0" / "output"
    frozen_summary = REPO / "logs" / "graph" / "eval" / "_w2_e16_section.json"
    if args.scratch.exists():
        shutil.rmtree(args.scratch)
    args.scratch.mkdir(parents=True)

    sys.path.insert(0, str(REPO / "research"))
    sys.path.insert(0, str(REPO / "scripts"))
    import m1_statement_parser as mp
    import paper_t1_eval_baselines as t1

    all_rows: list[dict[str, Any]] = []
    per_seed: list[dict[str, Any]] = []
    gate: dict[str, Any] | None = None
    for seed in SEEDS:
        output = inject_seed(seed, args.scratch, REPO, drift_input)
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        if seed == SEEDS[0]:
            gate = {
                "injected_tables_sha256": [
                    sha256_file(output / "injected_tables.json"),
                    sha256_file(frozen / "injected_tables.json"),
                ],
                "injection_map_sha256": [
                    sha256_file(output / "injection_map.json"),
                    sha256_file(frozen / "injection_map.json"),
                ],
                "determinism_sha256": [
                    report.get("determinism_sha256"),
                    json.loads(
                        (frozen / "report.json").read_text(encoding="utf-8")
                    ).get("determinism_sha256"),
                ],
            }
            gate["pass"] = all(
                pair[0] == pair[1]
                for pair in (
                    gate["injected_tables_sha256"],
                    gate["injection_map_sha256"],
                    gate["determinism_sha256"],
                )
            )
        t1.DRIFT = output
        arm = t1.run_arm_b(mp)
        seed_rows = []
        for table in sorted(arm["tables"], key=lambda item: item["uid"]):
            row = {
                "seed": seed,
                "uid": table["uid"],
                "n_injections": table["n_injections"],
                "types": table["types"],
            }
            for protocol, key in PROTOCOL_KEYS.items():
                row[key] = bool(table[key])
            seed_rows.append(row)
            all_rows.append(row)
        per_seed.append(
            {
                "seed": seed,
                "n_tables": len(seed_rows),
                "n_injections": report.get("n_injections_total"),
                "protocols": {
                    protocol: summarize_protocol(
                        seed_rows, key, n_boot=args.n_boot
                    )
                    for protocol, key in PROTOCOL_KEYS.items()
                },
            }
        )

    protocol_summaries = {
        protocol: summarize_protocol(all_rows, key, n_boot=args.n_boot)
        for protocol, key in PROTOCOL_KEYS.items()
    }
    flat_rows = all_rows
    rates = [
        row["protocols"]["E1.2_flat"]["run_weighted_rate"] for row in per_seed
    ]
    pooled_from_rows = sum(int(row["E1.2_detected"]) for row in flat_rows)
    if pooled_from_rows != 219 or len(flat_rows) != 282:
        raise RuntimeError(
            f"unexpected E1.2 reconstruction: {pooled_from_rows}/{len(flat_rows)}"
        )
    historical = json.loads(frozen_summary.read_text(encoding="utf-8"))
    naive_ci = historical["pooled_across_seeds"]["E1.2_flat"][
        "table_detect_rate_ci95"
    ]
    cluster_ci = protocol_summaries["E1.2_flat"][
        "source_table_cluster_bootstrap"
    ]["run_weighted_rate_ci95"]
    payload = {
        "schema": "g1_injection_seed_source_table_reanalysis_v1",
        "date": "2026-10-21",
        "status": "POST_HOC_REANALYSIS_COMPLETE",
        "evidence_identity": "POST_HOC_DETERMINISTIC_REANALYSIS_NOT_NEW_MODEL_EXPERIMENT",
        "estimands": {
            "table_run": (
                "Probability that a sampled injected table-seed run is detected "
                "under the three fixed injection seeds."
            ),
            "source_table_uid_equal": (
                "Mean of each source-table UID's detection proportion across "
                "the seeds in which that UID is injected, weighting UIDs equally."
            ),
            "seed_generalization": (
                "Not estimated reliably because only three injection seeds are "
                "available; report the three rates and leave-one-seed-out values."
            ),
        },
        "source_hashes": {
            "input_tatqa_tables_sha256": sha256_file(drift_input),
            "frozen_injected_tables_sha256": sha256_file(
                frozen / "injected_tables.json"
            ),
            "frozen_injection_map_sha256": sha256_file(
                frozen / "injection_map.json"
            ),
            "historical_summary_sha256": sha256_file(frozen_summary),
        },
        "seed42_byte_identity_gate": gate,
        "seeds": SEEDS,
        "ratio": RATIO,
        "per_seed": per_seed,
        "pooled_protocols": protocol_summaries,
        "uid_overlap": uid_overlap_summary(all_rows),
        "flat_seed_sensitivity": {
            "per_seed_rates": rates,
            "spread": round(max(rates) - min(rates), 6),
            "leave_one_seed_out": leave_one_seed_out(
                flat_rows, "E1.2_detected"
            ),
        },
        "historical_pooled_e1_2": {
            "point_estimate": historical["pooled_across_seeds"]["E1.2_flat"][
                "table_detect_rate"
            ],
            "naive_table_run_bootstrap_ci95": naive_ci,
        },
        "rows": all_rows,
        "ruling": {
            "keep_point_estimate": True,
            "retained_text": (
                "The denominator-weighted table-run estimate 219/282 = 0.7766 "
                "is retained as a descriptive result."
            ),
            "replace_interval": True,
            "recommended_interval": (
                "Use the source-table UID-cluster bootstrap interval and the "
                "three-seed range/leave-one-seed-out sensitivity. Keep the old "
                "[0.7270, 0.8227] only as a historical naive table-run interval, "
                "not as a source-table uncertainty interval."
            ),
            "cluster_ci95": cluster_ci,
            "naive_ci95": naive_ci,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "pooled_e1_2": protocol_summaries["E1.2_flat"],
                "uid_overlap": payload["uid_overlap"],
                "ruling": payload["ruling"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
