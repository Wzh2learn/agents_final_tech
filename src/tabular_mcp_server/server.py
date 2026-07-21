"""FastMCP stdio server for isolated, read-only tabular inference."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tabular_mcp_server.service import run_tabular_classify


mcp = FastMCP(
    "JinRongAgents Tabular",
    instructions=(
        "Use tabular_classify only for small in-memory numeric classification data. "
        "The tool is read-only and does not accept files, paths, or model identifiers."
    ),
)


@mcp.tool(name="tabular_classify")
def tabular_classify(
    feature_names: list[str],
    train_rows: list[list[float]],
    labels: list[float],
    predict_rows: list[list[float]],
    model: str = "tabpfn",
    model_version: str = "v2",
) -> dict[str, Any]:
    """Classify bounded numeric rows through a server-selected tabular model."""
    return run_tabular_classify(
        feature_names, train_rows, labels, predict_rows, model, model_version
    )


def main() -> None:
    """Run stdio MCP without importing tabpfn or tabfm in this interpreter."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
