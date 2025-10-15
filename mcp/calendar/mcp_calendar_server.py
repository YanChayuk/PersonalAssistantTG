import os
import datetime as dt
from typing import List
from fastapi import FastAPI, Query
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = FastAPI(title="MCP Calendar Server")

GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
CALENDAR_ID = os.getenv('CALENDAR_ID')
_service = None

if GOOGLE_CREDENTIALS_PATH and os.path.exists(GOOGLE_CREDENTIALS_PATH) and CALENDAR_ID:
    try:
        scopes = ['https://www.googleapis.com/auth/calendar']
        creds = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=scopes)
        _service = build('calendar', 'v3', credentials=creds)
    except Exception:
        _service = None


class AddEventPayload(BaseModel):
    datetime: str
    duration: int
    title: str


@app.post("/calendar/add")
def add_event(payload: AddEventPayload) -> str:
    """
    MCP endpoint for adding calendar events. Если нет Google creds — моковый ответ.
    """
    try:
        start = dt.datetime.fromisoformat(payload.datetime)
        end = start + dt.timedelta(minutes=payload.duration)
    except Exception:
        return "Ошибка: неверный формат даты/времени"

    if not _service or not CALENDAR_ID:
        return f"[calendar mock] Добавлено: {payload.title} ({start.isoformat()} — {end.isoformat()})"

    try:
        event = {
            'summary': payload.title,
            'start': {'dateTime': start.isoformat(), 'timeZone': os.getenv('TIMEZONE','UTC')},
            'end': {'dateTime': end.isoformat(), 'timeZone': os.getenv('TIMEZONE','UTC')},
        }
        ev = _service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"Событие добавлено: {ev.get('htmlLink')}"
    except Exception as e:
        return f"Ошибка добавления события: {e}"


@app.get("/calendar/list")
def list_events(days: int = Query(7, ge=1, le=365)) -> str:
    """
    MCP endpoint for listing calendar events. Если нет Google creds — моковые события.
    """
    now = dt.datetime.utcnow()
    if not _service or not CALENDAR_ID:
        items: List[str] = []
        for i in range(min(days, 5)):
            when = (now + dt.timedelta(days=i)).isoformat() + "Z"
            items.append(f"{when} - Моковое событие #{i+1}")
        return "\n".join(items) if items else "Событий нет."

    try:
        events = _service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now.isoformat()+'Z',
            timeMax=(now + dt.timedelta(days=days)).isoformat()+'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        items = events.get('items', [])
        if not items:
            return 'Событий нет.'
        out = []
        for it in items:
            s = it['start'].get('dateTime', it['start'].get('date'))
            out.append(f"{s} - {it.get('summary','(без названия)')}")
        return "\n".join(out)
    except Exception as e:
        return f"Ошибка получения событий: {e}"


