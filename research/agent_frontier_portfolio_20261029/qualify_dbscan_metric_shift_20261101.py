#!/usr/bin/env python3
"""Inspect one natural metric change on a frozen public-task input; no Agent."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path


COMMIT = "726e1f79b96b0cb3d729d0e55a1c847e0b5353ae"
HASHES = {"citsci_train.csv": "5a1169e807ceddec822fa676bac29f92562a3a463bd27178b15778c61b642f19",
          "expert_train.csv": "f7402b188f34c0dcf3c843545b15a486167d2e5770aec7cb5773fbb8aa777d92"}


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def equivalent_labels(first, second):
    """Compare partitions up to cluster renaming, preserving noise membership."""
    if len(first) != len(second):
        return False
    forward, reverse = {}, {}
    for left, right in zip(first, second):
        left, right = int(left), int(right)
        if (left == -1) != (right == -1):
            return False
        if left == -1:
            continue
        if (left in forward and forward[left] != right) or (right in reverse and reverse[right] != left):
            return False
        forward[left], reverse[right] = right, left
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve the existing qualification output")
    import numpy as np
    import pandas as pd
    import scipy
    import sklearn
    from sklearn.cluster import DBSCAN

    commit = subprocess.check_output(["git", "-C", str(args.checkout), "rev-parse", "HEAD"], text=True).strip()
    if commit != COMMIT:
        raise ValueError("unexpected benchmark revision")
    family = args.checkout / "tasks/dbscan-parameter-tuning"
    inputs = []
    for version in (1, 2):
        data = family / ("dbscan-parameter-tuning-" + str(version)) / "environment/data"
        for name, expected in HASHES.items():
            if sha(data / name) != expected:
                raise ValueError("unexpected data hash: " + str(version) + "/" + name)
        inputs.append(data)
    start = time.monotonic()
    citizen = pd.read_csv(inputs[0] / "citsci_train.csv", usecols=["file_rad", "x", "y"])
    expert = pd.read_csv(inputs[0] / "expert_train.csv", usecols=["file_rad"])
    expert_ids = set(expert["file_rad"].dropna().astype(str))
    grouped = {str(key): value[["x", "y"]].to_numpy(dtype=float)
               for key, value in citizen.groupby("file_rad", sort=False)}
    differences, missing, samples = 0, 0, []
    for image in sorted(expert_ids, key=lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()):
        points = grouped.get(image)
        if points is None or len(points) == 0:
            missing += 1
            continue
        source = DBSCAN(eps=12, min_samples=5, metric="euclidean", n_jobs=1).fit_predict(points)
        target = DBSCAN(eps=12, min_samples=5, metric="chebyshev", n_jobs=1).fit_predict(points)
        different = not equivalent_labels(source, target)
        differences += different
        if len(samples) < 10:
            samples.append({"image_id_sha256": hashlib.sha256(image.encode("utf-8")).hexdigest(),
                            "point_count": len(points), "different_partition": different})
    result = {"status": "SOURCE_QUALIFICATION_NOT_AGENT_EVALUATION", "commit": commit,
              "data_sha256": HASHES, "metric_pair": ["euclidean", "chebyshev"],
              "settings": {"min_samples": 5, "epsilon": 12, "shape_weight": 1.0},
              "expert_image_count": len(expert_ids), "images_without_citizen_points": missing,
              "different_partition_count": differences, "first_10_hash_order": samples,
              "elapsed_seconds": round(time.monotonic() - start, 3),
              "versions": {"numpy": np.__version__, "pandas": pd.__version__,
                           "scipy": scipy.__version__, "sklearn": sklearn.__version__},
              "model_calls": 0, "limitations": "One grid point; researcher-exposed task; not benchmark reproduction."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("expert_image_count", "images_without_citizen_points",
                                                   "different_partition_count", "elapsed_seconds", "versions")}))


if __name__ == "__main__":
    main()
