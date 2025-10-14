import asyncio, logging, requests

logger = logging.getLogger(__name__)

class WebSearchTool:
    def __init__(self, api_key=None):
        self.api_key = api_key

    async def search(self, query):
        if not self.api_key:
            return f"[Search mock] Что искать: {query} — (подключите SERPAPI_KEY для реального поиска)."
        params = {"engine": "google", "q": query, "api_key": self.api_key}
        try:
            def _do_request():
                r = requests.get('https://serpapi.com/search.json', params=params, timeout=8)
                r.raise_for_status()
                return r.json()

            data = await asyncio.to_thread(_do_request)
            snippets = []
            for item in data.get('organic_results', [])[:3]:
                title = item.get('title'); link = item.get('link'); snippet = item.get('snippet') or ''
                snippets.append(f"{title}\n{snippet}\n{link}")
            return '\n\n'.join(snippets) if snippets else 'Ничего не найдено.'
        except Exception as e:
            logger.exception("WebSearchTool.search failed")
            return f'Ошибка при поиске: {e}'
