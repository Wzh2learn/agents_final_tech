"""Download a model entry declared in models/model_catalog.json."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / "models" / "model_catalog.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a cataloged model from Hugging Face.")
    parser.add_argument("model_key", help="Key in models/model_catalog.json, e.g. qwen3-8b-gguf.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="Catalog JSON path.")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("HF_ENDPOINT", "https://hf-mirror.com"),
        help="Hugging Face endpoint, defaulting to HF_ENDPOINT or https://hf-mirror.com.",
    )
    parser.add_argument("--revision", default="main", help="Repository revision.")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved download plan only.")
    return parser.parse_args()


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_target(storage_root: str, target: str) -> Path:
    return (Path(storage_root).expanduser() / target).resolve()


def main() -> None:
    args = parse_args()
    catalog = load_catalog(args.catalog)
    models = catalog.get("models", {})

    if args.model_key not in models:
        available = ", ".join(sorted(models))
        raise SystemExit(f"Unknown model key: {args.model_key}\nAvailable: {available}")

    entry = models[args.model_key]
    repo_id = entry["repo_id"]
    allow_patterns = entry.get("include")
    target = resolve_target(catalog.get("storage_root", "~/wzh/models"), entry["target"])

    print(f"model_key: {args.model_key}")
    print(f"repo_id: {repo_id}")
    print(f"endpoint: {args.endpoint}")
    print(f"target: {target}")
    print(f"include: {allow_patterns}")

    if args.dry_run:
        return

    target.mkdir(parents=True, exist_ok=True)
    os.environ["HF_ENDPOINT"] = args.endpoint
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

    result = snapshot_download(
        repo_id=repo_id,
        revision=args.revision,
        local_dir=target,
        allow_patterns=allow_patterns,
    )
    print(f"Downloaded {repo_id} to {result}")


if __name__ == "__main__":
    main()
