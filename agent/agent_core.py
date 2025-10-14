import os, openai, asyncio, logging
from .memory import Memory
from .vstore import VStore
from .tools.web_search import WebSearchTool
from .tools.weather import WeatherTool
from .tools.google_calendar import GoogleCalendarTool
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

class AgentCore:
    def __init__(self):
        self.memory = Memory(db_path=os.getenv('SQLITE_DB','./data/memory.db'))
        self.vstore = VStore(chroma_dir=os.getenv('CHROMA_DIR','./chroma_db'))
        self.search = WebSearchTool(api_key=os.getenv('SERPAPI_KEY'))
        self.weather = WeatherTool(api_key=os.getenv('OPENWEATHER_KEY'))
        self.calendar = GoogleCalendarTool(creds_path=os.getenv('GOOGLE_CREDENTIALS_PATH'), calendar_id=os.getenv('CALENDAR_ID'))
        self.logger = logging.getLogger(__name__)
    def health_check(self):
        ok = []
        ok.append(f"Memory: {'OK' if self.memory.ping() else 'FAIL'}")
        ok.append(f"VStore: {'OK' if self.vstore.ping() else 'FAIL'}")
        ok.append(f"Search: {'configured' if self.search.api_key else 'mock'}")
        ok.append(f"Weather: {'configured' if self.weather.api_key else 'mock'}")
        ok.append(f"Calendar: {'configured' if self.calendar.configured else 'not configured'}")
        return '\n'.join(ok)
    async def handle_message(self, user_id: str, text: str) -> str:
        t = text.strip()
        low = t.lower()
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
        # generic: use vstore + llm if available
        docs = self.vstore.search(text, k=3)
        prompt = 'You are a helpful personal assistant.\n\nUser: ' + text + '\n\n'
        if docs:
            prompt += '\nRelevant documents:\n' + '\n'.join([f'- {d}' for d in docs]) + '\n'
        history = self.memory.get_recent(user_id, limit=6)
        if history:
            prompt += '\nConversation history:\n' + '\n'.join([f"{r['role']}: {r['text']}" for r in history]) + '\n'
        if OPENAI_API_KEY:
            try:
                resp = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=[{'role':'user','content':prompt}],
                    max_tokens=400
                )
                return resp['choices'][0]['message']['content'].strip()
            except Exception as e:
                self.logger.exception('LLM error')
                return f'LLM error: {e}'
        return "Я бот-помощник (LLM не настроен). Доступные команды: search:, weather:, calendar:add:, calendar:list:."

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
                self.vstore.add(doc_id, text, meta={'source': 'demo'})
                added += 1
            except Exception:
                self.logger.exception('Failed to add document to VStore')
        # Выполним тестовый поиск, чтобы прогреть индекс
        _ = self.vstore.search('семантический поиск ассистент', k=3)
        return added
