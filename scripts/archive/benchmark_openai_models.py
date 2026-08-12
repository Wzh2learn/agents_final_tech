"""Run a small M1/M2 baseline set against OpenAI-compatible model services."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    """Parse command line options for a repeatable local-model benchmark."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/m1_m2_baseline_cases.json"),
        help="Path to the JSON baseline case set.",
    )
    parser.add_argument(
        "--target",
        action="append",
        required=True,
        metavar="NAME|BASE_URL|MODEL",
        help="Repeat for each model, e.g. qwen3-4b|http://127.0.0.1:8002/v1|Qwen3-4B-Q4_K_M.gguf",
    )
    parser.add_argument("--output-dir", type=Path, help="Directory for JSONL, CSV, and run metadata.")
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--disable-thinking", action="store_true")
    return parser.parse_args()


def parse_target(value: str) -> dict[str, str]:
    """Parse one target declaration into a named OpenAI-compatible endpoint."""
    parts = value.split("|", maxsplit=2)
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"Invalid --target: {value!r}. Expected NAME|BASE_URL|MODEL.")
    return {"name": parts[0], "base_url": parts[1].rstrip("/"), "model": parts[2]}


def post_json(url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    """Send a JSON request to a local OpenAI-compatible endpoint."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local-dev"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def unwrap_json(content: str) -> Any:
    """Parse raw JSON or JSON placed inside a Markdown code fence."""
    candidate = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    return json.loads(candidate)


def validate(content: str, validator: dict[str, Any]) -> tuple[bool, str]:
    """Apply the case's lightweight automatic validation rule."""
    validator_type = validator["type"]
    if validator_type == "json_fields":
        try:
            parsed = unwrap_json(content)
        except json.JSONDecodeError as exc:
            return False, f"invalid_json: {exc.msg}"
        if not isinstance(parsed, dict):
            return False, "json_not_object"
        missing = [field for field in validator["required_fields"] if field not in parsed]
        return (not missing, "ok" if not missing else f"missing_fields: {','.join(missing)}")

    normalized = content.lower()
    keywords = [item.lower() for item in validator["required_keywords"]]
    matched = [item for item in keywords if item in normalized]
    if validator_type == "keywords":
        return (len(matched) == len(keywords), f"matched: {','.join(matched)}")
    if validator_type == "keywords_any":
        return (bool(matched), f"matched: {','.join(matched)}")
    raise ValueError(f"Unsupported validator type: {validator_type}")


def run_case(target: dict[str, str], case: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Run and record one case for one model target."""
    payload: dict[str, Any] = {
        "model": target["model"],
        "messages": case["messages"],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}

    record: dict[str, Any] = {
        "target": target["name"],
        "model": target["model"],
        "base_url": target["base_url"],
        "case_id": case["id"],
        "task": case["task"],
        "passed": False,
    }
    started = time.perf_counter()
    try:
        response = post_json(f"{target['base_url']}/chat/completions", payload, args.timeout)
        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        passed, validation = validate(content, case["validator"])
        record.update(
            elapsed_sec=round(time.perf_counter() - started, 3),
            passed=passed,
            validation=validation,
            finish_reason=choice.get("finish_reason"),
            usage=response.get("usage", {}),
            content=content,
            reasoning_content=message.get("reasoning_content"),
        )
    except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        record.update(elapsed_sec=round(time.perf_counter() - started, 3), validation=f"request_error: {exc}")
    return record


def write_summary(records: list[dict[str, Any]], output_dir: Path) -> None:
    """Write a compact, spreadsheet-friendly summary for every model and case."""
    fields = ["target", "model", "case_id", "task", "passed", "elapsed_sec", "finish_reason", "validation"]
    with (output_dir / "summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def main() -> None:
    """Execute the selected cases and persist raw and summarized results."""
    args = parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    targets = [parse_target(value) for value in args.target]
    output_dir = args.output_dir or Path("docs/experiments/results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=False)

    records = [run_case(target, case, args) for target in targets for case in cases]
    with (output_dir / "raw_results.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    write_summary(records, output_dir)

    passed_count = sum(bool(record["passed"]) for record in records)
    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "cases": str(args.cases),
        "targets": targets,
        "total": len(records),
        "passed": passed_count,
        "pass_rate": round(passed_count / len(records), 4) if records else 0.0,
    }
    (output_dir / "run_meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**metadata, "output_dir": str(output_dir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
