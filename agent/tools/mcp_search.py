import logging
from ..mcp_client import MCPClient

logger = logging.getLogger(__name__)


class MCPSearchTool:
    def __init__(self, mcp: MCPClient):
        self.mcp = mcp

    async def search(self, query: str) -> str:
        if not self.mcp.is_configured():
            return f"[MCP search mock] Что искать: {query} — настройте MCP."
        return await self.mcp.call(self.mcp.search_server, "search", {"q": query})


