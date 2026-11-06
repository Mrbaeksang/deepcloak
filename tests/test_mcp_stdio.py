"""Starts the real MCP server over stdio. Needs the optional `mcp` dependency."""

import asyncio
import sys

import pytest

pytest.importorskip("mcp")


def test_stdio_server_lists_research_tools():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def list_tool_names():
        params = StdioServerParameters(
            command=sys.executable, args=["-c", "from deepcloak.mcp_server import serve; serve()"]
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return sorted(tool.name for tool in result.tools)

    assert asyncio.run(asyncio.wait_for(list_tool_names(), timeout=60)) == [
        "deep_research",
        "get_evidence",
        "list_models",
        "quick_summary",
    ]
