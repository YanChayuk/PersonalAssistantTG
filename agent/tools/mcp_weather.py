import logging
from ..mcp_client import MCPClient

logger = logging.getLogger(__name__)


class MCPWeatherTool:
    def __init__(self, mcp: MCPClient):
        self.mcp = mcp

    async def get_weather(self, city: str) -> str:
        if not self.mcp.is_configured():
            return f"[MCP weather mock] Погода для {city}: настройте MCP."
        return await self.mcp.call(self.mcp.weather_server, "weather", {"city": city})


