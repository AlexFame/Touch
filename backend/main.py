import asyncio
import hashlib
import hmac
import json
import logging
from datetime import date, datetime, timedelta
from urllib.parse import parse_qsl

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.booking import first_visit_bonus_available, get_free_slots, parse_local_datetime
from app.calendar_client import CalendarClient
from app.config import get_settings
from app.database import (
    init_db, init_pool,
    db_ensure_client, db_update_client_profile,
    db_get_services, db_get_service,
    db_create_appointment, db_create_booking_atomic,
    db_update_appointment_google_event_id, db_update_appointment_status,
    db_get_active_bookings, db_get_client_appointment, db_get_appointment_admin_summary_data,
    db_get_google_event_id,
)
from app.validation import normalize_contact, normalize_name, valid_contact, valid_name

settings = get_settings()
app = FastAPI(title="Massage Touch Mini App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
calendar = CalendarClient(settings)


class BookingCreate(BaseModel):
    service_id: str
    day_iso: str
    slot: str
    name: str = Field(min_length=1, max_length=80)
    contact: str | None = Field(default=None, max_length=40)
    phone: str | None = Field(default=None, max_length=40)
    lang: str = "ru"


class RescheduleRequest(BaseModel):
    service_id: str
    day_iso: str
    slot: str
    lang: str = "ru"


logger = logging.getLogger("uvicorn.error")


@app.on_event("startup")
async def startup() -> None:
    await init_db()
    if settings.dev_telegram_id:
        logger.warning(
            "DEV AUTH BYPASS ENABLED — all unauthenticated requests will be treated as "
            "Telegram user id=%s. Set APP_ENV=production to disable.",
            settings.dev_telegram_id,
        )
    else:
        logger.info("Dev auth bypass DISABLED (APP_ENV=%s).", settings.app_env)
    if settings.allowed_origins == ["*"]:
        logger.warning("CORS: wildcard origins allowed. Set ALLOWED_ORIGINS in production.")
    else:
        logger.info("CORS allowed origins: %s", settings.allowed_origins or "(none)")


@app.on_event("shutdown")
async def shutdown() -> None:
    await bot.session.close()


@app.get("/api/calendar/status")
async def calendar_status():
    return {
        "enabled": calendar.enabled(),
        "calendar_id": settings.google_calendar_id if calendar.enabled() else None,
        "booking_days_ahead": settings.booking_days_ahead,
    }


def verify_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=401, detail="Telegram initData is missing")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram hash is missing")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", settings.bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Telegram initData is invalid")

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="Telegram user is missing")
    return json.loads(user_raw)


def current_user(init_data: str | None = None, x_telegram_init_data: str | None = None) -> dict:
    raw = x_telegram_init_data or init_data or ""
    if raw:
        return verify_init_data(raw)
    if settings.dev_telegram_id:
        return {"id": settings.dev_telegram_id, "username": "dev_user"}
    raise HTTPException(status_code=401, detail="Open this page from Telegram Mini App")


def current_user_id(init_data: str | None = None, x_telegram_init_data: str | None = None) -> int:
    return int(current_user(init_data, x_telegram_init_data)["id"])


def service_title(row, lang: str) -> str:
    return row["title_ua"] if lang in ("ua", "uk") else row["title_ru"]


def validate_client_fields(name: str, contact: str | None) -> tuple[str, str]:
    clean_name = normalize_name(name)
    clean_contact = normalize_contact(contact)
    if not valid_name(clean_name):
        raise HTTPException(status_code=422, detail="Invalid name")
    if not valid_contact(clean_contact):
        raise HTTPException(status_code=422, detail="Invalid contact")
    return clean_name, clean_contact


@app.get("/api/me")
async def me(initData: str | None = Query(default=None), x_telegram_init_data: str | None = Header(default=None)):
    telegram_id = current_user_id(initData, x_telegram_init_data)
    client = await db_ensure_client(telegram_id)
    return {
        "telegram_id": telegram_id,
        "lang": client["lang"],
        "name": client["name"],
        "phone": client["phone"],
        "contact": client["contact"] if "contact" in client.keys() and client["contact"] else client["phone"],
        "first_visit_bonus_used": bool(client["first_visit_bonus_used"]),
    }


@app.get("/api/services")
async def services(lang: str = "ru"):
    rows = await db_get_services(exclude_packages=True)
    return [
        {
            "id": r["id"],
            "title": service_title(r, lang),
            "duration_minutes": r["duration_minutes"],
            "price_eur": r["price_eur"],
            "is_package": bool(r["is_package"]),
            "package_sessions": r["package_sessions"],
        }
        for r in rows
    ]


@app.get("/api/days")
async def days(days_count: int | None = None):
    today = datetime.now(settings.tzinfo).date()
    count = days_count or settings.booking_days_ahead
    return [{"iso": (today + timedelta(days=i)).isoformat()} for i in range(count)]


@app.get("/api/slots")
async def slots(
    service_id: str,
    day_iso: str,
    initData: str | None = Query(default=None),
    x_telegram_init_data: str | None = Header(default=None),
):
    telegram_id = current_user_id(initData, x_telegram_init_data)
    client = await db_ensure_client(telegram_id)
    service = await db_get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    first_bonus = not bool(service["is_package"]) and await first_visit_bonus_available(client["id"])
    duration = service["duration_minutes"] + (15 if first_bonus else 0)
    free = await get_free_slots(day_iso, duration, settings, calendar)
    return {"slots": free, "duration_minutes": duration, "first_visit_bonus_applied": first_bonus}


@app.post("/api/bookings")
async def create_booking(
    payload: BookingCreate,
    initData: str | None = Query(default=None),
    x_telegram_init_data: str | None = Header(default=None),
):
    user = current_user(initData, x_telegram_init_data)
    telegram_id = int(user["id"])
    username = user.get("username")
    client = await db_ensure_client(telegram_id)
    
    clean_name, final_contact = validate_client_fields(
        payload.name,
        payload.contact if payload.contact else payload.phone,
    )

    await db_update_client_profile(telegram_id, clean_name, final_contact)

    service = await db_get_service(payload.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    first_bonus = not bool(service["is_package"]) and await first_visit_bonus_available(client["id"])
    duration = service["duration_minutes"] + (15 if first_bonus else 0)
    available_slots = await get_free_slots(payload.day_iso, duration, settings, calendar)
    if payload.slot not in available_slots:
        raise HTTPException(status_code=409, detail="Slot is no longer available")

    start = parse_local_datetime(payload.day_iso, payload.slot, settings)
    end = start + timedelta(minutes=duration + settings.buffer_minutes)
    client_title = service_title(service, payload.lang)
    admin_title = service_title(service, "ru")

    summary = (
        f"Услуга: {admin_title}\n"
        f"Дата: {start.strftime('%d.%m.%Y')}\n"
        f"Время: {start.strftime('%H:%M')}\n"
        f"Длительность: {duration} мин\n"
        f"Цена: {service['price_eur']}€\n"
        f"Имя: {clean_name}"
    )
    
    if final_contact.startswith("@"):
        username_clean = final_contact[1:]
        admin_contact = f"Telegram: <a href=\"https://t.me/{username_clean}\">@{username_clean}</a>"
    elif final_contact:
        admin_contact = f"Контакт: {final_contact}\nTelegram: <a href=\"tg://user?id={telegram_id}\">открыть профиль</a>"
    else:
        if username:
            admin_contact = f"Telegram: <a href=\"https://t.me/{username}\">@{username}</a>"
        else:
            admin_contact = f"Контакт: не указан\nTelegram: <a href=\"tg://user?id={telegram_id}\">открыть профиль</a>"

    admin_summary = summary + f"\n{admin_contact}"
    
    calendar_description = (
        summary + 
        f"\nКонтакт: {final_contact or 'не указан'}" +
        f"\nTelegram ID: {telegram_id}" +
        (f"\nUsername: @{username}" if username else "")
    )
    
    if first_bonus:
        admin_summary += "\nБонус первого визита: +15 минут"
        calendar_description += "\nБонус первого визита: +15 минут"

    # All booking-related DB writes in a single transaction: appointment row,
    # optional package row, and first-visit bonus flag.  If any step fails the
    # whole thing rolls back and the client gets a clean 500.
    package_expires = (start.date() + timedelta(days=90)).isoformat() if service["is_package"] else None
    appointment_id = await db_create_booking_atomic(
        client["id"],
        service["id"],
        start.isoformat(),
        end.isoformat(),
        duration,
        service["price_eur"],
        "telegram_miniapp",
        int(first_bonus),
        package_sessions=service["package_sessions"] if service["is_package"] else None,
        package_expires_at=package_expires,
    )

    # Google Calendar is non-critical: a failure must never abort the booking
    # or skip notifications — the slot is already committed in the DB.
    try:
        google_event_id = calendar.create_event(
            summary=f"Massage - {clean_name} - {admin_title.split(' - ')[0]}",
            description=calendar_description + f"\n\nAppointment ID: {appointment_id}\nBuffer: {settings.buffer_minutes} min",
            start=start,
            end=end,
            appointment_id=appointment_id,
        )
        if google_event_id:
            await db_update_appointment_google_event_id(appointment_id, google_event_id)
    except Exception as exc:
        logger.warning(
            "Booking %s: Google Calendar sync failed — %s", appointment_id, exc
        )

    client_text = (
        "✅ Запись подтверждена\n\n"
        f"{client_title}\n"
        f"{start.strftime('%d.%m.%Y')} в {start.strftime('%H:%M')}\n"
        f"{duration} мин · {service['price_eur']}€\n\n"
        "За сутки до визита я напомню вам о сеансе 🐾"
    )
    admin_text = "Новая запись через Mini App:\n\n" + admin_summary

    # Fire-and-forget: Telegram sends must not block or fail the HTTP response.
    async def _send_notifications() -> None:
        try:
            await bot.send_message(telegram_id, client_text)
        except Exception as exc:
            logger.warning(
                "Booking %s: failed to notify client %s — %s",
                appointment_id, telegram_id, exc,
            )
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(admin_id, admin_text)
            except Exception as exc:
                logger.warning(
                    "Booking %s: failed to notify admin %s — %s",
                    appointment_id, admin_id, exc,
                )

    asyncio.create_task(_send_notifications())

    return {
        "appointment_id": appointment_id,
        "title": client_title,
        "date": start.strftime("%d.%m.%Y"),
        "time": start.strftime("%H:%M"),
        "duration_minutes": duration,
        "price_eur": service["price_eur"],
        "is_package": bool(service["is_package"]),
        "package_sessions": service["package_sessions"],
        "first_visit_bonus_applied": first_bonus,
    }


@app.get("/api/my-appointments")
async def my_appointments(lang: str = "ru", initData: str | None = Query(default=None), x_telegram_init_data: str | None = Header(default=None)):
    telegram_id = current_user_id(initData, x_telegram_init_data)
    client = await db_ensure_client(telegram_id)
    rows = await db_get_active_bookings(client["id"])
    return [
        {
            "id": r["id"],
            "title": service_title(r, lang),
            "starts_at": r["starts_at"],
            "duration_minutes": r["duration_minutes"],
            "price_eur": r["price_eur"],
            "is_package": bool(r["is_package"]),
            "package_sessions": r["package_sessions"],
            "status": r["status"],
        }
        for r in rows
    ]


@app.get("/api/active-bookings")
async def active_bookings(lang: str = "ru", initData: str | None = Query(default=None), x_telegram_init_data: str | None = Header(default=None)):
    telegram_id = current_user_id(initData, x_telegram_init_data)
    client = await db_ensure_client(telegram_id)
    now_iso = datetime.now(settings.tzinfo).isoformat()
    rows = await db_get_active_bookings(client["id"], now_iso)
    return [
        {
            "id": row["id"],
            "service_id": row["service_id"],
            "title": service_title(row, lang),
            "starts_at": row["starts_at"],
            "duration_minutes": row["duration_minutes"],
            "price_eur": row["price_eur"],
            "is_package": bool(row["is_package"]),
            "package_sessions": row["package_sessions"],
            "status": row["status"],
            "contact": client["contact"] if "contact" in client.keys() and client["contact"] else client["phone"],
        }
        for row in rows
    ]


@app.post("/api/bookings/{appointment_id}/cancel")
async def cancel_booking_endpoint(
    appointment_id: int,
    initData: str | None = Query(default=None),
    x_telegram_init_data: str | None = Header(default=None)
):
    telegram_id = current_user_id(initData, x_telegram_init_data)
    client = await db_ensure_client(telegram_id)
    row = await db_get_client_appointment(appointment_id, client["id"])
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    if row["google_event_id"]:
        calendar.delete_event(row["google_event_id"])
    await db_update_appointment_status(appointment_id, "cancelled")
    
    from app.handlers import get_appointment_admin_summary
    from app.i18n import t
    summary = await get_appointment_admin_summary(appointment_id)
    for admin_id in settings.admin_ids:
        await bot.send_message(admin_id, t("ru", "admin_client_cancelled", summary=summary))
    return {"status": "ok"}


@app.post("/api/bookings/{appointment_id}/reschedule")
async def reschedule_booking_endpoint(
    appointment_id: int,
    payload: RescheduleRequest,
    initData: str | None = Query(default=None),
    x_telegram_init_data: str | None = Header(default=None)
):
    user = current_user(initData, x_telegram_init_data)
    telegram_id = int(user["id"])
    username = user.get("username")
    client = await db_ensure_client(telegram_id)
    
    old_row = await db_get_client_appointment(appointment_id, client["id"])
    if not old_row:
        raise HTTPException(status_code=404, detail="Booking not found")

    service = await db_get_service(payload.service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    first_bonus = bool(old_row["first_visit_bonus_applied"])
    duration = service["duration_minutes"] + (15 if first_bonus else 0)
    available_slots = await get_free_slots(payload.day_iso, duration, settings, calendar)
    if payload.slot not in available_slots:
        raise HTTPException(status_code=409, detail="Slot is no longer available")

    if old_row["google_event_id"]:
        calendar.delete_event(old_row["google_event_id"])
    await db_update_appointment_status(appointment_id, "rescheduled")

    start = parse_local_datetime(payload.day_iso, payload.slot, settings)
    end = start + timedelta(minutes=duration + settings.buffer_minutes)
    client_title = service_title(service, payload.lang)
    admin_title = service_title(service, "ru")
    
    final_contact = client["contact"] if "contact" in client.keys() and client["contact"] else client["phone"]
    
    summary_text = (
        f"Услуга: {admin_title}\n"
        f"Дата: {start.strftime('%d.%m.%Y')}\n"
        f"Время: {start.strftime('%H:%M')}\n"
        f"Длительность: {duration} мин\n"
        f"Цена: {service['price_eur']}€\n"
        f"Имя: {client['name']}"
    )

    if final_contact and final_contact.startswith("@"):
        username_clean = final_contact[1:]
        admin_contact = f"Telegram: <a href=\"https://t.me/{username_clean}\">@{username_clean}</a>"
    elif final_contact:
        admin_contact = f"Контакт: {final_contact}\nTelegram: <a href=\"tg://user?id={telegram_id}\">открыть профиль</a>"
    else:
        if username:
            admin_contact = f"Telegram: <a href=\"https://t.me/{username}\">@{username}</a>"
        else:
            admin_contact = f"Контакт: не указан\nTelegram: <a href=\"tg://user?id={telegram_id}\">открыть профиль</a>"

    admin_summary = summary_text + f"\n{admin_contact}"
    
    calendar_description = (
        summary_text + 
        f"\nКонтакт: {final_contact or 'не указан'}" +
        f"\nTelegram ID: {telegram_id}" +
        (f"\nUsername: @{username}" if username else "")
    )
    
    if first_bonus:
        admin_summary += "\nБонус первого визита: +15 минут"
        calendar_description += "\nБонус первого визита: +15 минут"

    new_appointment_id = await db_create_appointment(client["id"], service["id"], start.isoformat(), end.isoformat(), duration, service["price_eur"], "telegram_miniapp", int(first_bonus))

    google_event_id = calendar.create_event(
        summary=f"Massage - {client['name']} - {admin_title.split(' - ')[0]}",
        description=calendar_description + f"\n\nAppointment ID: {new_appointment_id}\nBuffer: {settings.buffer_minutes} min",
        start=start,
        end=end,
        appointment_id=new_appointment_id,
    )
    if google_event_id:
        await db_update_appointment_google_event_id(new_appointment_id, google_event_id)

    client_text = (
        "✅ Запись перенесена\n\n"
        f"{client_title}\n"
        f"{start.strftime('%d.%m.%Y')} в {start.strftime('%H:%M')}\n"
        f"{duration} мин · {service['price_eur']}€\n\n"
        "За сутки до визита я напомню вам о сеансе 🐾"
    )
    await bot.send_message(telegram_id, client_text)

    from app.handlers import get_appointment_admin_summary
    from app.i18n import t
    old_summary = await get_appointment_admin_summary(appointment_id)
    admin_text = t("ru", "admin_client_reschedule", summary=old_summary) + f"\n\nНовая запись:\n{admin_summary}"
    for admin_id in settings.admin_ids:
        await bot.send_message(admin_id, admin_text)

    return {
        "status": "ok",
        "appointment_id": new_appointment_id,
        "title": client_title,
        "date": start.strftime("%d.%m.%Y"),
        "time": start.strftime("%H:%M"),
        "duration_minutes": duration,
        "price_eur": service["price_eur"],
        "is_package": bool(service["is_package"]),
        "package_sessions": service["package_sessions"],
        "first_visit_bonus_applied": first_bonus,
    }
