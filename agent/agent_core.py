import os, asyncio, logging
from .memory import Memory
from .vstore import VStore
from .mcp_client import MCPClient
from .tools.mcp_search import MCPSearchTool
from .tools.mcp_weather import MCPWeatherTool
from .tools.mcp_calendar import MCPCalendarTool
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

class AgentCore:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory = Memory(db_path=os.getenv('SQLITE_DB','./data/memory.db'))
        self.vstore = VStore(chroma_dir=os.getenv('CHROMA_DIR','./chroma_db'))
        # MCP client and tools
        self.mcp = MCPClient()
        self.search = MCPSearchTool(self.mcp)
        self.weather = MCPWeatherTool(self.mcp)
        self.calendar = MCPCalendarTool(self.mcp)
        # Track active user sessions
        self.active_sessions = set()
    def health_check(self):
        ok = []
        ok.append(f"Memory: {'OK' if self.memory.ping() else 'FAIL'}")
        ok.append(f"VStore: {'OK' if self.vstore.ping() else 'FAIL'}")
        ok.append(f"MCP: {'configured' if self.mcp.is_configured() else 'not configured'}")
        ok.append(f"Active sessions: {len(self.active_sessions)}")
        return '\n'.join(ok)
    async def handle_message(self, user_id: str, text: str) -> str:
        # Track active session
        self.active_sessions.add(user_id)
        
        try:
            t = text.strip()
            low = t.lower()
            
            # Handle commands
            if low.startswith('search:'):
                q = t.split(':',1)[1].strip()
                return await self.search.search(q)
            if low.startswith('weather:'):
                city = t.split(':',1)[1].strip()
                return await self.weather.get_weather(city)
            if low.startswith('calendar:add:'):
                payload = t.split(':',2)[2]
                # expected format ISOdatetime|duration_minutes|title
                try:
                    dt, dur, title = payload.split('|',2)
                except:
                    return 'Неверный формат. Используй: calendar:add:2025-10-20T15:00:00|60|Встреча'
                return await self.calendar.add_event(dt, int(dur), title)
            if low.startswith('calendar:list:'):
                try:
                    days = int(t.split(':',2)[2])
                except Exception:
                    return 'Неверный формат. Используй: calendar:list:7'
                return await self.calendar.list_events(days)
            
            if low.startswith('seed:'):
                # seed:demo
                arg = t.split(':',1)[1].strip()
                if arg == 'demo':
                    added = self.seed_chroma_demo()
                    return f'Добавлено {added} документов в векторное хранилище.'
                return 'Неизвестный seed. Используй: seed:demo'
            if low.startswith('calendar:test'):
                # Test calendar via MCP
                if not self.mcp.is_configured():
                    return 'MCP для календаря не настроен. Укажите MCP_CALENDAR_SERVER.'
                try:
                    res = await self.calendar.list_events(1)
                    if not res or 'Событий нет' in res:
                        return '✅ MCP календарь доступен, но событий нет.'
                    return f'✅ MCP календарь доступен. Пример:\n{res.splitlines()[0]}'
                except Exception as e:
                    return f'❌ Ошибка MCP календаря: {e}'
            
            # Generic conversation with context isolation per user
            docs = self.vstore.search(text, k=3)
            prompt = f'You are a helpful personal assistant for user {user_id}.\n\nUser: ' + text + '\n\n'
            if docs:
                prompt += '\nRelevant documents:\n' + '\n'.join([f'- {d}' for d in docs]) + '\n'
            
            # Get user-specific conversation history
            history = self.memory.get_recent(user_id, limit=6)
            if history:
                prompt += '\nConversation history:\n' + '\n'.join([f"{r['role']}: {r['text']}" for r in history]) + '\n'
            
            if OPENAI_API_KEY:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=OPENAI_API_KEY)
                    resp = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[{'role':'user','content':prompt}],
                        max_tokens=400
                    )
                    return resp.choices[0].message.content.strip()
                except Exception as e:
                    self.logger.exception('LLM error')
                    return f'LLM error: {e}'
            return "Я бот-помощник (LLM не настроен). Доступные команды: search:, weather:, calendar:add:, calendar:list:."
        
        finally:
            # Keep session active for a while, remove after timeout
            asyncio.create_task(self._cleanup_session_later(user_id))
    
    async def _cleanup_session_later(self, user_id: str):
        """Remove user session after 5 minutes of inactivity"""
        await asyncio.sleep(300)  # 5 minutes
        self.active_sessions.discard(user_id)

    def seed_chroma_demo(self) -> int:
        """Добавляет демонстрационные документы и делает тестовый запрос."""
        demo_docs = {
            'doc1': 'Telegram персональный ассистент поддерживает веб-поиск, погоду и календарь Google.',
            'doc2': 'Векторная база данных Chroma используется для семантического поиска релевантных документов.',
            'doc3': 'Память диалога хранится в SQLite, последние сообщения добавляются в промпт.'
        }
        added = 0
        for doc_id, text in demo_docs.items():
            try:
                # Check if document already exists to avoid warnings
                existing = self.vstore.search(text, k=1)
                if not existing:
                    self.vstore.add(doc_id, text, meta={'source': 'demo'})
                    added += 1
            except Exception:
                self.logger.exception('Failed to add document to VStore')
        # Выполним тестовый поиск, чтобы прогреть индекс
        _ = self.vstore.search('семантический поиск ассистент', k=3)
        return added
