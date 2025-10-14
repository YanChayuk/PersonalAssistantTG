import os, datetime, json, asyncio, logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

class GoogleCalendarTool:
    def __init__(self, creds_path=None, calendar_id=None):
        self.creds_path = creds_path
        self.calendar_id = calendar_id
        self.configured = False
        if creds_path and os.path.exists(creds_path) and calendar_id:
            try:
                scopes = ['https://www.googleapis.com/auth/calendar']
                creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
                self.service = build('calendar', 'v3', credentials=creds)
                self.configured = True
            except Exception as e:
                print('GoogleCalendar init error:', e)
                self.configured = False
        self.logger = logging.getLogger(__name__)
        self.timezone = os.getenv('TIMEZONE', 'UTC')
    async def add_event(self, iso_dt, duration_minutes, title):
        if not self.configured:
            return '[Calendar mock] Сервис не настроен. Укажите GOOGLE_CREDENTIALS_PATH и CALENDAR_ID.'
        try:
            start = datetime.datetime.fromisoformat(iso_dt)
            end = start + datetime.timedelta(minutes=duration_minutes)
            event = {
                'summary': title,
                'start': {'dateTime': start.isoformat(), 'timeZone': self.timezone},
                'end': {'dateTime': end.isoformat(), 'timeZone': self.timezone},
            }

            def _do_insert():
                return self.service.events().insert(calendarId=self.calendar_id, body=event).execute()

            ev = await asyncio.to_thread(_do_insert)
            return f"Событие добавлено: {ev.get('htmlLink')}"
        except Exception as e:
            self.logger.exception('Calendar add_event failed')
            return f'Ошибка добавления события: {e}'
    async def list_events(self, days=7):
        if not self.configured:
            return '[Calendar mock] Сервис не настроен.'
        try:
            now = datetime.datetime.utcnow()
            end = now + datetime.timedelta(days=days)

            def _do_list():
                return self.service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=now.isoformat()+'Z',
                    timeMax=end.isoformat()+'Z',
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()

            events_result = await asyncio.to_thread(_do_list)
            items = events_result.get('items', [])
            if not items:
                return 'Событий нет.'
            out = []
            for it in items:
                s = it['start'].get('dateTime', it['start'].get('date'))
                out.append(f"{s} - {it.get('summary','(без названия)')}")
            return '\n'.join(out)
        except Exception as e:
            self.logger.exception('Calendar list_events failed')
            return f'Ошибка при получении событий: {e}'
