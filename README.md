# Personal Assistant — Telegram Agent (Ubuntu target) + MCP

## Содержание
Личный помощник через Telegram, использующий три MCP‑сервера (поиск, погода, календарь), память (SQLite) и векторную базу (Chroma).

## Быстрый старт (Ubuntu 22.04)
1. Скопируйте репозиторий на сервер, например `/opt/assistant-personal`.
2. Положите JSON сервисного аккаунта в `/opt/assistant-personal/credentials/google_service.json`.
3. Создайте файл `.env` и заполните переменные:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   MCP_ENABLED=1
   MCP_SEARCH_SERVER=http://mcp-search:8081
   MCP_WEATHER_SERVER=http://mcp-weather:8082
   MCP_CALENDAR_SERVER=http://mcp-calendar:8083
   # Ключи для реальных внешних API, которые вызывают MCP-сервера
   ZENSERP_KEY=your_zenserp_key_here
   OPENWEATHER_KEY=your_openweather_api_key_here
   GOOGLE_CREDENTIALS_PATH=/app/credentials/google_service.json
   CALENDAR_ID=your_calendar_id_here
   TIMEZONE=UTC
   ```
4. Запустите весь стек (бот + 3 MCP‑сервиса): `docker-compose up --build -d`
5. Для systemd: отредактируйте `systemd/assistant.service` путь `WorkingDirectory` и `ExecStart`, затем:  
   ```bash
   sudo cp systemd/assistant.service /etc/systemd/system/assistant.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now assistant.service
   ```

## Testing and Verification
1. Проверьте Telegram команды:
   - `/help` — список команд, наличие `/seed`
   - `/health` — состояние сервисов
   - `search:пример запроса` — идёт в MCP‑сервер поиска, который вызывает ZenSerp (при наличии `ZENSERP_KEY`), иначе отдаёт мок
   - `weather:Москва` — идёт в MCP‑сервер погоды, который вызывает OpenWeatherMap (при наличии `OPENWEATHER_KEY`), иначе отдаёт мок
   - `calendar:add:2025-10-20T15:00:00|60|Встреча` — добавление события через MCP‑сервер календаря (Google Calendar при наличии `GOOGLE_CREDENTIALS_PATH` и `CALENDAR_ID`, иначе мок)
   - `calendar:list:7` — список ближайших событий через MCP‑сервер календаря (реальные или моковые)
2. Проверьте семантический поиск:
   - Выполните `/seed` в Telegram, затем спросите: "какая база для семантического поиска?" — в ответе должны упоминаться документы Chroma.
3. Healthcheck контейнера:
   - Убедитесь, что `docker ps` показывает `healthy` (проверяется `http://localhost:8080/healthz`).
4. Cursor логи: в директории `conversations/` приложите экспортированные логи сессий Cursor (пример `example_session.log`).

## MCP сервера
Три MCP‑сервера поднимаются вместе с ботом через `docker-compose` и доступны по адресам из `.env`. Агент выступает как MCP‑клиент и вызывает инструменты `search`, `weather`, `calendar.add`/`calendar.list` на соответствующих серверах. Сервера:
- `mcp-search` (`/search?q=`) — проксирует запрос в ZenSerp.
- `mcp-weather` (`/weather?city=`) — проксирует запрос в OpenWeatherMap.
- `mcp-calendar` (`POST /calendar/add`, `GET /calendar/list?days=`) — работает с Google Calendar через service account.
Если ключи/креды не заданы, каждый сервер возвращает безопасные мок‑ответы, чтобы бот оставался работоспособным.

## Команды в Telegram
- `/help` — подсказки
- `/health` — состояние сервисов
- `search:<запрос>` — поиск в вебе
- `weather:<город>` — погода
- `calendar:add:2025-10-20T15:00:00|60|Встреча` — добавить событие (UTC)
- `calendar:list:7` — показать события на 7 дней вперед

## Что нужно заменить
1. TELEGRAM_BOT_TOKEN — токен от BotFather.
2. OPENAI_API_KEY (опционально) — для LLM.
3. ZENSERP_KEY — ключ ZenSerp (поиск).
4. OPENWEATHER_KEY — ключ OpenWeatherMap (погода).
5. GOOGLE_CREDENTIALS_PATH — путь до JSON сервисного аккаунта Google.
6. CALENDAR_ID — id календаря (в Integrate calendar), сервисный аккаунт должен иметь доступ.
