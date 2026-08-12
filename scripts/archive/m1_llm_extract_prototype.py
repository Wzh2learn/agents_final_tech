#!/usr/bin/env python3
"""M1 LLM-based structured extraction prototype on TAT-DQA dev split.

Zero-shot structured extraction with the local Qwen3-14B chat-completions
service (http://127.0.0.1:8004). Reads the first N dev documents' parsed text
blocks from ``tatdqa_docs_dev.zip`` *in memory* (no extraction to disk), asks
the LLM to return a JSON object of financial fields, and records parse success,
field counts, latency, and token usage.

Constraints honoured by design:
- dev(validation) split only; test / test_gold never opened.
- No model download; uses the already-running local service.
- No changes to ``src/biz/m1_service.py`` (standalone prototype).
- 60s timeout per LLM call; 30-minute total wall-clock budget.
- Stops after 3 consecutive call timeouts.

Stdlib-only so it runs under the system interpreter without venv activation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_DATA_ROOT = Path("/home/testuser/wzh/datasets/tat-dqa")
DEFAULT_LLM_URL = "http://127.0.0.1:8004/v1/chat/completions"
DEFAULT_MODEL = "Qwen3-14B-Q4_K_M.gguf"
CALL_TIMEOUT_S = 60.0
TOTAL_BUDGET_S = 30 * 60.0
MAX_CONSECUTIVE_TIMEOUTS = 3
TEXT_CHAR_LIMIT = 3000
# Qwen3-14B on this llama-server defaults to thinking mode: it spends the whole
# completion budget on reasoning_content and leaves content empty. The /no_think
# switch in the user message disables thinking so the JSON answer is emitted
# directly (verified: 1024-token empty reasoning -> 6-token direct answer).
NO_THINK_PREFIX = "/no_think\n"

PROMPT_TEMPLATE = """You are a financial document analyst. Extract structured information from the following text.
Return a JSON object with these fields:
- company_name: string
- reporting_period: string
- key_metrics: array of {{name, value, unit}}
- risk_factors: array of strings (max 3)
- accounting_changes: array of strings (empty if none)

If a field cannot be determined, use null. Return ONLY valid JSON, no explanation.

Document text (truncated to 3000 chars):
{text}"""


def load_dev_docs(data_root: Path, limit: int) -> list[dict]:
    """Return the first ``limit`` dev records: {uid, source, text}."""
    dev_json = data_root / "raw" / "tatdqa_dataset_dev.json"
    docs_zip = data_root / "raw" / "tatdqa_docs_dev.zip"
    records = json.loads(dev_json.read_text(encoding="utf-8"))
    archive = zipfile.ZipFile(docs_zip)
    out: list[dict] = []
    for record in records[:limit]:
        doc = record["doc"]
        uid = doc["uid"]
        source = doc.get("source", "")
        text = extract_text_from_zip(archive, uid)
        out.append({"uid": uid, "source": source, "text": text})
    return out


def extract_text_from_zip(archive: zipfile.ZipFile, uid: str) -> str:
    """Read ``dev/{uid}.json`` in memory and join non-empty block texts in order."""
    try:
        parsed = json.loads(archive.read(f"dev/{uid}.json"))
    except KeyError:
        return ""
    blocks: list[tuple[int, str]] = []
    for page in parsed.get("pages", []):
        for block in page.get("blocks", []):
            text = (block.get("text") or "").strip()
            if text:
                blocks.append((int(block.get("order", 0)), text))
    blocks.sort(key=lambda item: item[0])
    return "\n".join(text for _, text in blocks)


def build_prompt(text: str) -> str:
    return PROMPT_TEMPLATE.format(text=text[:TEXT_CHAR_LIMIT])


def call_llm(url: str, model: str, prompt: str) -> dict:
    """Call chat completions. Returns {ok, content, latency_s, prompt_tokens,
    completion_tokens, total_tokens, error, error_type}."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": NO_THINK_PREFIX + prompt}],
        "temperature": 0,
        "max_tokens": 1024,
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=CALL_TIMEOUT_S) as response:
            body = json.loads(response.read().decode("utf-8"))
        latency = time.monotonic() - started
        choice = body["choices"][0]
        content = choice.get("message", {}).get("content", "")
        usage = body.get("usage", {}) or {}
        return {
            "ok": True,
            "content": content,
            "latency_s": round(latency, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "error": None,
            "error_type": None,
        }
    except urllib.error.HTTPError as exc:
        return _failure(started, f"HTTP {exc.code}: {exc.reason}", "http_error")
    except TimeoutError as exc:
        return _failure(started, str(exc) or "timeout", "timeout")
    except Exception as exc:  # noqa: BLE001 - prototype records any failure
        error_type = "timeout" if "timed out" in str(exc).lower() else "error"
        return _failure(started, str(exc), error_type)


def _failure(started: float, message: str, error_type: str) -> dict:
    return {
        "ok": False,
        "content": "",
        "latency_s": round(time.monotonic() - started, 2),
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "error": message,
        "error_type": error_type,
    }


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def parse_json(content: str) -> tuple[object | None, str]:
    """Parse LLM output into a JSON object. Returns (obj, method)."""
    stripped = content.strip()
    try:
        return json.loads(stripped), "direct"
    except json.JSONDecodeError:
        pass
    fence = _FENCE_RE.search(stripped)
    if fence:
        try:
            return json.loads(fence.group(1).strip()), "fence"
        except json.JSONDecodeError:
            pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(stripped[start : end + 1]), "brace_slice"
        except json.JSONDecodeError:
            pass
    return None, "failed"


def company_from_source(source: str) -> str:
    """'quicklogic-corporation_2019.pdf' -> 'quicklogic corporation'."""
    stem = source.rsplit(".", 1)[0]
    stem = re.sub(r"_\d{4}$", "", stem)
    return stem.replace("-", " ").replace("_", " ").strip().lower()


def company_matches(extracted: object, source: str) -> bool:
    """Fuzzy containment: do the filename company tokens appear in extracted name?"""
    if not isinstance(extracted, str) or not extracted.strip():
        return False
    expected_tokens = [t for t in company_from_source(source).split() if t]
    haystack = extracted.lower()
    if not expected_tokens:
        return False
    hits = sum(1 for token in expected_tokens if token in haystack)
    return hits >= max(1, len(expected_tokens) // 2 + (1 if len(expected_tokens) == 1 else 0))


def count_metrics(parsed: object) -> int:
    if isinstance(parsed, dict):
        metrics = parsed.get("key_metrics")
        if isinstance(metrics, list):
            return len(metrics)
    return 0


def count_risks(parsed: object) -> int:
    if isinstance(parsed, dict):
        risks = parsed.get("risk_factors")
        if isinstance(risks, list):
            return len(risks)
    return 0


def run(args: argparse.Namespace) -> dict:
    docs = load_dev_docs(Path(args.data_root), args.limit)
    results: list[dict] = []
    consecutive_timeouts = 0
    overall_start = time.monotonic()
    stopped_reason = "completed"

    for index, doc in enumerate(docs):
        elapsed = time.monotonic() - overall_start
        if elapsed > TOTAL_BUDGET_S:
            stopped_reason = "total_budget_exceeded"
            print(f"[stop] total budget exceeded after {elapsed:.0f}s", file=sys.stderr)
            break

        prompt = build_prompt(doc["text"])
        print(
            f"[{index + 1}/{len(docs)}] uid={doc['uid'][:12]} source={doc['source']} "
            f"chars={len(doc['text'])}",
            file=sys.stderr,
        )
        call = call_llm(args.url, args.model, prompt)

        if call["ok"]:
            parsed, method = parse_json(call["content"])
            json_ok = parsed is not None
            consecutive_timeouts = 0
        else:
            parsed, method, json_ok = None, "failed", False
            if call["error_type"] == "timeout":
                consecutive_timeouts += 1
            print(
                f"    call failed ({call['error_type']}): {call['error']}",
                file=sys.stderr,
            )

        result = {
            "uid": doc["uid"],
            "source": doc["source"],
            "company_from_filename": company_from_source(doc["source"]),
            "doc_chars": len(doc["text"]),
            "call_ok": call["ok"],
            "error": call["error"],
            "json_ok": json_ok,
            "json_method": method,
            "company_name": parsed.get("company_name") if isinstance(parsed, dict) else None,
            "company_match": company_matches(
                parsed.get("company_name") if isinstance(parsed, dict) else None, doc["source"]
            ),
            "reporting_period": parsed.get("reporting_period") if isinstance(parsed, dict) else None,
            "num_metrics": count_metrics(parsed),
            "num_risks": count_risks(parsed),
            "latency_s": call["latency_s"],
            "prompt_tokens": call["prompt_tokens"],
            "completion_tokens": call["completion_tokens"],
            "total_tokens": call["total_tokens"],
            "parsed": parsed,
            "raw_content": call["content"],
        }
        results.append(result)
        print(
            f"    json_ok={json_ok} method={method} metrics={result['num_metrics']} "
            f"risks={result['num_risks']} latency={call['latency_s']}s "
            f"tokens={call['total_tokens']}",
            file=sys.stderr,
        )

        if consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
            stopped_reason = "consecutive_timeouts"
            print(
                f"[stop] {MAX_CONSECUTIVE_TIMEOUTS} consecutive timeouts",
                file=sys.stderr,
            )
            break

    total_latency = round(sum(r["latency_s"] for r in results), 2)
    total_tokens = sum(r["total_tokens"] or 0 for r in results)
    summary = {
        "model": args.model,
        "url": args.url,
        "num_docs_requested": args.limit,
        "num_docs_processed": len(results),
        "stopped_reason": stopped_reason,
        "json_success": sum(1 for r in results if r["json_ok"]),
        "company_match": sum(1 for r in results if r["company_match"]),
        "docs_with_metrics": sum(1 for r in results if r["num_metrics"] > 0),
        "total_latency_s": total_latency,
        "avg_latency_s": round(total_latency / len(results), 2) if results else None,
        "total_tokens": total_tokens,
        "wall_clock_s": round(time.monotonic() - overall_start, 2),
        "results": results,
    }
    return summary


def print_table(summary: dict) -> None:
    print("\n=== RESULTS TABLE ===")
    header = (
        f"{'doc':12} {'company(filename)':34} {'json':5} {'match':5} "
        f"{'metrics':7} {'risks':5} {'latency':8} {'tokens':7}"
    )
    print(header)
    print("-" * len(header))
    for r in summary["results"]:
        print(
            f"{r['uid'][:12]:12} {r['company_from_filename'][:34]:34} "
            f"{str(r['json_ok']):5} {str(r['company_match']):5} "
            f"{r['num_metrics']:<7} {r['num_risks']:<5} "
            f"{r['latency_s']:<8} {str(r['total_tokens']):7}"
        )
    print("\n=== SUMMARY ===")
    for key in (
        "num_docs_processed",
        "stopped_reason",
        "json_success",
        "company_match",
        "docs_with_metrics",
        "total_latency_s",
        "avg_latency_s",
        "total_tokens",
        "wall_clock_s",
    ):
        print(f"{key}: {summary[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    parser.add_argument("--url", default=DEFAULT_LLM_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--out", default="/tmp/m1_llm_results.json")
    args = parser.parse_args()

    summary = run(args)
    print_table(summary)
    Path(args.out).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\n[written] full results -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
