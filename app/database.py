import os
import aiosqlite
from pathlib import Path

try:
    import asyncpg
except ImportError:
    asyncpg = None

DB_PATH = Path("massage_bot.sqlite3")
DATABASE_URL = os.getenv("DATABASE_URL")
_pg_pool = None

class DBRow:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def keys(self):
        return self._data.keys()
    def get(self, key, default=None):
        return self._data.get(key, default)

async def init_pool() -> None:
    global _pg_pool
    if DATABASE_URL:
        if not asyncpg:
            raise RuntimeError("asyncpg is required for PostgreSQL")
        _pg_pool = await asyncpg.create_pool(DATABASE_URL)

async def ensure_column(db: aiosqlite.Connection, table: str, column: str, definition: str) -> None:
    cur = await db.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in await cur.fetchall()]
    if column not in columns:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

async def init_db() -> None:
    if DATABASE_URL:
        if not _pg_pool:
            await init_pool()
        async with _pg_pool.acquire() as conn:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                lang VARCHAR NOT NULL DEFAULT 'ru',
                name VARCHAR,
                phone VARCHAR,
                contact VARCHAR,
                no_show_count INTEGER NOT NULL DEFAULT 0,
                first_visit_bonus_used INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS services (
                id VARCHAR PRIMARY KEY,
                title_ru VARCHAR NOT NULL,
                title_ua VARCHAR NOT NULL,
                duration_minutes INTEGER NOT NULL,
                price_eur INTEGER NOT NULL,
                is_package INTEGER NOT NULL DEFAULT 0,
                package_sessions INTEGER
            );
            CREATE TABLE IF NOT EXISTS packages (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                sessions_total INTEGER NOT NULL,
                sessions_used INTEGER NOT NULL DEFAULT 0,
                package_paid INTEGER NOT NULL DEFAULT 0,
                bonus_used INTEGER NOT NULL DEFAULT 0,
                expires_at VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                service_id VARCHAR NOT NULL REFERENCES services(id),
                starts_at VARCHAR NOT NULL,
                ends_at VARCHAR NOT NULL,
                duration_minutes INTEGER NOT NULL,
                price_eur INTEGER NOT NULL,
                status VARCHAR NOT NULL DEFAULT 'booked',
                source VARCHAR NOT NULL DEFAULT 'telegram_bot',
                google_event_id VARCHAR,
                reminder_sent INTEGER NOT NULL DEFAULT 0,
                review_sent INTEGER NOT NULL DEFAULT 0,
                followup_7d_sent INTEGER NOT NULL DEFAULT 0,
                followup_30d_sent INTEGER NOT NULL DEFAULT 0,
                first_visit_bonus_applied INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            await conn.execute("""
            ALTER TABLE clients ADD COLUMN IF NOT EXISTS no_show_count INTEGER NOT NULL DEFAULT 0;
            """)
            await conn.execute("""
            INSERT INTO services (id, title_ru, title_ua, duration_minutes, price_eur, is_package, package_sessions)
            VALUES 
                ('classic_back', 'Классический массаж спины - 45 мин - 20€', 'Класичний масаж спини - 45 хв - 20€', 45, 20, 0, NULL),
                ('classic_back_package_5', 'Классический массаж спины - курс 5 сеансов - 90€', 'Класичний масаж спини - курс 5 сеансів - 90€', 45, 90, 1, 5),
                ('classic_back_package_10', 'Классический массаж спины - курс 10 сеансов - 175€', 'Класичний масаж спини - курс 10 сеансів - 175€', 45, 175, 1, 10),
                ('child_wellness', 'Детский велнес-массаж - 30 мин - 15€', 'Дитячий велнес-масаж - 30 хв - 15€', 30, 15, 0, NULL),
                ('child_wellness_package_5', 'Детский велнес-массаж - курс 5 сеансов - 60€', 'Дитячий велнес-масаж - курс 5 сеансів - 60€', 30, 60, 1, 5),
                ('child_wellness_package_10', 'Детский велнес-массаж - курс 10 сеансов - 130€', 'Дитячий велнес-масаж - курс 10 сеансів - 130€', 30, 130, 1, 10),
                ('general', 'Общий массаж - 90 мин - 70€', 'Загальний масаж - 90 хв - 70€', 90, 70, 0, NULL),
                ('general_package_5', 'Общий массаж - курс 5 сеансов - 180€', 'Загальний масаж - курс 5 сеансів - 180€', 90, 180, 1, 5),
                ('general_package_10', 'Общий массаж - курс 10 сеансов - 350€', 'Загальний масаж - курс 10 сеансів - 350€', 90, 350, 1, 10),
                ('anti_cellulite', 'Антицеллюлитный массаж - 45 мин - 30€', 'Антицелюлітний масаж - 45 хв - 30€', 45, 30, 0, NULL),
                ('anti_cellulite_package_5', 'Антицеллюлитный массаж - курс 5 сеансов - 135€', 'Антицелюлітний масаж - курс 5 сеансів - 135€', 45, 135, 1, 5),
                ('anti_cellulite_package_10', 'Антицеллюлитный массаж - курс 10 сеансов - 260€', 'Антицелюлітний масаж - курс 10 сеансів - 260€', 45, 260, 1, 10),
                ('sport', 'Спортивный массаж - 45 мин - 30€', 'Спортивний масаж - 45 хв - 30€', 45, 30, 0, NULL),
                ('sport_package_5', 'Спортивный массаж - курс 5 сеансов - 135€', 'Спортивний масаж - курс 5 сеансів - 135€', 45, 135, 1, 5),
                ('sport_package_10', 'Спортивный массаж - курс 10 сеансов - 260€', 'Спортивний масаж - курс 10 сеансів - 260€', 45, 260, 1, 10),
                ('relax', 'Релакс-массаж - 45 мин - 20€', 'Релакс-масаж - 45 хв - 20€', 45, 20, 0, NULL),
                ('relax_package_5', 'Релакс-массаж - курс 5 сеансов - 90€', 'Релакс-масаж - курс 5 сеансів - 90€', 45, 90, 1, 5),
                ('relax_package_10', 'Релакс-массаж - курс 10 сеансов - 175€', 'Релакс-масаж - курс 10 сеансів - 175€', 45, 175, 1, 10)
            ON CONFLICT (id) DO UPDATE SET 
                title_ru = EXCLUDED.title_ru,
                title_ua = EXCLUDED.title_ua,
                duration_minutes = EXCLUDED.duration_minutes,
                price_eur = EXCLUDED.price_eur,
                is_package = EXCLUDED.is_package,
                package_sessions = EXCLUDED.package_sessions;
            """)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                lang TEXT NOT NULL DEFAULT 'ru',
                name TEXT,
                phone TEXT,
                contact TEXT,
                no_show_count INTEGER NOT NULL DEFAULT 0,
                first_visit_bonus_used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                title_ru TEXT NOT NULL,
                title_ua TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                price_eur INTEGER NOT NULL,
                is_package INTEGER NOT NULL DEFAULT 0,
                package_sessions INTEGER
            );
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                sessions_total INTEGER NOT NULL,
                sessions_used INTEGER NOT NULL DEFAULT 0,
                package_paid INTEGER NOT NULL DEFAULT 0,
                bonus_used INTEGER NOT NULL DEFAULT 0,
                expires_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                service_id TEXT NOT NULL,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                price_eur INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'booked',
                source TEXT NOT NULL DEFAULT 'telegram_bot',
                google_event_id TEXT,
                reminder_sent INTEGER NOT NULL DEFAULT 0,
                review_sent INTEGER NOT NULL DEFAULT 0,
                followup_7d_sent INTEGER NOT NULL DEFAULT 0,
                followup_30d_sent INTEGER NOT NULL DEFAULT 0,
                first_visit_bonus_applied INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(service_id) REFERENCES services(id)
            );
            """)
            await ensure_column(db, "appointments", "followup_7d_sent", "INTEGER NOT NULL DEFAULT 0")
            await ensure_column(db, "appointments", "followup_30d_sent", "INTEGER NOT NULL DEFAULT 0")
            await ensure_column(db, "clients", "contact", "TEXT")
            await ensure_column(db, "clients", "no_show_count", "INTEGER NOT NULL DEFAULT 0")
            await db.executemany(
                """
                INSERT OR REPLACE INTO services
                (id, title_ru, title_ua, duration_minutes, price_eur, is_package, package_sessions)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("classic_back", "Классический массаж спины - 45 мин - 20€", "Класичний масаж спини - 45 хв - 20€", 45, 20, 0, None),
                    ("classic_back_package_5", "Классический массаж спины - курс 5 сеансов - 90€", "Класичний масаж спини - курс 5 сеансів - 90€", 45, 90, 1, 5),
                    ("classic_back_package_10", "Классический массаж спины - курс 10 сеансов - 175€", "Класичний масаж спини - курс 10 сеансів - 175€", 45, 175, 1, 10),
                    ("child_wellness", "Детский велнес-массаж - 30 мин - 15€", "Дитячий велнес-масаж - 30 хв - 15€", 30, 15, 0, None),
                    ("child_wellness_package_5", "Детский велнес-массаж - курс 5 сеансов - 60€", "Дитячий велнес-масаж - курс 5 сеансів - 60€", 30, 60, 1, 5),
                    ("child_wellness_package_10", "Детский велнес-массаж - курс 10 сеансов - 130€", "Дитячий велнес-масаж - курс 10 сеансів - 130€", 30, 130, 1, 10),
                    ("general", "Общий массаж - 90 мин - 70€", "Загальний масаж - 90 хв - 70€", 90, 70, 0, None),
                    ("general_package_5", "Общий массаж - курс 5 сеансов - 180€", "Загальний масаж - курс 5 сеансів - 180€", 90, 180, 1, 5),
                    ("general_package_10", "Общий массаж - курс 10 сеансов - 350€", "Загальний масаж - курс 10 сеансів - 350€", 90, 350, 1, 10),
                    ("anti_cellulite", "Антицеллюлитный массаж - 45 мин - 30€", "Антицелюлітний масаж - 45 хв - 30€", 45, 30, 0, None),
                    ("anti_cellulite_package_5", "Антицеллюлитный массаж - курс 5 сеансов - 135€", "Антицелюлітний масаж - курс 5 сеансів - 135€", 45, 135, 1, 5),
                    ("anti_cellulite_package_10", "Антицеллюлитный массаж - курс 10 сеансов - 260€", "Антицелюлітний масаж - курс 10 сеансів - 260€", 45, 260, 1, 10),
                    ("sport", "Спортивный массаж - 45 мин - 30€", "Спортивний масаж - 45 хв - 30€", 45, 30, 0, None),
                    ("sport_package_5", "Спортивный массаж - курс 5 сеансов - 135€", "Спортивний масаж - курс 5 сеансів - 135€", 45, 135, 1, 5),
                    ("sport_package_10", "Спортивный массаж - курс 10 сеансов - 260€", "Спортивний масаж - курс 10 сеансів - 260€", 45, 260, 1, 10),
                    ("relax", "Релакс-массаж - 45 мин - 20€", "Релакс-масаж - 45 хв - 20€", 45, 20, 0, None),
                    ("relax_package_5", "Релакс-массаж - курс 5 сеансов - 90€", "Релакс-масаж - курс 5 сеансів - 90€", 45, 90, 1, 5),
                    ("relax_package_10", "Релакс-массаж - курс 10 сеансов - 175€", "Релакс-масаж - курс 10 сеансів - 175€", 45, 175, 1, 10),
                ],
            )
            await db.commit()

async def db_ensure_client(telegram_id: int, lang: str = "ru") -> DBRow:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("INSERT INTO clients (telegram_id, lang) VALUES ($1, $2) ON CONFLICT (telegram_id) DO NOTHING", telegram_id, lang)
            row = await conn.fetchrow("SELECT * FROM clients WHERE telegram_id = $1", telegram_id)
            if not row: raise RuntimeError("Client was not created")
            return DBRow(dict(row))
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("INSERT OR IGNORE INTO clients (telegram_id, lang) VALUES (?, ?)", (telegram_id, lang))
            await db.commit()
            cur = await db.execute("SELECT * FROM clients WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            if not row: raise RuntimeError("Client was not created")
            return DBRow(dict(row))

async def db_update_client_lang(telegram_id: int, lang: str) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE clients SET lang = $1 WHERE telegram_id = $2", lang, telegram_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE clients SET lang = ? WHERE telegram_id = ?", (lang, telegram_id))
            await db.commit()

async def db_update_client_profile(telegram_id: int, name: str, contact: str) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE clients SET name = $1, phone = $2, contact = $3 WHERE telegram_id = $4", name, contact, contact, telegram_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE clients SET name = ?, phone = ?, contact = ? WHERE telegram_id = ?", (name, contact, contact, telegram_id))
            await db.commit()

async def db_get_services(exclude_packages: bool = False) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            if exclude_packages:
                rows = await conn.fetch("SELECT * FROM services WHERE is_package = 0 ORDER BY duration_minutes, price_eur")
            else:
                rows = await conn.fetch("SELECT * FROM services ORDER BY is_package, duration_minutes")
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            if exclude_packages:
                cur = await db.execute("SELECT * FROM services WHERE is_package = 0 ORDER BY duration_minutes, price_eur")
            else:
                cur = await db.execute("SELECT * FROM services ORDER BY is_package, duration_minutes")
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]

async def db_get_service(service_id: str) -> DBRow | None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM services WHERE id = $1", service_id)
            return DBRow(dict(row)) if row else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM services WHERE id = ?", (service_id,))
            row = await cur.fetchone()
            return DBRow(dict(row)) if row else None

async def db_create_appointment(client_id: int, service_id: str, starts_at: str, ends_at: str, duration_minutes: int, price_eur: int, source: str, first_visit_bonus_applied: int) -> int:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO appointments
                (client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
                """,
                client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied
            )
            return row["id"]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                """
                INSERT INTO appointments
                (client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied)
            )
            await db.commit()
            return cur.lastrowid


async def db_create_booking_atomic(
    client_id: int,
    service_id: str,
    starts_at: str,
    ends_at: str,
    duration_minutes: int,
    price_eur: int,
    source: str,
    first_visit_bonus_applied: int,
    *,
    package_sessions: int | None = None,
    package_expires_at: str | None = None,
) -> int:
    """
    Atomically insert the appointment row, optionally create the package row,
    and mark the first-visit bonus as used — all inside a single transaction.
    Returns the new appointment id.  Rolls back everything on any failure.
    """
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO appointments
                    (client_id, service_id, starts_at, ends_at, duration_minutes,
                     price_eur, source, first_visit_bonus_applied)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
                    """,
                    client_id, service_id, starts_at, ends_at, duration_minutes,
                    price_eur, source, first_visit_bonus_applied,
                )
                appointment_id = row["id"]
                if package_sessions is not None and package_expires_at is not None:
                    await conn.execute(
                        "INSERT INTO packages (client_id, sessions_total, package_paid, expires_at)"
                        " VALUES ($1, $2, 0, $3)",
                        client_id, package_sessions, package_expires_at,
                    )
                if first_visit_bonus_applied:
                    await conn.execute(
                        "UPDATE clients SET first_visit_bonus_used = 1 WHERE id = $1",
                        client_id,
                    )
                return appointment_id
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                cur = await db.execute(
                    """
                    INSERT INTO appointments
                    (client_id, service_id, starts_at, ends_at, duration_minutes,
                     price_eur, source, first_visit_bonus_applied)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (client_id, service_id, starts_at, ends_at, duration_minutes,
                     price_eur, source, first_visit_bonus_applied),
                )
                appointment_id = cur.lastrowid
                if package_sessions is not None and package_expires_at is not None:
                    await db.execute(
                        "INSERT INTO packages (client_id, sessions_total, package_paid, expires_at)"
                        " VALUES (?, ?, 0, ?)",
                        (client_id, package_sessions, package_expires_at),
                    )
                if first_visit_bonus_applied:
                    await db.execute(
                        "UPDATE clients SET first_visit_bonus_used = 1 WHERE id = ?",
                        (client_id,),
                    )
                await db.commit()
                return appointment_id
            except Exception:
                await db.rollback()
                raise

async def db_reschedule_atomic(
    old_appointment_id: int,
    client_id: int,
    service_id: str,
    starts_at: str,
    ends_at: str,
    duration_minutes: int,
    price_eur: int,
    source: str,
    first_visit_bonus_applied: int,
) -> int:
    """
    Atomically mark the old appointment as 'rescheduled' and insert the new
    appointment row — both in a single transaction.
    Returns the new appointment id.  Rolls back everything on any failure,
    so the DB never ends up with the old booking cancelled but no new one.
    """
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE appointments SET status = 'rescheduled' WHERE id = $1",
                    old_appointment_id,
                )
                row = await conn.fetchrow(
                    """
                    INSERT INTO appointments
                    (client_id, service_id, starts_at, ends_at, duration_minutes,
                     price_eur, source, first_visit_bonus_applied)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
                    """,
                    client_id, service_id, starts_at, ends_at, duration_minutes,
                    price_eur, source, first_visit_bonus_applied,
                )
                return row["id"]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute(
                    "UPDATE appointments SET status = 'rescheduled' WHERE id = ?",
                    (old_appointment_id,),
                )
                cur = await db.execute(
                    """
                    INSERT INTO appointments
                    (client_id, service_id, starts_at, ends_at, duration_minutes,
                     price_eur, source, first_visit_bonus_applied)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (client_id, service_id, starts_at, ends_at, duration_minutes,
                     price_eur, source, first_visit_bonus_applied),
                )
                new_appointment_id = cur.lastrowid
                await db.commit()
                return new_appointment_id
            except Exception:
                await db.rollback()
                raise


async def db_update_appointment_google_event_id(appointment_id: int, google_event_id: str) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE appointments SET google_event_id = $1 WHERE id = $2", google_event_id, appointment_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE appointments SET google_event_id = ? WHERE id = ?", (google_event_id, appointment_id))
            await db.commit()

async def db_update_appointment_status(appointment_id: int, status: str) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE appointments SET status = $1 WHERE id = $2", status, appointment_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
            await db.commit()

async def db_update_appointment_time(appointment_id: int, starts_at: str, ends_at: str) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE appointments SET starts_at = $1, ends_at = $2 WHERE id = $3",
                starts_at,
                ends_at,
                appointment_id,
            )
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE appointments SET starts_at = ?, ends_at = ? WHERE id = ?",
                (starts_at, ends_at, appointment_id),
            )
            await db.commit()

async def db_increment_client_no_show_count(client_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE clients SET no_show_count = no_show_count + 1 WHERE id = $1", client_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE clients SET no_show_count = no_show_count + 1 WHERE id = ?", (client_id,))
            await db.commit()

async def db_get_active_bookings(client_id: int, min_starts_at: str | None = None) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            if min_starts_at:
                rows = await conn.fetch(
                    """
                    SELECT a.*, s.title_ru, s.title_ua, s.is_package, s.package_sessions
                    FROM appointments a
                    JOIN services s ON s.id = a.service_id
                    WHERE a.client_id = $1 AND a.status = 'booked' AND a.starts_at >= $2
                    ORDER BY a.starts_at
                    """, client_id, min_starts_at
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT a.*, s.title_ru, s.title_ua, s.is_package, s.package_sessions
                    FROM appointments a
                    JOIN services s ON s.id = a.service_id
                    WHERE a.client_id = $1 AND a.status = 'booked'
                    ORDER BY a.starts_at
                    """, client_id
                )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            if min_starts_at:
                cur = await db.execute(
                    """
                    SELECT a.*, s.title_ru, s.title_ua, s.is_package, s.package_sessions
                    FROM appointments a
                    JOIN services s ON s.id = a.service_id
                    WHERE a.client_id = ? AND a.status = 'booked' AND a.starts_at >= ?
                    ORDER BY a.starts_at
                    """, (client_id, min_starts_at)
                )
            else:
                cur = await db.execute(
                    """
                    SELECT a.*, s.title_ru, s.title_ua, s.is_package, s.package_sessions
                    FROM appointments a
                    JOIN services s ON s.id = a.service_id
                    WHERE a.client_id = ? AND a.status = 'booked'
                    ORDER BY a.starts_at
                    """, (client_id,)
                )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]

async def db_get_client_appointment(appointment_id: int, client_id: int) -> DBRow | None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM appointments WHERE id = $1 AND client_id = $2 AND status = 'booked'", appointment_id, client_id)
            return DBRow(dict(row)) if row else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM appointments WHERE id = ? AND client_id = ? AND status = 'booked'", (appointment_id, client_id))
            row = await cur.fetchone()
            return DBRow(dict(row)) if row else None

async def db_get_appointment_admin_summary_data(appointment_id: int) -> DBRow | None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT a.starts_at, a.duration_minutes, a.price_eur, a.status, c.name, c.phone, c.contact, c.telegram_id, s.title_ru
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.id = $1
                """, appointment_id
            )
            return DBRow(dict(row)) if row else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.starts_at, a.duration_minutes, a.price_eur, a.status, c.name, c.phone, c.contact, c.telegram_id, s.title_ru
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.id = ?
                """, (appointment_id,)
            )
            row = await cur.fetchone()
            return DBRow(dict(row)) if row else None

async def db_get_active_package(client_id: int) -> DBRow | None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM packages
                WHERE client_id = $1 AND package_paid = 1 AND sessions_used < sessions_total
                ORDER BY created_at DESC
                LIMIT 1
                """, client_id
            )
            return DBRow(dict(row)) if row else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT * FROM packages
                WHERE client_id = ? AND package_paid = 1 AND sessions_used < sessions_total
                ORDER BY created_at DESC
                LIMIT 1
                """, (client_id,)
            )
            row = await cur.fetchone()
            return DBRow(dict(row)) if row else None

async def db_create_package(client_id: int, sessions_total: int, expires_at: str) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO packages (client_id, sessions_total, package_paid, expires_at) VALUES ($1, $2, 0, $3)",
                client_id, sessions_total, expires_at
            )
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO packages (client_id, sessions_total, package_paid, expires_at) VALUES (?, ?, 0, ?)",
                (client_id, sessions_total, expires_at)
            )
            await db.commit()

async def db_get_appointments_today() -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.*, c.name, c.phone, c.contact, c.telegram_id, s.title_ru
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE DATE(a.starts_at) = CURRENT_DATE
                ORDER BY a.starts_at
                """
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.*, c.name, c.phone, c.contact, c.telegram_id, s.title_ru
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE date(a.starts_at) = date('now', 'localtime')
                ORDER BY a.starts_at
                """
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]

async def db_get_appointment_with_client(appointment_id: int) -> DBRow | None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT a.*, c.telegram_id, c.lang, c.name, c.phone, c.contact, c.first_visit_bonus_used, c.id AS client_id,
                       s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.id = $1
                """, appointment_id
            )
            return DBRow(dict(row)) if row else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.*, c.telegram_id, c.lang, c.name, c.phone, c.contact, c.first_visit_bonus_used, c.id AS client_id,
                       s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.id = ?
                """, (appointment_id,)
            )
            row = await cur.fetchone()
            return DBRow(dict(row)) if row else None

async def db_mark_first_visit_bonus_used(client_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE clients SET first_visit_bonus_used = 1 WHERE id = $1", client_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE clients SET first_visit_bonus_used = 1 WHERE id = ?", (client_id,))
            await db.commit()

async def db_increment_package_sessions(package_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE packages SET sessions_used = sessions_used + 1 WHERE id = $1", package_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE packages SET sessions_used = sessions_used + 1 WHERE id = ?", (package_id,))
            await db.commit()

async def db_mark_review_sent(appointment_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE appointments SET review_sent = 1 WHERE id = $1", appointment_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE appointments SET review_sent = 1 WHERE id = ?", (appointment_id,))
            await db.commit()

async def db_get_google_event_id(appointment_id: int) -> str | None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT google_event_id FROM appointments WHERE id = $1", appointment_id)
            return row["google_event_id"] if row else None
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT google_event_id FROM appointments WHERE id = ?", (appointment_id,))
            row = await cur.fetchone()
            return row["google_event_id"] if row else None

async def db_first_visit_bonus_available(client_id: int) -> bool:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT first_visit_bonus_used FROM clients WHERE id = $1", client_id)
            return not bool(row["first_visit_bonus_used"]) if row else True
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT first_visit_bonus_used FROM clients WHERE id = ?", (client_id,))
            row = await cur.fetchone()
            return not bool(row["first_visit_bonus_used"]) if row else True

async def db_get_booked_appointments_for_day(day_iso: str) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT starts_at, ends_at FROM appointments
                WHERE starts_at LIKE $1 AND status = 'booked'
                """, day_iso + '%'
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT starts_at, ends_at FROM appointments
                WHERE date(starts_at) = date(?)
                AND status = 'booked'
                """, (day_iso,)
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]


async def db_get_pending_reminders(lower_iso: str, upper_iso: str) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, a.starts_at, a.duration_minutes,
                       c.telegram_id, c.lang, s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.status = 'booked'
                AND a.reminder_sent = 0
                AND a.starts_at BETWEEN $1 AND $2
                """,
                lower_iso, upper_iso
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.id, a.starts_at, a.duration_minutes,
                       c.telegram_id, c.lang, s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.status = 'booked'
                AND a.reminder_sent = 0
                AND a.starts_at BETWEEN ? AND ?
                """,
                (lower_iso, upper_iso),
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]


async def db_mark_reminder_sent(appointment_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE appointments SET reminder_sent = 1 WHERE id = $1", appointment_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE appointments SET reminder_sent = 1 WHERE id = ?", (appointment_id,))
            await db.commit()


async def db_get_pending_followups_7d(before_iso: str) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, c.telegram_id, c.lang
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                WHERE a.status = 'completed'
                AND a.followup_7d_sent = 0
                AND a.starts_at <= $1
                """,
                before_iso
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.id, c.telegram_id, c.lang
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                WHERE a.status = 'completed'
                AND a.followup_7d_sent = 0
                AND a.starts_at <= ?
                """,
                (before_iso,),
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]


async def db_mark_followup_7d_sent(appointment_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE appointments SET followup_7d_sent = 1 WHERE id = $1", appointment_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE appointments SET followup_7d_sent = 1 WHERE id = ?", (appointment_id,))
            await db.commit()


async def db_get_pending_followups_30d(before_iso: str) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, c.telegram_id, c.lang
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                WHERE a.status = 'completed'
                AND a.followup_30d_sent = 0
                AND a.starts_at <= $1
                AND NOT EXISTS (
                    SELECT 1 FROM appointments newer
                    WHERE newer.client_id = a.client_id
                    AND newer.status IN ('booked', 'completed')
                    AND newer.starts_at > a.starts_at
                )
                """,
                before_iso
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.id, c.telegram_id, c.lang
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                WHERE a.status = 'completed'
                AND a.followup_30d_sent = 0
                AND a.starts_at <= ?
                AND NOT EXISTS (
                    SELECT 1 FROM appointments newer
                    WHERE newer.client_id = a.client_id
                    AND newer.status IN ('booked', 'completed')
                    AND newer.starts_at > a.starts_at
                )
                """,
                (before_iso,),
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]


async def db_mark_followup_30d_sent(appointment_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE appointments SET followup_30d_sent = 1 WHERE id = $1", appointment_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE appointments SET followup_30d_sent = 1 WHERE id = ?", (appointment_id,))
            await db.commit()


async def db_get_expired_packages(today_iso: str) -> list[DBRow]:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id FROM packages
                WHERE expires_at IS NOT NULL
                AND expires_at < $1
                AND sessions_used < sessions_total
                """,
                today_iso
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT id FROM packages
                WHERE expires_at IS NOT NULL
                AND expires_at < ?
                AND sessions_used < sessions_total
                """,
                (today_iso,),
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]


async def db_expire_package(package_id: int) -> None:
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            await conn.execute("UPDATE packages SET sessions_used = sessions_total WHERE id = $1", package_id)
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE packages SET sessions_used = sessions_total WHERE id = ?", (package_id,))
            await db.commit()


async def db_get_booked_appointments_for_date(day_iso: str) -> list[DBRow]:
    """Return booked appointments for one local calendar date YYYY-MM-DD."""
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.*, c.name, c.phone, c.contact, c.telegram_id, c.lang, s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.status = 'booked'
                AND a.starts_at::date = $1::date
                ORDER BY a.starts_at::timestamptz
                """,
                day_iso,
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.*, c.name, c.phone, c.contact, c.telegram_id, c.lang, s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.status = 'booked'
                AND date(a.starts_at) = date(?)
                ORDER BY a.starts_at
                """,
                (day_iso,),
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]


async def db_get_upcoming_booked_appointments(from_iso: str, limit: int = 20) -> list[DBRow]:
    """Return upcoming booked appointments from a local ISO datetime string."""
    if DATABASE_URL:
        async with _pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.*, c.name, c.phone, c.contact, c.telegram_id, c.lang, s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.status = 'booked'
                AND a.starts_at::timestamptz >= $1::timestamptz
                ORDER BY a.starts_at::timestamptz
                LIMIT $2
                """,
                from_iso,
                limit,
            )
            return [DBRow(dict(r)) for r in rows]
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                """
                SELECT a.*, c.name, c.phone, c.contact, c.telegram_id, c.lang, s.title_ru, s.title_ua
                FROM appointments a
                JOIN clients c ON c.id = a.client_id
                JOIN services s ON s.id = a.service_id
                WHERE a.status = 'booked'
                AND datetime(a.starts_at) >= datetime(?)
                ORDER BY datetime(a.starts_at)
                LIMIT ?
                """,
                (from_iso, limit),
            )
            rows = await cur.fetchall()
            return [DBRow(dict(r)) for r in rows]
