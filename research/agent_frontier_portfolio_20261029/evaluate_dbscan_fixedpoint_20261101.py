#!/usr/bin/env python3
"""Post-hoc score one fixed DBSCAN setting under two task-visible metrics."""

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

from qualify_dbscan_metric_shift_20261101 import HASHES, equivalent_labels, sha


def greedy_metrics(centroids, experts, cutoff=100.0):
    candidates = sorted((math.dist(a, b), i, j) for i, a in enumerate(centroids)
                        for j, b in enumerate(experts))
    used_centroids, used_experts, distances = set(), set(), []
    for distance, i, j in candidates:
        if distance >= cutoff:
            break
        if i not in used_centroids and j not in used_experts:
            used_centroids.add(i)
            used_experts.add(j)
            distances.append(distance)
    tp = len(distances)
    fp, fn = len(centroids) - tp, len(experts) - tp
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return f1, sum(distances) / len(distances) if distances else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous results")
    for name, expected in HASHES.items():
        if sha(args.data / name) != expected:
            raise ValueError("unexpected frozen input: " + name)
    import numpy as np
    import pandas as pd
    import sklearn
    from sklearn.cluster import DBSCAN

    start = time.monotonic()
    citizen = pd.read_csv(args.data / "citsci_train.csv", usecols=["file_rad", "x", "y"])
    expert = pd.read_csv(args.data / "expert_train.csv", usecols=["file_rad", "x", "y"])
    cgroups = {str(k): v[["x", "y"]].to_numpy(dtype=float) for k, v in citizen.groupby("file_rad", sort=False)}
    egroups = {str(k): v[["x", "y"]].to_numpy(dtype=float) for k, v in expert.groupby("file_rad", sort=False)}
    rows = []
    for image in sorted(egroups, key=lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()):
        points, truth = cgroups.get(image), egroups[image]
        if points is None or len(points) == 0:
            rows.append({"image_id_sha256": hashlib.sha256(image.encode()).hexdigest(),
                         "euclidean": {"f1": 0.0, "delta": None},
                         "chebyshev": {"f1": 0.0, "delta": None}, "partition_differs": False})
            continue
        item = {"image_id_sha256": hashlib.sha256(image.encode()).hexdigest()}
        labels = {}
        for metric in ("euclidean", "chebyshev"):
            labels[metric] = DBSCAN(eps=12, min_samples=5, metric=metric, n_jobs=1).fit_predict(points)
            ids = sorted(int(x) for x in set(labels[metric]) if x != -1)
            centers = [np.mean(points[labels[metric] == cluster], axis=0) for cluster in ids]
            f1, delta = greedy_metrics(centers, truth)
            item[metric] = {"f1": f1, "delta": delta}
        item["partition_differs"] = not equivalent_labels(labels["euclidean"], labels["chebyshev"])
        rows.append(item)
    aggregate = {}
    for metric in ("euclidean", "chebyshev"):
        deltas = [row[metric]["delta"] for row in rows if row[metric]["delta"] is not None]
        aggregate[metric] = {"mean_f1": sum(row[metric]["f1"] for row in rows) / len(rows),
                             "mean_delta_matched_images": sum(deltas) / len(deltas) if deltas else None,
                             "images_with_delta": len(deltas)}
    result = {"status": "POSTHOC_FIXED_POINT_QUALIFICATION", "settings": {"epsilon": 12, "min_samples": 5,
              "shape_weight": 1.0, "match_cutoff_strictly_less_than": 100},
              "image_count": len(rows), "partition_difference_count": sum(row["partition_differs"] for row in rows),
              "aggregate": aggregate, "images": rows, "sklearn": sklearn.__version__,
              "elapsed_seconds": round(time.monotonic() - start, 3), "model_calls": 0,
              "limitation": "Single setting on exposed input; not full Pareto search or benchmark reproduction."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("image_count", "partition_difference_count", "aggregate", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
