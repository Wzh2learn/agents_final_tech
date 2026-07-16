"""Download selected Hugging Face model files through a configurable mirror."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from huggingface_hub import snapshot_download


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download model files from Hugging Face or an HF-compatible mirror."
    )
    parser.add_argument("repo_id", help="Hugging Face repository, for example Qwen/Qwen3-4B-GGUF")
    parser.add_argument(
        "--include",
        action="append",
        dest="allow_patterns",
        help="File glob to download; repeat for multiple patterns.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Local model directory.",
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("HF_ENDPOINT", "https://hf-mirror.com"),
        help="Hugging Face endpoint (default: HF_ENDPOINT or https://hf-mirror.com).",
    )
    parser.add_argument("--revision", default="main", help="Repository revision.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = args.target.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    os.environ["HF_ENDPOINT"] = args.endpoint
    result = snapshot_download(
        repo_id=args.repo_id,
        revision=args.revision,
        local_dir=target,
        allow_patterns=args.allow_patterns,
    )
    print(f"Downloaded {args.repo_id} to {result}")


if __name__ == "__main__":
    main()
