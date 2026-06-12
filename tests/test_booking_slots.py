import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

os.environ.pop("DATABASE_URL", None)
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("ADMIN_IDS", "111")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("CALENDAR_ENABLED", "false")

from app import database
from app.booking import get_free_slots, parse_local_datetime
from app.config import get_settings


class DummyCalendar:
    def __init__(self, busy_ranges):
        self.busy_ranges = busy_ranges

    def get_busy_ranges(self, start, end):
        return self.busy_ranges


class BookingSlotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.tmpdir.name) / "test.sqlite3"
        await database.init_db()
        self.settings = get_settings()
        self.day_iso = (datetime.now(self.settings.tzinfo).date() + timedelta(days=2)).isoformat()

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_parse_local_datetime_uses_business_timezone(self):
        parsed = parse_local_datetime(self.day_iso, "10:30", self.settings)
        self.assertEqual(parsed.strftime("%H:%M"), "10:30")
        self.assertEqual(parsed.tzinfo, self.settings.tzinfo)

    async def test_slots_respect_db_busy_ranges_calendar_busy_ranges_and_buffer(self):
        client = await database.db_ensure_client(1001)
        busy_start = parse_local_datetime(self.day_iso, "10:30", self.settings)
        busy_end = busy_start + timedelta(minutes=60)
        await database.db_create_booking_atomic(
            client["id"],
            "classic_back",
            busy_start.isoformat(),
            busy_end.isoformat(),
            45,
            25,
            "test",
            0,
        )

        calendar_busy_start = parse_local_datetime(self.day_iso, "14:00", self.settings)
        calendar_busy_end = calendar_busy_start + timedelta(minutes=60)
        slots = await get_free_slots(
            self.day_iso,
            45,
            self.settings,
            DummyCalendar([(calendar_busy_start, calendar_busy_end)]),
        )

        self.assertNotIn("10:00", slots)
        self.assertNotIn("10:30", slots)
        self.assertNotIn("11:00", slots)
        self.assertIn("11:30", slots)
        self.assertNotIn("13:30", slots)
        self.assertNotIn("14:00", slots)
        self.assertNotIn("14:30", slots)
        self.assertIn("15:00", slots)
