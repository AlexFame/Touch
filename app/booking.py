from datetime import datetime, date, time, timedelta
from typing import Protocol

from app.config import Settings
from app.database import db_first_visit_bonus_available, db_get_booked_appointments_for_day


class BusyCalendar(Protocol):
    def get_busy_ranges(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]: ...


def parse_local_datetime(day_iso: str, slot_hhmm: str, settings: Settings) -> datetime:
    hour, minute = map(int, slot_hhmm.split(":"))
    d = date.fromisoformat(day_iso)
    return datetime.combine(d, time(hour, minute), tzinfo=settings.tzinfo)


async def first_visit_bonus_available(client_id: int) -> bool:
    return await db_first_visit_bonus_available(client_id)


async def get_free_slots(
    day_iso: str,
    duration_minutes: int,
    settings: Settings,
    calendar: BusyCalendar | None = None,
) -> list[str]:
    d = date.fromisoformat(day_iso)
    start = datetime.combine(d, time(settings.business_start_hour, 0), tzinfo=settings.tzinfo)
    end_of_day = datetime.combine(d, time(settings.business_end_hour, 0), tzinfo=settings.tzinfo)

    rows = await db_get_booked_appointments_for_day(day_iso)

    busy: list[tuple[datetime, datetime]] = []
    for row in rows:
        busy_start = datetime.fromisoformat(row["starts_at"]).astimezone(settings.tzinfo)
        busy_end = datetime.fromisoformat(row["ends_at"]).astimezone(settings.tzinfo)
        busy.append((busy_start, busy_end))

    if calendar is not None:
        busy.extend(calendar.get_busy_ranges(start, end_of_day))

    slots = []
    cursor = start
    now = datetime.now(settings.tzinfo)
    full_duration = timedelta(minutes=duration_minutes + settings.buffer_minutes)

    while cursor + full_duration <= end_of_day:
        slot_end = cursor + full_duration

        if cursor > now:
            overlap = any(cursor < b_end and slot_end > b_start for b_start, b_end in busy)
            if not overlap:
                slots.append(cursor.strftime("%H:%M"))

        cursor += timedelta(minutes=settings.slot_step_minutes)

    return slots


def format_summary(lang: str, service_title: str, start: datetime, duration: int, price: int, name: str, contact: str, bonus: bool) -> str:
    bonus_line = "\nБонус первого визита: +15 минут" if bonus and lang == "ru" else ""
    if bonus and lang == "ua":
        bonus_line = "\nБонус першого візиту: +15 хвилин"

    return (
        f"Услуга: {service_title}\n"
        f"Дата: {start.strftime('%d.%m.%Y')}\n"
        f"Время: {start.strftime('%H:%M')}\n"
        f"Длительность: {duration} мин\n"
        f"Цена: {price}€\n"
        f"Имя: {name}\n"
        f"Контакт: {contact}"
        f"{bonus_line}"
    )
