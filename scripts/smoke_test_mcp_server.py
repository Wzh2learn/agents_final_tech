"""Protocol-level smoke test for the local JinRongAgents MCP server."""

from __future__ import annotations

import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run() -> None:
    """Start the stdio server, discover tools, and call the collection tool."""
    server = StdioServerParameters(
        command="bash",
        args=["scripts/start_mcp_server.sh"],
        env=os.environ.copy(),
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            expected = {
                "knowledge_search",
                "knowledge_list_collections",
                "knowledge_get_source",
            }
            missing = expected.difference(tool_names)
            if missing:
                raise RuntimeError(f"Missing MCP tools: {sorted(missing)}")

            result = await session.call_tool(
                "knowledge_list_collections",
                arguments={},
            )
            print(json.dumps({
                "tools": tool_names,
                "collection_result": [
                    item.model_dump(mode="json") for item in result.content
                ],
                "is_error": result.isError,
            }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(run())
