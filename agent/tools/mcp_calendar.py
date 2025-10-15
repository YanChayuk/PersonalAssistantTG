import logging
from ..mcp_client import MCPClient

logger = logging.getLogger(__name__)


class MCPCalendarTool:
    def __init__(self, mcp: MCPClient):
        self.mcp = mcp

    async def add_event(self, iso_dt: str, duration_minutes: int, title: str) -> str:
        if not self.mcp.is_configured():
            return '[MCP calendar mock] Сервис не настроен.'
        payload = {"iso": iso_dt, "duration": duration_minutes, "title": title}
        return await self.mcp.call(self.mcp.calendar_server, "calendar.add", payload)

    async def list_events(self, days: int = 7) -> str:
        if not self.mcp.is_configured():
            return '[MCP calendar mock] Сервис не настроен.'
        payload = {"days": days}
        return await self.mcp.call(self.mcp.calendar_server, "calendar.list", payload)


