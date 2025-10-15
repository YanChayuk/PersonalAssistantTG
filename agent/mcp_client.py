import os
import asyncio
import logging
import requests

logger = logging.getLogger(__name__)


class MCPClient:
    """Тонкая обёртка над MCP-клиентом.

    В проде ожидается наличие Python-библиотеки MCP и адресов серверов.
    Если окружение не настроено или библиотека недоступна, методы возвращают
    понятные сообщения об отсутствии конфигурации, чтобы не ломать бота.
    """

    def __init__(self):
        self.enabled = os.getenv('MCP_ENABLED', '0') == '1'
        self.search_server = os.getenv('MCP_SEARCH_SERVER')
        self.weather_server = os.getenv('MCP_WEATHER_SERVER')
        self.calendar_server = os.getenv('MCP_CALENDAR_SERVER')
        # В этой реализации MCP-клиент использует HTTP-вызовы к локальным FastAPI сервисам.
        # Это упрощённая модель "MCP over HTTP" для демонстрации.

    def is_configured(self) -> bool:
        if not self.enabled:
            return False
        return all([self.search_server, self.weather_server, self.calendar_server])

    async def call(self, server: str, tool: str, payload: dict) -> str:
        """Вызов MCP-инструмента на указанном сервере.

        Для упрощения: возвращаем строковый результат. В реальной жизни
        потребуется сериализация/десериализация структур и обработка ошибок.
        """
        if not self.enabled:
            return f"[MCP mock] {tool}: MCP не настроен."
        if not server:
            return f"[MCP mock] {tool}: сервер не указан."

        try:
            def _do_call():
                if tool == 'search':
                    r = requests.get(f"{server}/search", params={"q": payload.get("q","")}, timeout=8)
                    r.raise_for_status()
                    return r.text
                if tool == 'weather':
                    r = requests.get(f"{server}/weather", params={"city": payload.get("city","")}, timeout=8)
                    r.raise_for_status()
                    return r.text
                if tool == 'calendar.add':
                    r = requests.post(f"{server}/calendar/add", json={
                        "datetime": payload.get("iso"),
                        "duration": payload.get("duration"),
                        "title": payload.get("title"),
                    }, timeout=8)
                    r.raise_for_status()
                    return r.text
                if tool == 'calendar.list':
                    r = requests.get(f"{server}/calendar/list", params={"days": payload.get("days", 7)}, timeout=8)
                    r.raise_for_status()
                    return r.text
                return f"[MCP error] unknown tool: {tool}"

            result = await asyncio.to_thread(_do_call)
            return result
        except Exception as e:
            logger.exception("MCP call failed: server=%s tool=%s", server, tool)
            return f"[MCP error] {tool}: {e}"


