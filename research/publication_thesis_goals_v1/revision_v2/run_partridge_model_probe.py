"""Generate one bounded natural model candidate for the Partridge migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_json(url: str, timeout: int = 10) -> Any:
    request = urllib.request.Request(url, headers={"accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, Any], timeout: int) -> tuple[dict[str, Any], bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"accept": "application/json", "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8")), raw


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-module", type=Path, required=True)
    parser.add_argument("--parent-setup", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--models-endpoint", default="http://127.0.0.1:8004/v1/models")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8004/v1/chat/completions")
    parser.add_argument("--model", default="Qwen3.6-35B-A3B-Q4_K_M.gguf")
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if (output_dir / "COMPLETE").exists():
        raise RuntimeError("probe_already_complete")

    identity = get_json(args.models_endpoint)
    models = [row.get("id") or row.get("name") for row in identity.get("data", [])]
    if args.model not in models:
        raise RuntimeError(f"model_identity_mismatch:{models}")

    parent_module = args.parent_module.read_text(encoding="utf-8")
    parent_setup = args.parent_setup.read_text(encoding="utf-8")
    prompt = f"""+Complete one dependency migration while preserving observable behavior.

Task:
- Replace the chardet dependency with cchardet.
- Update the complete partridge utilities module and setup requirements.
- Preserve existing behavior and do not remove unrelated helpers or module state.
- Return only one JSON object with exactly two string fields: module_code and setup_code.
- module_code must be the complete partridge/utilities.py file.
- setup_code must be the complete setup.py file.

Current partridge/utilities.py:
```python
{parent_module}
```

Current setup.py:
```python
{parent_setup}
```
"""
    request = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": args.max_tokens,
        "response_format": {"type": "json_object"},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request_path = output_dir / "request.json"
    write_json(
        request_path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "request": request,
            "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
            "parent_module_sha256": sha256_bytes(parent_module.encode("utf-8")),
            "parent_setup_sha256": sha256_bytes(parent_setup.encode("utf-8")),
            "retry_cap": 0,
            "concurrency": 1,
        },
    )
    started = time.perf_counter()
    body, raw = post_json(args.endpoint, request, timeout=240)
    latency = round(time.perf_counter() - started, 6)
    (output_dir / "response.json").write_bytes(raw)
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("response_choices_missing")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise RuntimeError("response_content_missing")
    parsed = json.loads(content)
    module_code = parsed.get("module_code")
    setup_code = parsed.get("setup_code")
    if not isinstance(module_code, str) or not isinstance(setup_code, str):
        raise RuntimeError("candidate_fields_invalid")
    (output_dir / "candidate_utilities.py").write_text(module_code, encoding="utf-8")
    (output_dir / "candidate_setup.py").write_text(setup_code, encoding="utf-8")
    usage = body.get("usage", {})
    receipt = {
        "schema": "partridge_natural_model_probe_v1",
        "status": "COMPLETE",
        "evidence_identity": "ONE_NATURAL_MODEL_OUTPUT_NOT_HUMAN_GOLD",
        "model_observed": body.get("model"),
        "model_expected": args.model,
        "latency_seconds": latency,
        "usage": usage,
        "request_sha256": sha256_bytes(request_path.read_bytes()),
        "response_sha256": sha256_bytes(raw),
        "candidate_module_sha256": sha256_bytes(module_code.encode("utf-8")),
        "candidate_setup_sha256": sha256_bytes(setup_code.encode("utf-8")),
        "accounting_attempts": 1,
        "physical_http_calls": 1,
        "accounting_tokens": int(usage.get("total_tokens", args.max_tokens)),
        "retry_count": 0,
    }
    write_json(output_dir / "receipt.json", receipt)
    (output_dir / "COMPLETE").write_text("COMPLETE\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
