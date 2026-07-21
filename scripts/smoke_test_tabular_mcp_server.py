"""Protocol smoke test for the local JinRongAgents Tabular MCP server."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SYNTHETIC_REQUEST: dict[str, Any] = {
    "feature_names": ["age", "debt_ratio", "consecutive_overdue_months"],
    "train_rows": [
        [25, 0.35, 0], [42, 0.55, 1], [58, 0.62, 2], [31, 0.48, 0],
        [19, 0.30, 0], [63, 0.40, 0], [45, 0.75, 1], [36, 0.50, 3],
    ],
    "labels": [1, 1, 1, 1, 0, 0, 0, 0],
    "predict_rows": [[30, 0.45, 0], [65, 0.45, 0], [40, 0.80, 3]],
}


def parse_args() -> argparse.Namespace:
    """Keep the default protocol-only; opt in explicitly to model inference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-synthetic", action="store_true")
    parser.add_argument("--model", choices=("tabpfn", "tabfm"), default="tabpfn")
    return parser.parse_args()


def _tool_payload(result: Any) -> dict[str, Any]:
    if result.isError or not result.content:
        raise RuntimeError("MCP tabular call failed")
    text = getattr(result.content[0], "text", None)
    payload = json.loads(text)
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise RuntimeError("MCP tabular call returned an invalid response")
    return payload


async def run(args: argparse.Namespace) -> None:
    """Verify discovery and optionally run the fixed desensitized chain."""
    server = StdioServerParameters(
        command="bash",
        args=["scripts/start_tabular_mcp_server.sh"],
        env=os.environ.copy(),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            if names != ["tabular_classify"]:
                raise RuntimeError("Expected only MCP tool: tabular_classify")
            summary: dict[str, Any] = {"status": "pass", "mode": "discovery", "tools": names}
            if args.run_synthetic:
                request = dict(SYNTHETIC_REQUEST)
                request["model"] = args.model
                payload = _tool_payload(await session.call_tool("tabular_classify", arguments=request))
                probabilities = payload["probabilities"]
                summary = {
                    "status": "pass",
                    "mode": "synthetic",
                    "model": payload["model_key"],
                    "train_count": payload["train_count"],
                    "predict_count": payload["predict_count"],
                    "elapsed_sec": payload["elapsed_sec"],
                    "output_dimensions": [len(payload["predictions"]), len(probabilities[0])],
                }
            print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    arguments = parse_args()
    try:
        asyncio.run(run(arguments))
    except Exception:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "mode": "synthetic" if arguments.run_synthetic else "discovery",
                    "model": arguments.model if arguments.run_synthetic else None,
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)
