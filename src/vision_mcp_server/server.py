"""FastMCP stdio server for isolated, read-only local OCR inference."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from vision_mcp_server.service import run_vision_ocr


mcp = FastMCP(
    "JinRongAgents Vision",
    instructions=(
        "Use vision_ocr_extract only for approved local image files. "
        "The tool is read-only and does not accept model paths."
    ),
)


@mcp.tool(name="vision_ocr_extract")
def vision_ocr_extract(
    image_path: str, model: str = "paddleocr", max_new_tokens: int = 256
) -> dict[str, Any]:
    """Extract text from an allowed local image using a fixed server-side model mapping."""
    return run_vision_ocr(image_path, model, max_new_tokens)


def main() -> None:
    """Run the local stdio MCP server without importing vision model dependencies."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
