"""Evaluate the existing read-only RAG MCP and local answer model on M2 labels.

The committed fixture deliberately contains synthetic labels only.  A real run
requires a separately approved, local label-to-source-label mapping; it is never
written to the report or to version control.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


REFUSAL_MARKERS = ("无法", "不足", "未提供", "没有提供", "没有说明", "不确定")
VALID_CATEGORIES = {"answerable", "unanswerable", "boundary", "conflicting"}


def source_label(item: dict[str, Any]) -> str:
    """Return the stable source label exposed by the RAGService result schema."""
    metadata = item.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    # RAGService returns metadata.source at both the top level and in metadata.
    for value in (item.get("source"), metadata.get("source")):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def source_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def has_refusal(answer: str) -> bool:
    return any(marker in answer for marker in REFUSAL_MARKERS)


def validate_cases(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    cases = dataset.get("cases")
    if dataset.get("classification") != "sanitized-bootstrap" or not isinstance(cases, list):
        raise ValueError("Expected a sanitized bootstrap M2 fixture")
    if len(cases) != 20 or {case.get("category") for case in cases} != VALID_CATEGORIES:
        raise ValueError("Expected exactly 20 cases covering all four M2 categories")
    identifiers: set[str] = set()
    for case in cases:
        labels = case.get("expected_source_labels")
        if not isinstance(case.get("id"), str) or not isinstance(case.get("question"), str):
            raise ValueError("Every case requires string id and question fields")
        if not isinstance(labels, list) or not all(isinstance(label, str) and label for label in labels):
            raise ValueError("expected_source_labels must be a list of non-empty synthetic labels")
        if case["category"] == "unanswerable" and labels:
            raise ValueError("Unanswerable cases must not have expected document labels")
        if case["category"] != "unanswerable" and not labels:
            raise ValueError("Answerable cases require expected document labels")
        identifiers.update(labels)
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("M2 case ids must be unique")
    return cases


def load_approved_source_map(path: Path, cases: list[dict[str, Any]]) -> dict[str, str]:
    """Load an external approved mapping without putting source labels in reports."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    mapping = payload.get("source_labels") if isinstance(payload, dict) else None
    if payload.get("approved") is not True or not isinstance(mapping, dict):
        raise ValueError("Source map must contain approved: true and a source_labels object")
    required = {label for case in cases for label in case["expected_source_labels"]}
    if set(mapping) != required:
        raise ValueError("Source map must contain exactly the fixture's synthetic source labels")
    if not all(isinstance(value, str) and value.strip() for value in mapping.values()):
        raise ValueError("Every approved source label must be a non-empty string")
    return {label: value.strip() for label, value in mapping.items()}


def score_case(case: dict[str, Any], expected_ids: set[str], retrieved_ids: list[str], answer: str) -> dict[str, bool | None]:
    answerable = case["category"] != "unanswerable"
    retrieval_hit = bool(set(retrieved_ids[:5]) & expected_ids) if answerable else None
    cited_hit = any(f"[source: {identifier}]" in answer for identifier in expected_ids) if answerable else None
    keyword_hit = all(keyword.lower() in answer.lower() for keyword in case["required_keywords"])
    refusal = has_refusal(answer)
    # This is deterministic evidence adherence, not a substitute for human answer-quality review.
    adherence = refusal if not answerable else bool(cited_hit and keyword_hit and not refusal)
    return {
        "retrieval_hit": retrieval_hit,
        "source_hit": cited_hit,
        "refusal": refusal,
        "answer_adherent": adherence,
    }


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    return values[round((len(values) - 1) * fraction)]


def aggregate(records: list[dict[str, Any]]) -> dict[str, float]:
    answerable = [record for record in records if record["answerable"]]
    unanswerable = [record for record in records if not record["answerable"]]

    def rate(items: list[dict[str, Any]], key: str) -> float:
        return round(sum(bool(item[key]) for item in items) / len(items), 4) if items else 0.0

    latencies = [record["latency_sec"] for record in records]
    return {
        "recall_at_5": rate(answerable, "retrieval_hit"),
        "source_hit_rate": rate(answerable, "source_hit"),
        "refusal_rate": rate(unanswerable, "refusal"),
        "answer_adherence_rate": rate(records, "answer_adherent"),
        "latency_mean_sec": round(statistics.mean(latencies), 3) if latencies else 0.0,
        "latency_p50_sec": round(percentile(latencies, 0.5), 3),
        "latency_p95_sec": round(percentile(latencies, 0.95), 3),
    }


def tool_payload(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    content = getattr(result, "content", [])
    for item in content:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            payload = json.loads(text)
            if isinstance(payload, dict):
                return payload
    raise ValueError("knowledge_search returned no JSON object")


async def search(session: ClientSession, question: str) -> list[dict[str, Any]]:
    result = await session.call_tool("knowledge_search", {"query": question, "top_k": 5, "max_results": 5})
    payload = tool_payload(result)
    results = payload.get("results")
    if payload.get("status") != "success" or not isinstance(results, list) or not all(isinstance(item, dict) for item in results):
        raise ValueError("knowledge_search returned an invalid RAGService payload")
    return results


def answer(base_url: str, model: str, question: str, evidence: list[dict[str, Any]], timeout: int) -> str:
    safe_evidence = [{"source": source_label(item), "content": str(item.get("content", ""))} for item in evidence]
    prompt = (
        "Answer only from evidence. Cite every conclusion as [source: SOURCE_ID]. "
        "If evidence is insufficient, say so explicitly. If sources conflict, state the conflict and request confirmation.\n"
        f"Evidence: {json.dumps(safe_evidence, ensure_ascii=False)}\nQuestion: {question}"
    )
    payload = {"model": model, "temperature": 0, "max_tokens": 512, "messages": [{"role": "user", "content": prompt}]}
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local-dev"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"].get("content")
    if not isinstance(content, str):
        raise ValueError("Model response did not contain text content")
    return content


async def run(args: argparse.Namespace, cases: list[dict[str, Any]], source_map: dict[str, str]) -> list[dict[str, Any]]:
    server = StdioServerParameters(command="bash", args=["scripts/start_mcp_server.sh"], env=os.environ.copy())
    records: list[dict[str, Any]] = []
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for case in cases:
                started = time.perf_counter()
                evidence = await search(session, case["question"])
                result = answer(args.base_url, args.model, case["question"], evidence, args.timeout)
                expected_ids = {source_map[label] for label in case["expected_source_labels"]}
                scores = score_case(case, expected_ids, [source_label(item) for item in evidence], result)
                records.append({
                    "case_id": case["id"], "category": case["category"],
                    "answerable": case["category"] != "unanswerable",
                    "latency_sec": round(time.perf_counter() - started, 3), **scores,
                    "retrieved_source_hashes": [source_hash(source_label(item)) for item in evidence if source_label(item)],
                    "answer_sha256": hashlib.sha256(result.encode("utf-8")).hexdigest(),
                })
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("tests/fixtures/m2_eval_cases_v1.json"))
    parser.add_argument("--source-map", type=Path, help="Local approved synthetic-label-to-stable-source-label map; never committed or reported")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8004/v1")
    parser.add_argument("--model", default="Qwen3-14B-Q4_K_M.gguf")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases = validate_cases(json.loads(args.cases.read_text(encoding="utf-8")))
    if args.dry_run:
        print(json.dumps({"cases": len(cases), "fixture_valid": True, "requires_approved_source_map": True}))
        return
    if args.source_map is None or args.output_dir is None:
        raise SystemExit("--source-map and --output-dir are required for a real evaluation")
    if not os.getenv("PGDATABASE_URL"):
        raise SystemExit("PGDATABASE_URL must be exported; it is never read or logged by this script")
    source_map = load_approved_source_map(args.source_map, cases)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    records = asyncio.run(run(args, cases, source_map))
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sanitized": True,
        "metric_definitions": {
            "recall_at_5": "share of answerable cases with an expected approved source in the first five results",
            "source_hit_rate": "share of answerable cases citing an expected approved source",
            "refusal_rate": "share of unanswerable cases containing a refusal marker",
            "answer_adherence_rate": "deterministic citation/keyword/refusal check; human review is still required for answer quality",
        },
        "metrics": aggregate(records), "records": records,
    }
    (args.output_dir / "m2_eval_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
