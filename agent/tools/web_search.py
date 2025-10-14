import asyncio, logging, requests

logger = logging.getLogger(__name__)

class WebSearchTool:
    def __init__(self, api_key=None):
        self.api_key = api_key

    async def search(self, query):
        if not self.api_key:
            return f"[Search mock] Что искать: {query} — (подключите ZENSERP_KEY для реального поиска)."
        
        url = "https://app.zenserp.com/api/v2/search"
        params = {"q": query}
        headers = {"apikey": self.api_key}
        
        try:
            def _do_request():
                r = requests.get(url, params=params, headers=headers, timeout=8)
                r.raise_for_status()
                return r.json()

            data = await asyncio.to_thread(_do_request)
            snippets = []
            
            # ZenSerp API structure
            organic_results = data.get('organic', [])
            for item in organic_results[:3]:
                title = item.get('title', '')
                link = item.get('url', '')
                snippet = item.get('description', '')
                snippets.append(f"{title}\n{snippet}\n{link}")
            
            return '\n\n'.join(snippets) if snippets else 'Ничего не найдено.'
        except Exception as e:
            logger.exception("WebSearchTool.search failed")
            return f'Ошибка при поиске: {e}'
