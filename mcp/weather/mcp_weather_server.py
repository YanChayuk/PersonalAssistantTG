import os
import requests
from fastapi import FastAPI, Query

app = FastAPI(title="MCP Weather Server")

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")


@app.get("/weather")
def weather(city: str = Query("", description="City name")) -> str:
    """
    MCP endpoint for weather. Если OPENWEATHER_KEY не задан — возвращает мок.
    """
    if not city:
        return "[weather] город не указан"
    if not OPENWEATHER_KEY:
        return f"[weather mock] {city}: подключите OPENWEATHER_KEY."
    try:
        url = 'https://api.openweathermap.org/data/2.5/weather'
        params = {'q': city, 'appid': OPENWEATHER_KEY, 'units': 'metric', 'lang': 'ru'}
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        if r.status_code != 200:
            return f"Ошибка: {data.get('message')}"
        desc = data['weather'][0]['description']
        temp = data['main']['temp']
        feels = data['main']['feels_like']
        return f"Погода в {city}: {desc}, {temp}°C (ощущается {feels}°C)."
    except Exception as e:
        return f"Ошибка погоды: {e}"


