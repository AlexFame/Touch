from datetime import datetime, timedelta

from aiogram import Bot

from app.config import Settings
from app.database import (
    db_get_pending_reminders,
    db_mark_reminder_sent,
    db_get_pending_followups_7d,
    db_mark_followup_7d_sent,
    db_get_pending_followups_30d,
    db_mark_followup_30d_sent,
    db_get_expired_packages,
    db_expire_package,
)
from app.i18n import t
from app.keyboards import book_shortcut_kb, reminder_kb


def format_date(dt: datetime, lang: str) -> str:
    return dt.strftime("%d.%m.%Y") if lang == "ru" else dt.strftime("%d.%m.%Y")


async def send_24h_reminders(bot: Bot, settings: Settings) -> None:
    now = datetime.now(settings.tzinfo)
    lower = now + timedelta(hours=23, minutes=30)
    upper = now + timedelta(hours=24, minutes=30)

    rows = await db_get_pending_reminders(lower.isoformat(), upper.isoformat())

    for row in rows:
        starts_at = datetime.fromisoformat(row["starts_at"])
        lang = row["lang"]
        service = row["title_ua"] if lang == "ua" else row["title_ru"]
        await bot.send_message(
            row["telegram_id"],
            t(
                lang,
                "reminder",
                service=service,
                date=format_date(starts_at, lang),
                time=starts_at.strftime("%H:%M"),
                duration=row["duration_minutes"],
            ),
            reply_markup=reminder_kb(row["id"], lang),
        )
        await db_mark_reminder_sent(row["id"])


async def send_followups(bot: Bot, settings: Settings) -> None:
    now = datetime.now(settings.tzinfo)

    rows_7d = await db_get_pending_followups_7d((now - timedelta(days=7)).isoformat())
    for row in rows_7d:
        await bot.send_message(row["telegram_id"], t(row["lang"], "followup_7d"), reply_markup=book_shortcut_kb(row["lang"], settings.webapp_url))
        await db_mark_followup_7d_sent(row["id"])

    rows_30d = await db_get_pending_followups_30d((now - timedelta(days=30)).isoformat())
    for row in rows_30d:
        await bot.send_message(row["telegram_id"], t(row["lang"], "followup_30d"), reply_markup=book_shortcut_kb(row["lang"], settings.webapp_url))
        await db_mark_followup_30d_sent(row["id"])


async def cleanup_expired_packages() -> None:
    today = datetime.now().date().isoformat()
    expired = await db_get_expired_packages(today)
    for row in expired:
        await db_expire_package(row["id"])
