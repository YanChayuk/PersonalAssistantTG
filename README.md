# Personal Assistant — Telegram Agent (Ubuntu target)

## Содержание
Личный помощник через Telegram, использующий WebSearch, Weather и Google Calendar (service account), память (SQLite) и векторную базу (Chroma).

## Быстрый старт (Ubuntu 22.04)
1. Скопируйте репозиторий на сервер, например `/opt/assistant-personal`.
2. Положите JSON сервисного аккаунта в `/opt/assistant-personal/credentials/google_service.json`.
3. Создайте файл `.env` и заполните переменные:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ZENSERP_KEY=363de5b0-a940-11f0-a723-235492112ea0
   OPENWEATHER_KEY=your_openweather_api_key_here
   GOOGLE_CREDENTIALS_PATH=./credentials/google_service.json
   CALENDAR_ID=your_calendar_id_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```
4. Запустите: `docker-compose up --build -d`
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
   - `search:пример запроса` — реальные результаты при наличии `ZENSERP_KEY`
   - `weather:Москва` — реальные данные при наличии `OPENWEATHER_KEY`
   - `calendar:add:2025-10-20T15:00:00|60|Встреча` — добавление события (UTC)
   - `calendar:list:7` — список ближайших событий
2. Проверьте семантический поиск:
   - Выполните `/seed` в Telegram, затем спросите: "какая база для семантического поиска?" — в ответе должны упоминаться документы Chroma.
3. Healthcheck контейнера:
   - Убедитесь, что `docker ps` показывает `healthy` (проверяется `http://localhost:8080/healthz`).
4. Cursor логи: в директории `conversations/` приложите экспортированные логи сессий Cursor (пример `example_session.log`).

## Примечания по Google Calendar (Service Account)
- Рекомендуемые области доступа: `https://www.googleapis.com/auth/calendar` (минимально необходимые права).
- Убедитесь, что сервисный аккаунт имеет доступ к `CALENDAR_ID` (расшарьте календарь по e-mail сервисного аккаунта).
- Используются серверные ключи: `GOOGLE_CREDENTIALS_PATH` указывает путь до service account JSON.

## Команды в Telegram
- `/help` — подсказки
- `/health` — состояние сервисов
- `search:<запрос>` — поиск в вебе
- `weather:<город>` — погода
- `calendar:add:2025-10-20T15:00:00|60|Встреча` — добавить событие (UTC)
- `calendar:list:7` — показать события на 7 дней вперед

## Что нужно заменить
1. TELEGRAM_BOT_TOKEN — токен от BotFather.
2. GOOGLE_CREDENTIALS_PATH — путь до JSON сервисного аккаунта.
3. CALENDAR_ID — id календаря (в Integrate calendar).
4. OPENAI_API_KEY (опционально) — для LLM.
5. ZENSERP_KEY, OPENWEATHER_KEY (опционально).
