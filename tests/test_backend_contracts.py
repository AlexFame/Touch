import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

os.environ.pop("DATABASE_URL", None)
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("ADMIN_IDS", "111")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DEV_TELEGRAM_ID", "222")
os.environ.setdefault("CALENDAR_ENABLED", "false")

from app import database
from backend import main as api


class FailingCalendar:
    def enabled(self):
        return True

    def get_busy_ranges(self, start, end):
        return []

    def create_event(self, **kwargs):
        raise RuntimeError("calendar is down")

    def delete_event(self, event_id):
        raise RuntimeError("calendar is down")

    def update_event(self, *args, **kwargs):
        raise RuntimeError("calendar is down")


class FailingBot:
    async def send_message(self, *args, **kwargs):
        raise RuntimeError("telegram is down")


class BackendContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.tmpdir.name) / "test.sqlite3"
        await database.init_db()
        self.original_calendar = api.calendar
        self.original_bot = api.bot
        api.calendar = FailingCalendar()
        api.bot = FailingBot()

    async def asyncTearDown(self):
        api.calendar = self.original_calendar
        api.bot = self.original_bot
        self.tmpdir.cleanup()

    async def test_services_contract_has_current_prices_and_languages(self):
        ru_services = await api.services("ru")
        uk_services = await api.services("uk")
        ru_by_id = {service["id"]: service for service in ru_services}
        uk_by_id = {service["id"]: service for service in uk_services}

        self.assertEqual(ru_by_id["classic_back"]["price_eur"], 25)
        self.assertEqual(ru_by_id["relax"]["price_eur"], 25)
        self.assertEqual(ru_by_id["general"]["duration_minutes"], 90)
        self.assertEqual(ru_by_id["general"]["price_eur"], 70)
        self.assertIn("Классический", ru_by_id["classic_back"]["title"])
        self.assertIn("Класичний", uk_by_id["classic_back"]["title"])
        self.assertFalse(any(service["is_package"] for service in ru_services))

    async def test_create_booking_is_db_first_when_calendar_and_telegram_fail(self):
        day_iso = (datetime.now(api.settings.tzinfo).date() + timedelta(days=4)).isoformat()
        payload = api.BookingCreate(
            service_id="classic_back",
            day_iso=day_iso,
            slot="10:00",
            name="Alexey",
            contact="@iam_fvme",
            lang="ru",
        )

        with self.assertLogs(api.logger, level="WARNING") as logs:
            response = await api.create_booking(payload, initData="", x_telegram_init_data="")
            await __import__("asyncio").sleep(0)

        self.assertGreater(response["appointment_id"], 0)
        self.assertEqual(response["price_eur"], 25)
        self.assertEqual(response["duration_minutes"], 60)
        self.assertTrue(response["first_visit_bonus_applied"])
        self.assertTrue(any("Google Calendar sync failed" in item for item in logs.output))
        self.assertTrue(any("failed to notify client" in item for item in logs.output))
        self.assertTrue(any("failed to notify admin" in item for item in logs.output))

        async with aiosqlite.connect(database.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            row = await (
                await db.execute(
                    "SELECT a.*, c.name, c.contact FROM appointments a JOIN clients c ON c.id = a.client_id WHERE a.id = ?",
                    (response["appointment_id"],),
                )
            ).fetchone()

        self.assertEqual(row["status"], "booked")
        self.assertEqual(row["name"], "Alexey")
        self.assertEqual(row["contact"], "@iam_fvme")

    async def test_invalid_name_and_contact_are_rejected_before_booking(self):
        with self.assertRaises(Exception):
            await api.create_booking(
                api.BookingCreate(
                    service_id="classic_back",
                    day_iso=(datetime.now(api.settings.tzinfo).date() + timedelta(days=4)).isoformat(),
                    slot="10:00",
                    name="https://spam.example",
                    contact="@iam_fvme",
                    lang="ru",
                ),
                initData="",
                x_telegram_init_data="",
            )
