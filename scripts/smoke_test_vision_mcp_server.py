"""Protocol smoke test for the local JinRongAgents Vision MCP server."""

from __future__ import annotations

import argparse
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def parse_args() -> argparse.Namespace:
    """Accept an optional image for an explicit, real inference request."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "image", nargs="?", help="Allowed image path; omitted means discovery only."
    )
    parser.add_argument(
        "--model",
        default="paddleocr",
        choices=("paddleocr", "minicpm", "qwen3-vl"),
    )
    parser.add_argument("--max-new-tokens", type=int, default=256)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    """Start the stdio server, verify discovery, and optionally invoke the tool."""
    server = StdioServerParameters(
        command="bash",
        args=["scripts/start_vision_mcp_server.sh"],
        env=os.environ.copy(),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]
            if "vision_ocr_extract" not in names:
                raise RuntimeError("Missing MCP tool: vision_ocr_extract")
            summary: dict[str, object] = {"tools": names, "mode": "discovery"}
            if args.image:
                result = await session.call_tool(
                    "vision_ocr_extract",
                    arguments={
                        "image_path": args.image,
                        "model": args.model,
                        "max_new_tokens": args.max_new_tokens,
                    },
                )
                summary["mode"] = "inference"
                summary["is_error"] = result.isError
                summary["content_types"] = [item.type for item in result.content]
            print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
