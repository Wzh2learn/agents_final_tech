#!/usr/bin/env python3
"""Cross-check one computed point against the released source implementations."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path


SOURCE_HASHES = ("b25dbd168d4dd1a58873abfad38f1fccafab68cbbbf6cf9f79eb6114ab8e475e",
                 "f17b89148e9db5fabd6eaa7f624df7ee0818634225ea97a106831630b8488981")


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--source1", type=Path, required=True)
    parser.add_argument("--source2", type=Path, required=True)
    parser.add_argument("--fixedpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous cross-check")
    for source, expected in zip((args.source1, args.source2), SOURCE_HASHES):
        if sha(source) != expected:
            raise ValueError("released source changed")
    import pandas as pd
    import sklearn

    citizen = pd.read_csv(args.data / "citsci_train.csv", usecols=["file_rad", "x", "y"])
    expert = pd.read_csv(args.data / "expert_train.csv", usecols=["file_rad", "x", "y"])
    cgroups = {str(k): v[["x", "y"]].to_numpy(dtype=float) for k, v in citizen.groupby("file_rad", sort=False)}
    egroups = {str(k): v[["x", "y"]].to_numpy(dtype=float) for k, v in expert.groupby("file_rad", sort=False)}
    image_data = [(cgroups.get(key, []), value) for key, value in egroups.items()]
    previous = json.loads(args.fixedpoint.read_text(encoding="utf-8"))
    if previous["settings"]["epsilon"] != 12 or previous["settings"]["min_samples"] != 5:
        raise ValueError("fixed-point settings changed")
    results = {}
    for metric, source in zip(("euclidean", "chebyshev"), (args.source1, args.source2)):
        module = runpy.run_path(str(source), run_name="benchmark_reference_import")
        scored = module["evaluate_hyperparams"]((5, 12, 1.0), image_data)
        if scored is None:
            raise ValueError("reference filtered the selected setting")
        ours = previous["aggregate"][metric]
        difference_f1 = float(scored["F1"]) - ours["mean_f1"]
        difference_delta = float(scored["delta"]) - ours["mean_delta_matched_images"]
        results[metric] = {"reference_f1": float(scored["F1"]), "reference_delta": float(scored["delta"]),
                           "difference_f1": difference_f1, "difference_delta": difference_delta,
                           "agrees_within_1e-10": abs(difference_f1) < 1e-10 and abs(difference_delta) < 1e-10}
    output = {"status": "SOURCE_IMPLEMENTATION_FIXED_POINT_CROSSCHECK", "source_sha256": SOURCE_HASHES,
              "fixedpoint_raw_sha256": sha(args.fixedpoint), "images": len(image_data),
              "results": results, "sklearn": sklearn.__version__, "model_calls": 0,
              "limitation": "Same input and runtime, one point; source code is not independent ground truth."}
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(output))


if __name__ == "__main__":
    main()
