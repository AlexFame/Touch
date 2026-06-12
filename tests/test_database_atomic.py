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
os.environ.setdefault("CALENDAR_ENABLED", "false")

from app import database
from app.booking import parse_local_datetime
from app.config import get_settings


class DatabaseAtomicTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        database.DB_PATH = Path(self.tmpdir.name) / "test.sqlite3"
        await database.init_db()
        self.settings = get_settings()
        self.day_iso = (datetime.now(self.settings.tzinfo).date() + timedelta(days=3)).isoformat()

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_create_booking_atomic_creates_package_and_marks_bonus(self):
        client = await database.db_ensure_client(2001)
        start = parse_local_datetime(self.day_iso, "12:00", self.settings)
        appointment_id = await database.db_create_booking_atomic(
            client["id"],
            "classic_back_package_5",
            start.isoformat(),
            (start + timedelta(minutes=60)).isoformat(),
            45,
            90,
            "test",
            1,
            package_sessions=5,
            package_expires_at=(start.date() + timedelta(days=90)).isoformat(),
        )

        self.assertGreater(appointment_id, 0)
        async with aiosqlite.connect(database.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            client_row = await (await db.execute("SELECT * FROM clients WHERE id = ?", (client["id"],))).fetchone()
            package_row = await (await db.execute("SELECT * FROM packages WHERE client_id = ?", (client["id"],))).fetchone()
            appointment_row = await (await db.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))).fetchone()

        self.assertEqual(client_row["first_visit_bonus_used"], 1)
        self.assertEqual(package_row["sessions_total"], 5)
        self.assertEqual(appointment_row["status"], "booked")

    async def test_reschedule_atomic_keeps_old_and_new_state_consistent(self):
        client = await database.db_ensure_client(2002)
        old_start = parse_local_datetime(self.day_iso, "13:00", self.settings)
        old_id = await database.db_create_booking_atomic(
            client["id"],
            "relax",
            old_start.isoformat(),
            (old_start + timedelta(minutes=60)).isoformat(),
            60,
            25,
            "test",
            1,
        )

        new_start = parse_local_datetime(self.day_iso, "16:00", self.settings)
        new_id = await database.db_reschedule_atomic(
            old_id,
            client["id"],
            "relax",
            new_start.isoformat(),
            (new_start + timedelta(minutes=60)).isoformat(),
            60,
            25,
            "test",
            1,
        )

        async with aiosqlite.connect(database.DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            old_row = await (await db.execute("SELECT * FROM appointments WHERE id = ?", (old_id,))).fetchone()
            new_row = await (await db.execute("SELECT * FROM appointments WHERE id = ?", (new_id,))).fetchone()

        self.assertEqual(old_row["status"], "rescheduled")
        self.assertEqual(new_row["status"], "booked")
        self.assertEqual(new_row["starts_at"], new_start.isoformat())
