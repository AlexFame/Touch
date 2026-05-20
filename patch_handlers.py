import re

with open("app/handlers.py", "r") as f:
    code = f.read()

code = code.replace(
    'from app.database import ensure_client, execute, fetchall, fetchone, update_client_lang, update_client_profile',
    'from app.database import db_ensure_client, db_update_client_lang, db_update_client_profile, db_get_services, db_get_service, db_create_appointment, db_update_appointment_google_event_id, db_create_package, db_get_client_appointment, db_update_appointment_status, db_get_appointments_today, db_get_appointment_with_client, db_mark_first_visit_bonus_used, db_increment_package_sessions, db_mark_review_sent, db_get_google_event_id, db_get_active_bookings, db_get_active_package, db_get_appointment_admin_summary_data'
)

code = code.replace('await ensure_client', 'await db_ensure_client')
code = code.replace('await update_client_lang', 'await db_update_client_lang')
code = code.replace('await update_client_profile', 'await db_update_client_profile')

code = code.replace(
    'await fetchall("SELECT * FROM services ORDER BY is_package, duration_minutes")',
    'await db_get_services()'
)
code = code.replace(
    'await fetchall("SELECT * FROM services WHERE is_package = 0 ORDER BY duration_minutes, price_eur")',
    'await db_get_services(exclude_packages=True)'
)
code = re.sub(
    r'await fetchone\("SELECT \* FROM services WHERE id = \?", \((\w+),\)\)',
    r'await db_get_service(\1)',
    code
)

code = code.replace(
    'await execute("UPDATE appointments SET status = \'cancelled\' WHERE id = ?", (appointment_id,))',
    'await db_update_appointment_status(appointment_id, "cancelled")'
)
code = code.replace(
    'await execute("UPDATE appointments SET status = \'rescheduled\' WHERE id = ?", (reschedule_appointment_id,))',
    'await db_update_appointment_status(reschedule_appointment_id, "rescheduled")'
)

code = re.sub(
    r'await fetchone\("SELECT google_event_id FROM appointments WHERE id = \?", \((\w+),\)\)',
    r'{"google_event_id": await db_get_google_event_id(\1)}',
    code
)

code = code.replace(
    'await execute("UPDATE appointments SET status = \'completed\' WHERE id = ?", (appointment_id,))',
    'await db_update_appointment_status(appointment_id, "completed")'
)
code = code.replace(
    'await execute("UPDATE appointments SET status = \'no_show\' WHERE id = ?", (appointment_id,))',
    'await db_update_appointment_status(appointment_id, "no_show")'
)
code = code.replace(
    'await execute("UPDATE clients SET first_visit_bonus_used = 1 WHERE id = ?", (client_id,))',
    'await db_mark_first_visit_bonus_used(client_id)'
)
code = code.replace(
    'await execute("UPDATE packages SET sessions_used = sessions_used + 1 WHERE id = ?", (package_id,))',
    'await db_increment_package_sessions(package_id)'
)
code = code.replace(
    'await execute("UPDATE appointments SET review_sent = 1 WHERE id = ?", (appointment_id,))',
    'await db_mark_review_sent(appointment_id)'
)

# Replace the giant fetchone block in get_appointment_admin_summary
code = re.sub(
    r'row = await fetchone\(\s*"""\s*SELECT a\.starts_at, a\.duration_minutes, a\.price_eur, c\.name, c\.phone, c\.contact, c\.telegram_id, s\.title_ru\s*FROM appointments a\s*JOIN clients c ON c\.id = a\.client_id\s*JOIN services s ON s\.id = a\.service_id\s*WHERE a\.id = \?\s*""",\s*\(appointment_id,\),\s*\)',
    r'row = await db_get_appointment_admin_summary_data(appointment_id)',
    code
)

code = re.sub(
    r'row = await fetchone\(\s*"""\s*SELECT \* FROM packages\s*WHERE client_id = \? AND package_paid = 1 AND sessions_used < sessions_total\s*ORDER BY created_at DESC\s*LIMIT 1\s*""",\s*\(client\["id"\],\),\s*\)',
    r'row = await db_get_active_package(client["id"])',
    code
)

code = re.sub(
    r'appointment_id = await execute\(\s*"""\s*INSERT INTO appointments\s*\(client_id, service_id, starts_at, ends_at, duration_minutes, price_eur, source, first_visit_bonus_applied\)\s*VALUES \(\?, \?, \?, \?, \?, \?, \?, \?\)\s*""",\s*\(client\["id"\], service\["id"\], start\.isoformat\(\), end\.isoformat\(\), duration, service\["price_eur"\], "telegram_bot", int\(first_bonus\)\),\s*\)',
    r'appointment_id = await db_create_appointment(client["id"], service["id"], start.isoformat(), end.isoformat(), duration, service["price_eur"], "telegram_bot", int(first_bonus))',
    code
)

code = code.replace(
    'await execute("UPDATE appointments SET google_event_id = ? WHERE id = ?", (google_event_id, appointment_id))',
    'await db_update_appointment_google_event_id(appointment_id, google_event_id)'
)

code = code.replace(
    'await execute("INSERT INTO packages (client_id, sessions_total, package_paid, expires_at) VALUES (?, ?, 0, ?)", (client["id"], service["package_sessions"], expire_iso))',
    'await db_create_package(client["id"], service["package_sessions"], expire_iso)'
)

code = re.sub(
    r'row = await fetchone\("SELECT \* FROM appointments WHERE id = \? AND client_id = \? AND status = \'booked\'", \(appointment_id, client\["id"\]\)\)',
    r'row = await db_get_client_appointment(appointment_id, client["id"])',
    code
)

code = re.sub(
    r'rows = await fetchall\(\s*"""\s*SELECT a\.\*, c\.name, c\.phone, c\.contact, c\.telegram_id, s\.title_ru\s*FROM appointments a\s*JOIN clients c ON c\.id = a\.client_id\s*JOIN services s ON s\.id = a\.service_id\s*WHERE date\(a\.starts_at\) = date\(\'now\', \'localtime\'\)\s*ORDER BY a\.starts_at\s*"""\s*\)',
    r'rows = await db_get_appointments_today()',
    code
)

code = re.sub(
    r'row = await fetchone\(\s*"""\s*SELECT a\.\*, c\.telegram_id, c\.first_visit_bonus_used, c\.id AS client_id\s*FROM appointments a\s*JOIN clients c ON c\.id = a\.client_id\s*WHERE a\.id = \?\s*""",\s*\(appointment_id,\),\s*\)',
    r'row = await db_get_appointment_with_client(appointment_id)',
    code
)

code = re.sub(
    r'rows = await fetchall\(\s*"""\s*SELECT a\.\*, s\.title_ru, s\.title_ua\s*FROM appointments a\s*JOIN services s ON s\.id = a\.service_id\s*WHERE a\.client_id = \? AND a\.status = \'booked\' AND a\.starts_at >= \?\s*ORDER BY a\.starts_at\s*""",\s*\(client\["id"\], now_iso\),\s*\)',
    r'rows = await db_get_active_bookings(client["id"], now_iso)',
    code
)

with open("app/handlers.py", "w") as f:
    f.write(code)

