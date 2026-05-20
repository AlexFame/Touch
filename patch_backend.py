import re

with open("backend/main.py", "r") as f:
    code = f.read()

code = code.replace(
    "from app.database import ensure_client, fetchall, fetchone, update_client_profile, execute",
    "from app.database import db_ensure_client, db_get_services, db_get_service, db_update_client_profile, db_get_active_bookings, db_create_appointment, db_update_appointment_google_event_id, db_update_appointment_status, init_pool"
)

code = code.replace("app.mount(", """@app.on_event("startup")
async def startup_event():
    await init_pool()

app.mount(""")

code = code.replace("client = await ensure_client(telegram_id)", "client = await db_ensure_client(telegram_id)")

code = code.replace(
    'rows = await fetchall("SELECT * FROM services WHERE is_package = 0 ORDER BY duration_minutes, price_eur")',
    'rows = await db_get_services(exclude_packages=True)'
)

code = code.replace(
    'row = await fetchone("SELECT * FROM services WHERE id = ?", (payload.service_id,))',
    'row = await db_get_service(payload.service_id)'
)

code = code.replace(
    'await update_client_profile(telegram_id, payload.name, payload.contact)',
    'await db_update_client_profile(telegram_id, payload.name, payload.contact)'
)

code = code.replace(
    'appointment_id = await execute(\n        """\n        INSERT INTO appointments\n        (client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied)\n        VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n        """,\n        (client["id"], service["id"], starts_at, ends_at, duration, service["price_eur"], "telegram_webapp", first_bonus),\n    )',
    'appointment_id = await db_create_appointment(client["id"], service["id"], starts_at, ends_at, duration, service["price_eur"], "telegram_webapp", first_bonus)'
)

code = code.replace(
    'await execute("UPDATE appointments SET google_event_id = ? WHERE id = ?", (event_id, appointment_id))',
    'await db_update_appointment_google_event_id(appointment_id, event_id)'
)

code = code.replace(
    'await execute("UPDATE appointments SET google_event_id = ? WHERE id = ?", (event_id, new_appointment_id))',
    'await db_update_appointment_google_event_id(new_appointment_id, event_id)'
)

code = code.replace(
    'await execute("UPDATE appointments SET status = \'cancelled\' WHERE id = ?", (appointment_id,))',
    'await db_update_appointment_status(appointment_id, "cancelled")'
)

code = code.replace(
    'await execute("UPDATE appointments SET status = \'rescheduled\' WHERE id = ?", (appointment_id,))',
    'await db_update_appointment_status(appointment_id, "rescheduled")'
)

code = re.sub(
    r'rows = await fetchall\(\s*"""\s*SELECT a\.\*, s\.title_ru, s\.title_ua\s*FROM appointments a\s*JOIN services s ON s\.id = a\.service_id\s*WHERE a\.client_id = \? AND a\.status = \'booked\'\s*ORDER BY a\.starts_at\s*""",\s*\(client\["id"\],\),\s*\)',
    r'rows = await db_get_active_bookings(client["id"])',
    code
)

code = re.sub(
    r'rows = await fetchall\(\s*"""\s*SELECT a\.\*, s\.title_ru, s\.title_ua\s*FROM appointments a\s*JOIN services s ON s\.id = a\.service_id\s*WHERE a\.client_id = \? AND a\.status = \'booked\' AND a\.starts_at >= \?\s*ORDER BY a\.starts_at\s*""",\s*\(client\["id"\], now_iso\),\s*\)',
    r'rows = await db_get_active_bookings(client["id"], now_iso)',
    code
)

code = code.replace(
    'old_row = await fetchone("SELECT * FROM appointments WHERE id = ? AND client_id = ? AND status = \'booked\'", (appointment_id, client["id"]))',
    'old_row = await db_get_client_appointment(appointment_id, client["id"])'
)

code = code.replace('from app.database import db_ensure_client', 'from app.database import db_ensure_client, db_get_client_appointment')

with open("backend/main.py", "w") as f:
    f.write(code)

