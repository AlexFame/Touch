import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.calendar_client import CalendarClient
from app.config import get_settings
from app.database import init_db
from app.handlers import router
from app.scheduler import cleanup_expired_packages, send_24h_reminders, send_followups


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = get_settings()
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(settings=settings, calendar=CalendarClient(settings))
    dp.include_router(router)

    scheduler = AsyncIOScheduler(timezone=settings.business_tz)
    scheduler.add_job(send_24h_reminders, "interval", minutes=15, args=[bot, settings])
    scheduler.add_job(send_followups, "interval", hours=6, args=[bot, settings])
    scheduler.add_job(cleanup_expired_packages, "cron", hour=3, minute=0)
    scheduler.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
