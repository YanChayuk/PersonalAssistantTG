import asyncio, logging, requests

logger = logging.getLogger(__name__)

class WeatherTool:
    def __init__(self, api_key=None):
        self.api_key = api_key

    async def get_weather(self, city):
        if not self.api_key:
            return f"[Weather mock] Погода для {city}: ключ OPENWEATHER_KEY не задан."
        try:
            url = 'https://api.openweathermap.org/data/2.5/weather'
            params = {'q': city, 'appid': self.api_key, 'units': 'metric', 'lang': 'ru'}

            def _do_request():
                r = requests.get(url, params=params, timeout=6)
                return r.status_code, r.json()

            status_code, d = await asyncio.to_thread(_do_request)
            if status_code != 200:
                return f"Ошибка: {d.get('message')}"
            desc = d['weather'][0]['description']
            temp = d['main']['temp']
            feels = d['main']['feels_like']
            return f"Погода в {city}: {desc}, {temp}°C (ощущается {feels}°C)."
        except Exception as e:
            logger.exception("WeatherTool.get_weather failed")
            return f"Ошибка при запросе погоды: {e}"
