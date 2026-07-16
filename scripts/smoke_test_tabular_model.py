"""Run a synthetic credit-rule classification smoke test with TabPFN or TabFM."""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np
import pandas as pd


FEATURES = ["age", "debt_ratio", "consecutive_overdue_months"]


def parse_args() -> argparse.Namespace:
    """Parse the tabular model, execution device, and checkpoint options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="tabpfn", choices=("tabpfn", "tabfm"))
    parser.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    parser.add_argument(
        "--model-version",
        default="v2",
        choices=("v2", "v2.5", "v2.6", "v3"),
        help="TabPFN v2 supports direct download; newer versions require gated-model acceptance.",
    )
    parser.add_argument(
        "--checkpoint-path",
        default="/home/testuser/wzh/models/hf/tabfm-1.0.0-pytorch",
        help="Local TabFM checkpoint root; ignored for TabPFN.",
    )
    return parser.parse_args()


def build_dataset() -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """Return a deterministic, desensitized rule-eligibility dataset."""
    train = pd.DataFrame(
        [
            [25, 0.35, 0],
            [42, 0.55, 1],
            [58, 0.62, 2],
            [31, 0.48, 0],
            [19, 0.30, 0],
            [63, 0.40, 0],
            [45, 0.75, 1],
            [36, 0.50, 3],
        ],
        columns=FEATURES,
    )
    labels = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    test = pd.DataFrame(
        [
            [30, 0.45, 0],
            [65, 0.45, 0],
            [40, 0.80, 3],
        ],
        columns=FEATURES,
    )
    return train, labels, test


def build_classifier(args: argparse.Namespace) -> tuple[object, str]:
    """Create the requested tabular foundation-model classifier."""
    if args.model == "tabfm":
        from tabfm import TabFMClassifier
        from tabfm import tabfm_v1_0_0_pytorch

        model = tabfm_v1_0_0_pytorch.load(
            model_type="classification",
            checkpoint_path=args.checkpoint_path,
            device=args.device,
        )
        return TabFMClassifier(model=model, n_estimators=2), "TabFMClassifier"

    os.environ["TABPFN_MODEL_VERSION"] = args.model_version
    from tabpfn import TabPFNClassifier

    return TabPFNClassifier(device=args.device, n_estimators=2), "TabPFNClassifier"


def main() -> None:
    """Fit the selected model on synthetic rows and print predictions as JSON."""
    args = parse_args()
    train, labels, test = build_dataset()
    classifier, classifier_name = build_classifier(args)

    started = time.perf_counter()
    classifier.fit(train, labels)
    predictions = classifier.predict(test)
    probabilities = classifier.predict_proba(test)
    elapsed = time.perf_counter() - started

    result = {
        "model": classifier_name,
        "model_version": args.model_version if args.model == "tabpfn" else "1.0.0-pytorch",
        "device": args.device,
        "features": FEATURES,
        "train_rows": len(train),
        "test_rows": test.to_dict(orient="records"),
        "predictions": predictions.tolist(),
        "probabilities": probabilities.round(6).tolist(),
        "elapsed_sec": round(elapsed, 3),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
