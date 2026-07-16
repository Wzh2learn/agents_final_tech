"""Check whether a local vision-language model exposes config and processor APIs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse a local Hugging Face vision-language model directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    """Load configuration and processor without allocating model weights on the GPU."""
    args = parse_args()
    if not args.model_path.is_dir():
        raise SystemExit(f"Model directory does not exist: {args.model_path}")

    from transformers import AutoConfig, AutoProcessor

    config = AutoConfig.from_pretrained(str(args.model_path), trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(str(args.model_path), trust_remote_code=True)
    result: dict[str, Any] = {
        "model_path": str(args.model_path),
        "model_type": config.model_type,
        "architecture": config.architectures,
        "processor_class": processor.__class__.__name__,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
