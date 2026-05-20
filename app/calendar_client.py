from datetime import datetime
from typing import Iterable

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import Settings


SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.service = None
        if settings.calendar_enabled:
            import os
            import json
            env_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
            if env_json:
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(env_json),
                    scopes=SCOPES,
                )
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.google_service_account_file,
                    scopes=SCOPES,
                )
            self.service = build("calendar", "v3", credentials=credentials)

    def enabled(self) -> bool:
        return self.service is not None

    def get_busy_ranges(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        """Return busy intervals from Google Calendar in local timezone.

        Google Calendar is the source of truth for father's real availability:
        manual events, bot-created bookings, holidays, blocked time, etc.
        """
        if not self.enabled():
            return []

        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "timeZone": self.settings.business_tz,
            "items": [{"id": self.settings.google_calendar_id}],
        }
        result = self.service.freebusy().query(body=body).execute()
        busy_items = result.get("calendars", {}).get(self.settings.google_calendar_id, {}).get("busy", [])

        ranges: list[tuple[datetime, datetime]] = []
        for item in busy_items:
            busy_start = datetime.fromisoformat(item["start"].replace("Z", "+00:00")).astimezone(self.settings.tzinfo)
            busy_end = datetime.fromisoformat(item["end"].replace("Z", "+00:00")).astimezone(self.settings.tzinfo)
            ranges.append((busy_start, busy_end))
        return ranges

    def create_event(
        self,
        summary: str,
        description: str,
        start: datetime,
        end: datetime,
        appointment_id: int | None = None,
    ) -> str | None:
        if not self.enabled():
            return None

        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": self.settings.business_tz},
            "end": {"dateTime": end.isoformat(), "timeZone": self.settings.business_tz},
            "extendedProperties": {
                "private": {
                    "source": "massage_touch_bot",
                    "appointment_id": str(appointment_id or ""),
                }
            },
        }

        created = (
            self.service.events()
            .insert(calendarId=self.settings.google_calendar_id, body=event)
            .execute()
        )
        return created.get("id")

    def update_event_description(self, event_id: str | None, description: str) -> None:
        if not self.enabled() or not event_id:
            return
        self.service.events().patch(
            calendarId=self.settings.google_calendar_id,
            eventId=event_id,
            body={"description": description},
        ).execute()

    def update_event(
        self,
        event_id: str | None,
        summary: str,
        description: str,
        start: datetime,
        end: datetime,
    ) -> None:
        if not self.enabled() or not event_id:
            return
        self.service.events().patch(
            calendarId=self.settings.google_calendar_id,
            eventId=event_id,
            body={
                "summary": summary,
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": self.settings.business_tz},
                "end": {"dateTime": end.isoformat(), "timeZone": self.settings.business_tz},
            },
        ).execute()

    def delete_event(self, event_id: str | None) -> None:
        if not self.enabled() or not event_id:
            return
        self.service.events().delete(
            calendarId=self.settings.google_calendar_id,
            eventId=event_id,
        ).execute()
