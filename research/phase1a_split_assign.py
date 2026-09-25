"""Deterministic, label-blind layer assignment for phase1a packages (zero model, zero connect).

Turns an approved public-source staging tree into `layers` rows that satisfy
research/phase1a_data_contract.py: every row carries exactly MANIFEST_ROW_FIELDS,
uid == lineage_uid(dataset_id, dataset_revision, lineage_root_id), no uid or lineage
root crosses partitions, and no independence_cluster crosses role layers.

The rule is pre-registered and reads no label, gold match, perturbation trajectory or
pipeline output: cluster-level double-salt hash bucketing (one salt for the bounded
universe, an independent salt for the layer), so the assignment is fixed before any
annotation exists and cannot be tuned against an outcome.

Governance is encoded rather than only documented: the per-namespace role limit is read
from docs/datasets/paper-public-source-registry-v1.json (`role_fit`). A namespace whose
role_fit does not literally contain `gate_validation` / `sealed_test` emits those
partitions empty, keeps the affected rows visible under `pending_ruling_rows`, and reports
LAYER_CAPACITY_BLOCKED_PILOT_ONLY unless an explicit user ruling id is passed via
--pilot-override-ruling. Every file read must appear in the staging sha256 manifest with a
matching digest. The artifact carries no wall-clock field, so a re-run is byte-identical.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.phase1a_data_contract import (  # noqa: E402  reuse, never reimplement
    MANIFEST_ROW_FIELDS,
    REQUIRED_PARTITIONS,
    ROLE_LAYER_BY_PARTITION,
    _digest_object,
    lineage_uid,
)

CONTRACT_VERSION = "phase1a-split-assignment-v1"
UNIVERSE_SALT = "phase1a-split-v1:universe"
LAYER_SALT = "phase1a-split-v1:layer"
SAMPLE_SALT = "phase1a-split-v1:sample-id"
LAYER_BUCKETS = (
    ("proposal_train.train", 0, 50),
    ("proposal_train.dev", 50, 70),
    ("gate_validation", 70, 85),
    ("sealed_test", 85, 100),
)
HEX40 = set("0123456789abcdef")
DEFAULT_REGISTRY = REPO / "docs" / "datasets" / "paper-public-source-registry-v1.json"
FINQA_ID_RE = re.compile(r"^(?P<filing>.+)/(?P<page>page_\d+\.pdf)-(?P<k>\d+)$")
FINQA_SOURCES = (("finqa/train.json", "train"), ("finqa/dev.json", "dev"))
VALENTINE_DATA_RELPREFIX = "valentine/experiments/data"
CSV_FIELD_LIMIT = 10 ** 8


class SplitError(ValueError):
    """Fail-closed rejection with a machine-readable code."""

    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def install_network_guard() -> None:
    """Any connect attempt raises; the observed port set stays empty."""

    def _blocked(*_a: object, **_k: object) -> object:
        raise SplitError("zero_connect_violation")

    socket.socket.connect = _blocked  # type: ignore[method-assign]
    socket.create_connection = _blocked  # type: ignore[assignment]


def load_sha256_manifest(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            raise SplitError("invalid_manifest_line", line=line[:80])
        digest, rel = parts[0], parts[1].lstrip("*")
        if len(digest) != 64 or not set(digest) <= HEX40:
            raise SplitError("invalid_manifest_digest", path=rel)
        if rel in out:
            raise SplitError("duplicate_manifest_path", path=rel)
        out[rel] = digest
    if not out:
        raise SplitError("empty_sha256_manifest", path=str(path))
    return out


def read_verified(root: Path, rel: str, manifest: dict[str, str]) -> bytes:
    want = manifest.get(rel)
    if want is None:
        raise SplitError("input_not_in_sha256_manifest", path=rel)
    path = root / rel
    if not path.is_file():
        raise SplitError("missing_input_file", path=rel)
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != want:
        raise SplitError("input_sha256_mismatch", path=rel, expected=want, actual=got)
    return raw


def load_registry_entry(registry_path: Path, dataset_id: str) -> dict[str, object]:
    """Role limit, cluster namespace and revision all come from the registry, not from code."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for source in registry.get("sources", []):
        if isinstance(source, dict) and source.get("dataset_id") == dataset_id:
            role_fit = source.get("role_fit")
            if not isinstance(role_fit, list) or not role_fit:
                raise SplitError("invalid_registry_role_fit", dataset_id=dataset_id)
            namespace = source.get("independence_cluster_namespace")
            head = source.get("checked_default_head")
            if not isinstance(namespace, str) or not namespace.strip():
                raise SplitError("invalid_registry_cluster_namespace", dataset_id=dataset_id)
            if not isinstance(head, str) or len(head) != 40 or not set(head) <= HEX40:
                raise SplitError("invalid_registry_head", dataset_id=dataset_id)
            return {
                "role_fit": [str(r) for r in role_fit],
                "cluster_namespace": namespace,
                "dataset_revision": head,
            }
    raise SplitError("namespace_not_in_registry", dataset_id=dataset_id)


def bucket(salt: str, key: str, mod: int) -> int:
    digest = hashlib.sha256(f"{salt}\n{key}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % mod


def stable_sample_id(dataset_id: str, dataset_revision: str, natural_key: str) -> str:
    return _digest_object(
        {
            "salt": SAMPLE_SALT,
            "dataset_id": dataset_id,
            "dataset_revision": dataset_revision,
            "natural_key": natural_key,
        }
    )


def layer_for_bucket(value: int) -> str:
    for name, low, high in LAYER_BUCKETS:
        if low <= value < high:
            return name
    raise SplitError("layer_bucket_out_of_range", value=value)


def finqa_units(
    root: Path, manifest: dict[str, str], record: dict[str, str]
) -> list[dict[str, str]]:
    """One unit per FinQA example; lineage root = report page, cluster = filing (TICKER/YEAR)."""
    units: list[dict[str, str]] = []
    for rel, split in FINQA_SOURCES:
        entries = json.loads(read_verified_recording(root, rel, manifest, record))
        if not isinstance(entries, list):
            raise SplitError("invalid_source_json", path=rel)
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise SplitError("invalid_example_object", path=rel, index=index)
            example_id = entry.get("id")
            if not isinstance(example_id, str) or not example_id.strip():
                raise SplitError("missing_example_id", path=rel, index=index)
            match = FINQA_ID_RE.match(example_id)
            if match is None:
                raise SplitError("unparsable_example_id", path=rel, example_id=example_id)
            lineage_root_id = match.group("filing") + "/" + match.group("page")
            if example_id.rsplit("-", 1)[0] != lineage_root_id:
                raise SplitError("lineage_root_derivation_mismatch", example_id=example_id)
            units.append(
                {
                    "cluster_key": match.group("filing"),
                    "lineage_root_id": lineage_root_id,
                    "source_split": split,
                    "natural_key": example_id,
                }
            )
    if not units:
        raise SplitError("empty_inventory", namespace="finqa")
    return units


def valentine_units(
    root: Path, manifest: dict[str, str], record: dict[str, str]
) -> list[dict[str, str]]:
    """One unit per source column of one NYC pair.

    Only `source_table.csv` header rows are read. ground_truth.json, the perturbation
    trajectory files and every data row stay untouched, which keeps the assignment
    label-blind by construction rather than by promise.
    """
    data_root = root / VALENTINE_DATA_RELPREFIX
    if not data_root.is_dir():
        raise SplitError("missing_valentine_data_root", path=str(data_root))
    pairs = sorted(p.name for p in data_root.iterdir() if p.is_dir())
    if not pairs:
        raise SplitError("empty_valentine_data_root", path=str(data_root))
    csv.field_size_limit(CSV_FIELD_LIMIT)
    units: list[dict[str, str]] = []
    for pair in pairs:
        rel = VALENTINE_DATA_RELPREFIX + "/" + pair + "/source_table.csv"
        text = read_verified_recording(root, rel, manifest, record).decode("utf-8-sig", "replace")
        try:
            header = next(csv.reader(io.StringIO(text)))
        except StopIteration:
            raise SplitError("empty_source_table", pair=pair) from None
        cols = [cell.strip() for cell in header]
        if not cols or any(not cell for cell in cols):
            raise SplitError("invalid_source_header", pair=pair)
        if len(set(cols)) != len(cols):
            raise SplitError("duplicate_source_header_cell", pair=pair)
        for col_index, col in enumerate(cols):
            units.append(
                {
                    "cluster_key": pair,
                    "lineage_root_id": pair + "/source_table.csv",
                    "source_split": "unsplit_benchmark_pairs",
                    "natural_key": pair + "#" + str(col_index) + "#" + col,
                }
            )
    if not units:
        raise SplitError("empty_inventory", namespace="valentine_nyc")
    return units


NAMESPACE_BUILDERS = {"finqa": finqa_units, "valentine_nyc": valentine_units}


def read_verified_recording(
    root: Path, rel: str, manifest: dict[str, str], record: dict[str, str]
) -> bytes:
    raw = read_verified(root, rel, manifest)
    record[rel] = manifest[rel]
    return raw


def assign(
    units: list[dict[str, str]],
    *,
    dataset_id: str,
    dataset_revision: str,
    cluster_namespace: str,
    role_fit: list[str],
    m_universe: int,
    pilot_override_ruling: str | None,
) -> dict[str, object]:
    """Cluster-level double-salt bucketing; never inspects a label or a gold match."""
    clusters = sorted({unit["cluster_key"] for unit in units})
    universe = [c for c in clusters if bucket(UNIVERSE_SALT, c, m_universe) == 0]
    universe_set = set(universe)
    gate_allowed = "gate_validation" in role_fit or bool(pilot_override_ruling)
    sealed_allowed = "sealed_test" in role_fit or bool(pilot_override_ruling)
    layers: dict[str, object] = {
        "proposal_train": {"train": [], "dev": []},
        "gate_validation": [],
        "sealed_test": [],
        "future_replay": [],
    }
    pending: list[dict[str, object]] = []
    excluded_by_universe = 0
    for unit in sorted(units, key=lambda item: item["natural_key"]):
        if unit["cluster_key"] not in universe_set:
            excluded_by_universe += 1
            continue
        cluster = cluster_namespace + ":" + unit["cluster_key"]
        partition = layer_for_bucket(bucket(LAYER_SALT, cluster, 100))
        row = {
            "sample_id": stable_sample_id(dataset_id, dataset_revision, unit["natural_key"]),
            "uid": lineage_uid(dataset_id, dataset_revision, unit["lineage_root_id"]),
            "dataset_id": dataset_id,
            "dataset_revision": dataset_revision,
            "source_split": unit["source_split"],
            "independence_cluster": cluster,
            "lineage_root_id": unit["lineage_root_id"],
            "transformation_parent_id": None,
        }
        if partition == "gate_validation" and not gate_allowed:
            pending.append({"intended_partition": partition, "row": row})
            continue
        if partition == "sealed_test" and not sealed_allowed:
            pending.append({"intended_partition": partition, "row": row})
            continue
        if partition.startswith("proposal_train."):
            layers["proposal_train"][partition.split(".", 1)[1]].append(row)  # type: ignore[index]
        else:
            layers[partition].append(row)  # type: ignore[attr-defined]
    blocked = [
        name
        for name, allowed in (("gate_validation", gate_allowed), ("sealed_test", sealed_allowed))
        if not allowed
    ]
    return {
        "layers": layers,
        "pending_ruling_rows": pending,
        "blocked_partitions": blocked,
        "clusters_total": len(clusters),
        "clusters_in_universe": len(universe),
        "excluded_by_universe_rule": excluded_by_universe,
        "units_total": len(units),
    }


def validate_layers(layers: dict[str, object], dataset_id: str, dataset_revision: str) -> dict[str, dict[str, int]]:
    """Mirror the contract's layer_isolation invariants; any breach is our bug, so raise."""
    flat: dict[str, list[dict[str, object]]] = {
        "proposal_train.train": layers["proposal_train"]["train"],  # type: ignore[index]
        "proposal_train.dev": layers["proposal_train"]["dev"],  # type: ignore[index]
        "gate_validation": layers["gate_validation"],  # type: ignore[assignment]
        "sealed_test": layers["sealed_test"],  # type: ignore[assignment]
        "future_replay": layers["future_replay"],  # type: ignore[assignment]
    }
    seen_samples: set[str] = set()
    uid_partitions: dict[str, set[str]] = {}
    root_partitions: dict[str, set[str]] = {}
    cluster_layers: dict[str, set[str]] = {}
    counts: dict[str, dict[str, int]] = {}
    for partition, rows in flat.items():
        uids: set[str] = set()
        for row in rows:
            if set(row) != MANIFEST_ROW_FIELDS:
                raise SplitError("invalid_row_fields", partition=partition)
            uid = str(row["uid"])
            expected = lineage_uid(dataset_id, dataset_revision, str(row["lineage_root_id"]))
            if uid != expected:
                raise SplitError("lineage_uid_mismatch", partition=partition)
            sample_id = str(row["sample_id"])
            if sample_id in seen_samples:
                raise SplitError("duplicate_sample_id", partition=partition)
            seen_samples.add(sample_id)
            uids.add(uid)
            uid_partitions.setdefault(uid, set()).add(partition)
            root_partitions.setdefault(str(row["lineage_root_id"]), set()).add(partition)
            cluster_layers.setdefault(str(row["independence_cluster"]), set()).add(
                ROLE_LAYER_BY_PARTITION[partition]
            )
        counts[partition] = {
            "samples": len(rows),
            "uids": len(uids),
            "clusters": len({str(r["independence_cluster"]) for r in rows}),
        }
    for uid, parts in sorted(uid_partitions.items()):
        if len(parts) > 1:
            raise SplitError("uid_cross_partition", uid=uid, partitions=sorted(parts))
    for root, parts in sorted(root_partitions.items()):
        if len(parts) > 1:
            raise SplitError("lineage_root_cross_partition", lineage_root_id=root)
    for cluster, role_layers in sorted(cluster_layers.items()):
        if len(role_layers) > 1:
            raise SplitError("independence_cluster_cross_role_layer", independence_cluster=cluster)
    return counts


def compute(
    *,
    namespace: str,
    root: Path,
    manifest: dict[str, str],
    registry_entry: dict[str, object],
    m_universe: int,
    pilot_override_ruling: str | None,
) -> dict[str, object]:
    record: dict[str, str] = {}
    units = NAMESPACE_BUILDERS[namespace](root, manifest, record)
    dataset_id = namespace
    dataset_revision = str(registry_entry["dataset_revision"])
    role_fit = [str(r) for r in registry_entry["role_fit"]]  # type: ignore[index]
    result = assign(
        units,
        dataset_id=dataset_id,
        dataset_revision=dataset_revision,
        cluster_namespace=str(registry_entry["cluster_namespace"]),
        role_fit=role_fit,
        m_universe=m_universe,
        pilot_override_ruling=pilot_override_ruling,
    )
    layers = result["layers"]
    assert isinstance(layers, dict)
    counts = validate_layers(layers, dataset_id, dataset_revision)
    reasons: list[str] = []
    blocked = [str(b) for b in result["blocked_partitions"]]  # type: ignore[index]
    if blocked:
        reasons.append("LAYER_CAPACITY_BLOCKED_PILOT_ONLY:" + ",".join(blocked))
    pending = result["pending_ruling_rows"]
    assert isinstance(pending, list)
    if pending:
        reasons.append("ROWS_WITHHELD_PENDING_RULING:" + str(len(pending)))
    for partition in REQUIRED_PARTITIONS:
        if counts[partition]["samples"] == 0:
            reasons.append("EMPTY_REQUIRED_PARTITION:" + partition)
    return {
        "contract_version": CONTRACT_VERSION,
        "namespace": namespace,
        "dataset_id": dataset_id,
        "dataset_revision": dataset_revision,
        "cluster_namespace": registry_entry["cluster_namespace"],
        "registry_role_fit": role_fit,
        "m_universe": m_universe,
        "salts": {"universe": UNIVERSE_SALT, "layer": LAYER_SALT, "sample_id": SAMPLE_SALT},
        "layer_buckets": [list(item) for item in LAYER_BUCKETS],
        "pilot_override_ruling": pilot_override_ruling,
        "status": "READY" if not reasons else "INCOMPLETE",
        "reasons": reasons,
        "counts": {
            "units_total": result["units_total"],
            "clusters_total": result["clusters_total"],
            "clusters_in_universe": result["clusters_in_universe"],
            "excluded_by_universe_rule": result["excluded_by_universe_rule"],
            "partitions": counts,
        },
        "layers": layers,
        "layers_manifest_sha256": _digest_object(layers),
        "pending_ruling_rows": pending,
        "input_sha256": dict(sorted(record.items())),
        "observed_ports": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--namespace", required=True, choices=sorted(NAMESPACE_BUILDERS))
    ap.add_argument("--staging-root", required=True, type=Path)
    ap.add_argument("--sha256-manifest", required=True, type=Path)
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--m-universe", required=True, type=int)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--pilot-override-ruling", default=None)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    commit = args.commit.strip()
    if len(commit) != 40 or not set(commit) <= HEX40:
        raise SplitError("invalid_split_commit", commit=commit)
    if args.m_universe < 1:
        raise SplitError("invalid_m_universe", m_universe=args.m_universe)
    ruling = args.pilot_override_ruling
    if ruling is not None:
        ruling = ruling.strip()
        if not ruling:
            raise SplitError("empty_pilot_override_ruling")
    install_network_guard()
    manifest = load_sha256_manifest(args.sha256_manifest)
    entry = load_registry_entry(args.registry, args.namespace)
    kwargs = {
        "namespace": args.namespace,
        "root": args.staging_root,
        "manifest": manifest,
        "registry_entry": entry,
        "m_universe": args.m_universe,
        "pilot_override_ruling": ruling,
    }
    first = compute(**kwargs)
    second = compute(**kwargs)
    if json.dumps(first, sort_keys=True) != json.dumps(second, sort_keys=True):
        raise SplitError("nondeterministic_assignment")
    first["commit"] = commit
    args.out.write_text(
        json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    counts = first["counts"]
    assert isinstance(counts, dict)
    parts = counts["partitions"]
    assert isinstance(parts, dict)
    summary = " ".join(
        f"{name}={parts[name]['samples']}s/{parts[name]['uids']}u" for name in sorted(parts)
    )
    print(
        "wrote " + str(args.out) + " status=" + str(first["status"])
        + " reasons=" + json.dumps(first["reasons"]) + " | " + summary
    )
    print("layers_manifest_sha256=" + str(first["layers_manifest_sha256"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SplitError as exc:
        print("SPLIT_FAIL " + exc.code + " " + json.dumps(exc.detail, sort_keys=True, default=str), file=sys.stderr)
        raise SystemExit(2) from None
