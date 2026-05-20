with open("backend/main.py", "r") as f:
    code = f.read()

code = code.replace(
    'row = await fetchone("SELECT * FROM appointments WHERE id = ? AND client_id = ? AND status = \'booked\'", (appointment_id, client["id"]))',
    'row = await db_get_client_appointment(appointment_id, client["id"])'
)

code = code.replace(
    'service = await fetchone("SELECT * FROM services WHERE id = ?", (payload.service_id,))',
    'service = await db_get_service(payload.service_id)'
)

code = code.replace(
    'await execute("UPDATE appointments SET google_event_id = ? WHERE id = ?", (google_event_id, new_appointment_id))',
    'await db_update_appointment_google_event_id(new_appointment_id, google_event_id)'
)

code = code.replace(
    'new_appointment_id = await execute(\n        """\n        INSERT INTO appointments\n        (client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied)\n        VALUES (?, ?, ?, ?, ?, ?, ?, ?)\n        """,\n        (client["id"], service["id"], start.isoformat(), end.isoformat(), duration, service["price_eur"], "telegram_miniapp", int(first_bonus))\n    )',
    'new_appointment_id = await db_create_appointment(client["id"], service["id"], start.isoformat(), end.isoformat(), duration, service["price_eur"], "telegram_miniapp", int(first_bonus))'
)

with open("backend/main.py", "w") as f:
    f.write(code)

