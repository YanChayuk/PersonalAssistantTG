import os
import requests
from fastapi import FastAPI, Query

app = FastAPI(title="MCP Search Server")

ZENSERP_KEY = os.getenv("ZENSERP_KEY")


@app.get("/search")
def search(q: str = Query("", description="Search query")) -> str:
    """
    MCP endpoint for search. Если ZENSERP_KEY не задан — возвращает мок.
    Можно заменить на другой внешний API.
    """
    if not q:
        return "[search] пустой запрос"
    if not ZENSERP_KEY:
        return f"[search mock] {q}: подключите ZENSERP_KEY."
    try:
        url = "https://app.zenserp.com/api/v2/search"
        params = {"q": q}
        headers = {"apikey": ZENSERP_KEY}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        organic = data.get("organic", [])
        snippets = []
        for item in organic[:3]:
            title = item.get("title", "")
            link = item.get("url", "")
            desc = item.get("description", "")
            snippets.append(f"{title}\n{desc}\n{link}")
        return "\n\n".join(snippets) if snippets else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {e}"


