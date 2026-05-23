from datetime import datetime, timedelta
import html

from aiogram import F, Router, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.booking import first_visit_bonus_available, format_summary, get_free_slots, parse_local_datetime
from app.calendar_client import CalendarClient
from app.config import Settings
from app.database import db_ensure_client, db_update_client_lang, db_update_client_profile, db_get_services, db_get_service, db_create_appointment, db_update_appointment_google_event_id, db_update_appointment_time, db_create_package, db_get_client_appointment, db_update_appointment_status, db_get_appointments_today, db_get_appointment_with_client, db_mark_first_visit_bonus_used, db_increment_package_sessions, db_increment_client_no_show_count, db_mark_review_sent, db_get_google_event_id, db_get_active_bookings, db_get_active_package, db_get_appointment_admin_summary_data, db_get_booked_appointments_for_date, db_get_upcoming_booked_appointments, db_get_admin_booking_counts
from app.i18n import t
from app.keyboards import (
    admin_appointment_kb,
    admin_menu_kb,
    book_shortcut_kb,
    confirm_kb,
    dates_kb,
    main_menu_kb,
    main_menu_webapp_kb,
    open_miniapp_kb,
    services_kb,
    slots_kb,
)
from app.states import BookingState
from app.validation import normalize_contact, normalize_name, valid_contact, valid_name

router = Router()

WELCOME_TEXTS = {
    "ru": (
        "Добро пожаловать в массажную студию «Прикосновение» 🐾\n\n"
        "Здесь вы можете быстро записаться на массаж, выбрать удобное время и управлять своими визитами в приложении.\n\n"
        "Нажмите «Открыть», чтобы выбрать услугу, дату и время.\n\n"
        "Важно: мы не являемся врачами или физиотерапевтами и не оказываем лечебные или медицинские услуги. "
        "Все процедуры направлены на расслабление, восстановление сил и общее самочувствие."
    ),
    "ua": (
        "Ласкаво просимо до масажної студії «Прикосновение» 🐾\n\n"
        "Тут ви можете швидко записатися на масаж, вибрати зручний час і керувати своїми візитами в застосунку.\n\n"
        "Натисніть «Відкрити», щоб вибрати послугу, дату і час.\n\n"
        "Важливо: ми не є лікарями або фізіотерапевтами і не надаємо лікувальні або медичні послуги. "
        "Усі процедури спрямовані на розслаблення, відновлення сил і загальне самопочуття."
    ),
}


def is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.admin_ids


async def get_lang(user_id: int) -> str:
    client = await db_ensure_client(user_id)
    return client["lang"]


def telegram_lang(user) -> str:
    code = (getattr(user, "language_code", None) or "").lower()
    return "ua" if code.startswith("uk") else "ru"


def welcome_text(lang: str) -> str:
    return WELCOME_TEXTS["ua" if lang == "ua" else "ru"]


def admin_welcome_text() -> str:
    return "Массажная студия «Прикосновение»\n\nОткрой мини-приложение или админку."


def _html_escape(value) -> str:
    return html.escape(str(value or ""))


def _format_admin_status(status: str | None) -> str:
    labels = {
        "booked": "запланирована",
        "completed": "завершена",
        "cancelled": "отменена",
        "no_show": "клиент не пришёл",
        "rescheduled": "перенесена",
    }
    return labels.get(status or "", status or "-")


def _format_admin_contact(row) -> str:
    final_contact = row["contact"] if "contact" in row.keys() and row["contact"] else row.get("phone")
    telegram_id = row.get("telegram_id")

    if final_contact and str(final_contact).startswith("@"):
        username_clean = _html_escape(str(final_contact)[1:])
        return f'Telegram: <a href="https://t.me/{username_clean}">@{username_clean}</a>'

    if final_contact:
        contact = _html_escape(final_contact)
        if telegram_id:
            return f'Контакт: {contact}\nTelegram: <a href="tg://user?id={telegram_id}">открыть профиль</a>'
        return f"Контакт: {contact}"

    if telegram_id:
        return f'Контакт: не указан\nTelegram: <a href="tg://user?id={telegram_id}">открыть профиль</a>'

    return "Контакт: не указан"


def _format_admin_appointment(row) -> str:
    start = str(row["starts_at"])[:16].replace("T", " ")
    return (
        f"{_html_escape(row['title_ru'])}\n"
        f"Дата и время: {start}\n"
        f"Длительность: {row['duration_minutes']} мин\n"
        f"Цена: {row['price_eur']}€\n"
        f"Клиент: {_html_escape(row.get('name') or 'Без имени')}\n"
        f"{_format_admin_contact(row)}\n"
        f"Статус: {_html_escape(_format_admin_status(row.get('status')))}"
    )


async def get_appointment_admin_summary(appointment_id: int) -> str:
    row = await db_get_appointment_admin_summary_data(appointment_id)
    if not row:
        return f"Запись #{appointment_id}"
    return _format_admin_appointment(row)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    lang = telegram_lang(message.from_user)
    await db_ensure_client(message.from_user.id, lang)
    await db_update_client_lang(message.from_user.id, lang)
    admin = is_admin(message.from_user.id, settings)
    await message.answer(
        admin_welcome_text() if admin else welcome_text(lang),
        reply_markup=open_miniapp_kb(
            settings.webapp_url,
            is_admin=admin,
            lang=lang,
        ),
    )


@router.callback_query(F.data.startswith("lang:"))
async def set_language(call: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    lang = call.data.split(":")[1]
    await db_ensure_client(call.from_user.id, lang)
    await db_update_client_lang(call.from_user.id, lang)
    await state.clear()
    await call.message.answer(
        welcome_text(lang),
        reply_markup=open_miniapp_kb(
            settings.webapp_url,
            is_admin=is_admin(call.from_user.id, settings),
            lang=lang,
        ),
    )
    await call.answer()


@router.callback_query(F.data == "menu:main")
async def menu_main(call: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    await state.clear()
    lang = await get_lang(call.from_user.id)
    await call.message.edit_text(
        t(lang, "main_menu"),
        reply_markup=main_menu_webapp_kb(lang, settings.webapp_url, is_admin(call.from_user.id, settings)),
    )
    await call.answer()


@router.callback_query(F.data == "menu:prices")
async def prices(call: CallbackQuery, settings: Settings) -> None:
    lang = await get_lang(call.from_user.id)
    await call.message.edit_text(t(lang, "prices_text"), reply_markup=main_menu_kb(lang, settings.webapp_url))
    await call.answer()


@router.callback_query(F.data == "menu:contacts")
async def contacts(call: CallbackQuery, settings: Settings) -> None:
    lang = await get_lang(call.from_user.id)
    await call.message.edit_text(t(lang, "contacts_text"), reply_markup=main_menu_kb(lang, settings.webapp_url))
    await call.answer()


@router.callback_query(F.data == "menu:package")
async def package_status(call: CallbackQuery, settings: Settings) -> None:
    lang = await get_lang(call.from_user.id)
    client = await db_ensure_client(call.from_user.id)
    package = await db_get_active_package(client["id"])
    if not package:
        text = t(lang, "no_package")
    else:
        text = t(
            lang,
            "package_status",
            left=package["sessions_total"] - package["sessions_used"],
            total=package["sessions_total"],
            expires=package["expires_at"] or "-",
        )
    await call.message.edit_text(text, reply_markup=main_menu_kb(lang, settings.webapp_url))
    await call.answer()


@router.callback_query(F.data == "menu:my_booking")
async def my_booking_handler(call: CallbackQuery, settings: Settings) -> None:
    lang = await get_lang(call.from_user.id)
    client = await db_ensure_client(call.from_user.id)
    from datetime import datetime
    now_iso = datetime.now(settings.tzinfo).isoformat()
    rows = await db_get_active_bookings(client["id"], now_iso)
    if not rows:
        await call.message.edit_text(t(lang, "no_active_booking"), reply_markup=main_menu_kb(lang, settings.webapp_url, is_admin(call.from_user.id, settings)))
        await call.answer()
        return

    await call.message.delete()
    from app.keyboards import reminder_kb
    for row in rows:
        start = parse_local_datetime(row["starts_at"][:10], row["starts_at"][11:16], settings)
        title_key = "title_ua" if lang == "ua" else "title_ru"
        contact_val = client["contact"] if "contact" in client.keys() and client["contact"] else client["phone"]

        summary = format_summary(
            lang=lang,
            service_title=row[title_key],
            start=start,
            duration=row["duration_minutes"],
            price=row["price_eur"],
            name=client["name"],
            contact=contact_val,
            bonus=bool(row["first_visit_bonus_applied"]),
        )
        
        await call.message.answer(
            t(lang, "my_booking_text", summary=summary),
            reply_markup=reminder_kb(row["id"], lang, settings.webapp_url),
        )

    from app.keyboards import main_menu_webapp_kb
    await call.message.answer(t(lang, "main_menu"), reply_markup=main_menu_webapp_kb(lang, settings.webapp_url, is_admin(call.from_user.id, settings)))
    await call.answer()


@router.callback_query(F.data == "menu:book")
async def book_start(call: CallbackQuery, state: FSMContext) -> None:
    lang = await get_lang(call.from_user.id)
    services = await db_get_services(exclude_packages=True)
    await state.set_state(BookingState.choosing_service)
    await call.message.edit_text(t(lang, "choose_service"), reply_markup=services_kb(services, lang))
    await call.answer()


@router.callback_query(F.data.startswith("service:"), BookingState.choosing_service)
async def choose_service(call: CallbackQuery, state: FSMContext) -> None:
    lang = await get_lang(call.from_user.id)
    service_id = call.data.split(":")[1]
    service = await db_get_service(service_id)
    if not service:
        await call.answer("Service not found")
        return

    await state.update_data(service_id=service_id)
    await state.set_state(BookingState.choosing_date)
    await call.message.edit_text(t(lang, "choose_date"), reply_markup=dates_kb(lang))
    await call.answer()


@router.callback_query(F.data == "menu:dates")
async def back_to_dates(call: CallbackQuery, state: FSMContext) -> None:
    lang = await get_lang(call.from_user.id)
    await state.set_state(BookingState.choosing_date)
    await call.message.edit_text(t(lang, "choose_date"), reply_markup=dates_kb(lang))
    await call.answer()


@router.callback_query(F.data.startswith("date:"), BookingState.choosing_date)
async def choose_date(call: CallbackQuery, state: FSMContext, settings: Settings, calendar: CalendarClient) -> None:
    lang = await get_lang(call.from_user.id)
    data = await state.get_data()
    service = await db_get_service(data["service_id"])
    client = await db_ensure_client(call.from_user.id)
    first_bonus_applied = not bool(service["is_package"]) and await first_visit_bonus_available(client["id"])
    duration_for_slot = service["duration_minutes"] + (15 if first_bonus_applied else 0)
    day_iso = call.data.split(":", 1)[1]
    slots = await get_free_slots(day_iso, duration_for_slot, settings, calendar)

    await state.update_data(day_iso=day_iso)
    await state.set_state(BookingState.choosing_time)

    if not slots:
        await call.message.edit_text(t(lang, "no_slots"), reply_markup=dates_kb(lang))
    else:
        await call.message.edit_text(t(lang, "choose_time"), reply_markup=slots_kb(slots, lang))
    await call.answer()


@router.callback_query(F.data.startswith("time:"), BookingState.choosing_time)
async def choose_time(call: CallbackQuery, state: FSMContext) -> None:
    lang = await get_lang(call.from_user.id)
    slot = call.data.split(":", 1)[1]
    await state.update_data(slot=slot)
    await state.set_state(BookingState.entering_name)
    await call.message.edit_text(t(lang, "ask_name"))
    await call.answer()


@router.message(BookingState.entering_name)
async def enter_name(message: Message, state: FSMContext) -> None:
    lang = await get_lang(message.from_user.id)
    name = normalize_name(message.text)
    if not valid_name(name):
        await message.answer(t(lang, "invalid_name"))
        return
    await state.update_data(name=name)
    await state.set_state(BookingState.entering_contact)
    await message.answer(t(lang, "ask_contact"))


@router.message(BookingState.entering_contact)
async def enter_contact(message: Message, state: FSMContext, settings: Settings) -> None:
    lang = await get_lang(message.from_user.id)
    contact = normalize_contact(message.text or "")
    if not valid_contact(contact):
        await message.answer(t(lang, "invalid_contact"))
        return
    data = await state.get_data()
    service = await db_get_service(data["service_id"])
    client = await db_ensure_client(message.from_user.id)

    start = parse_local_datetime(data["day_iso"], data["slot"], settings)
    first_bonus_applied = not bool(service["is_package"]) and await first_visit_bonus_available(client["id"])
    duration = service["duration_minutes"] + (15 if first_bonus_applied else 0)

    title_key = "title_ua" if lang == "ua" else "title_ru"
    summary = format_summary(
        lang=lang,
        service_title=service[title_key],
        start=start,
        duration=duration,
        price=service["price_eur"],
        name=data["name"],
        contact=contact,
        bonus=first_bonus_applied,
    )
    await state.update_data(contact=contact, summary=summary, duration=duration, first_bonus_applied=first_bonus_applied)
    await state.set_state(BookingState.confirming)
    await message.answer(t(lang, "confirm_booking", summary=summary), reply_markup=confirm_kb(lang))


@router.callback_query(F.data == "booking:cancel")
async def cancel_booking(call: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    lang = await get_lang(call.from_user.id)
    await state.clear()
    await call.message.edit_text(t(lang, "main_menu"), reply_markup=main_menu_webapp_kb(lang, settings.webapp_url, is_admin(call.from_user.id, settings)))
    await call.answer()


@router.callback_query(F.data == "booking:confirm", BookingState.confirming)
async def confirm_booking(
    call: CallbackQuery,
    state: FSMContext,
    settings: Settings,
    calendar: CalendarClient,
    bot: Bot,
) -> None:
    lang = await get_lang(call.from_user.id)
    data = await state.get_data()
    service = await db_get_service(data["service_id"])
    client = await db_ensure_client(call.from_user.id)
    await db_update_client_profile(call.from_user.id, data["name"], data["contact"])

    reschedule_appointment_id = data.get("reschedule_appointment_id")
    if reschedule_appointment_id:
        old_row = {"google_event_id": await db_get_google_event_id(reschedule_appointment_id)}
        if old_row and old_row["google_event_id"]:
            calendar.delete_event(old_row["google_event_id"])
        await db_update_appointment_status(reschedule_appointment_id, "rescheduled")
        
        old_summary = await get_appointment_admin_summary(reschedule_appointment_id)
        for admin_id in settings.admin_ids:
            await bot.send_message(admin_id, t("ru", "admin_client_reschedule", summary=old_summary))

    start = parse_local_datetime(data["day_iso"], data["slot"], settings)
    end = start + timedelta(minutes=data["duration"] + settings.buffer_minutes)

    appointment_id = await db_create_appointment(
        client["id"],
        service["id"],
        start.isoformat(),
        end.isoformat(),
        data["duration"],
        service["price_eur"],
        "telegram_bot",
        int(data["first_bonus_applied"]),
    )

    google_event_id = calendar.create_event(
        summary=f"Massage - {data['name']}",
        description=data["summary"] + f"\n\nAppointment ID: {appointment_id}\nBuffer: {settings.buffer_minutes} min",
        start=start,
        end=end,
        appointment_id=appointment_id,
    )
    if google_event_id:
        await db_update_appointment_google_event_id(appointment_id, google_event_id)

    if service["is_package"]:
        expires = (start.date() + timedelta(days=90)).isoformat()
        await db_create_package(client["id"], service["package_sessions"], expires)

    await call.message.edit_text(t(lang, "confirmed"))
    for admin_id in settings.admin_ids:
        await bot.send_message(
            admin_id,
            t("ru", "admin_new", summary=data["summary"]),
            reply_markup=admin_appointment_kb(appointment_id),
        )

    await state.clear()
    await call.answer()


@router.callback_query(F.data.startswith("client:ok:"))
async def client_confirm_visit(call: CallbackQuery) -> None:
    lang = await get_lang(call.from_user.id)
    appointment_id = int(call.data.split(":")[2])
    client = await db_ensure_client(call.from_user.id)
    row = await db_get_client_appointment(appointment_id, client["id"])
    if not row:
        await call.answer("Запись не найдена")
        return
    await call.message.edit_text(t(lang, "reminder_confirmed"))
    await call.answer()


@router.callback_query(F.data.startswith("client:cancel:"))
async def client_cancel_visit(call: CallbackQuery, settings: Settings, calendar: CalendarClient, bot: Bot) -> None:
    lang = await get_lang(call.from_user.id)
    appointment_id = int(call.data.split(":")[2])
    client = await db_ensure_client(call.from_user.id)
    row = await db_get_client_appointment(appointment_id, client["id"])
    google_event_id = await db_get_google_event_id(appointment_id)
    if google_event_id:
        calendar.delete_event(google_event_id)
    await db_update_appointment_status(appointment_id, "cancelled")
    summary = await get_appointment_admin_summary(appointment_id)
    for admin_id in settings.admin_ids:
        await bot.send_message(admin_id, t("ru", "admin_client_cancelled", summary=summary))
    await call.message.edit_text(t(lang, "client_cancelled"), reply_markup=book_shortcut_kb(lang, settings.webapp_url))
    await call.answer()


@router.callback_query(F.data.startswith("client:reschedule:"))
async def client_reschedule_visit(call: CallbackQuery, settings: Settings, state: FSMContext, calendar: CalendarClient, bot: Bot) -> None:
    lang = await get_lang(call.from_user.id)
    appointment_id = int(call.data.split(":")[2])
    client = await db_ensure_client(call.from_user.id)
    row = await db_get_client_appointment(appointment_id, client["id"])
    if not row:
        await call.answer("Запись не найдена")
        return
        
    await state.update_data(reschedule_appointment_id=appointment_id)

    services = await db_get_services(exclude_packages=True)
    await state.set_state(BookingState.choosing_service)
    await call.message.edit_text(t(lang, "client_reschedule") + "\n\n" + t(lang, "choose_service"), reply_markup=services_kb(services, lang))
    await call.answer()


@router.callback_query(F.data == "admin:menu")
async def admin_menu(call: CallbackQuery, settings: Settings) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return
    await call.message.edit_text("Админка записей\n\nВыберите, какие записи показать:", reply_markup=admin_menu_kb())
    await call.answer()


async def _send_admin_appointments(call: CallbackQuery, rows, empty_text: str, title: str) -> None:
    if not rows:
        await call.message.edit_text(empty_text, reply_markup=admin_menu_kb())
        await call.answer()
        return

    await call.message.edit_text(title, reply_markup=admin_menu_kb())
    for row in rows:
        await call.message.answer(
            _format_admin_appointment(row),
            reply_markup=admin_appointment_kb(row["id"]),
            parse_mode="HTML",
        )
    await call.answer()


@router.callback_query(F.data == "admin:today")
async def admin_today(call: CallbackQuery, settings: Settings) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    today_iso = datetime.now(settings.tzinfo).date().isoformat()
    rows = await db_get_booked_appointments_for_date(today_iso)
    await _send_admin_appointments(call, rows, "На сегодня активных записей нет.", "Активные записи на сегодня:")


@router.callback_query(F.data == "admin:tomorrow")
async def admin_tomorrow(call: CallbackQuery, settings: Settings) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    tomorrow_iso = (datetime.now(settings.tzinfo).date() + timedelta(days=1)).isoformat()
    rows = await db_get_booked_appointments_for_date(tomorrow_iso)
    await _send_admin_appointments(call, rows, "На завтра активных записей нет.", "Активные записи на завтра:")


@router.callback_query(F.data == "admin:upcoming")
async def admin_upcoming(call: CallbackQuery, settings: Settings) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    today_iso = datetime.now(settings.tzinfo).date().isoformat()
    try:
        rows = await db_get_upcoming_booked_appointments(today_iso, limit=20)
        if rows:
            await _send_admin_appointments(call, rows, "Ближайших активных записей нет.", "Ближайшие активные записи:")
            return
        counts = await db_get_admin_booking_counts()
        await _send_admin_appointments(
            call,
            rows,
            "Ближайших активных записей нет.\n\n"
            f"Диагностика: всего записей в этой БД: {counts['total_count'] or 0}, "
            f"активных booked: {counts['booked_count'] or 0}.",
            "Ближайшие активные записи:",
        )
    except Exception as exc:
        await call.message.edit_text(
            "Не удалось загрузить ближайшие записи.\n\n"
            f"Ошибка: {type(exc).__name__}: {_html_escape(exc)}",
            reply_markup=admin_menu_kb(),
        )
        await call.answer()


@router.callback_query(F.data.startswith("admin:complete:"))
async def admin_complete(call: CallbackQuery, settings: Settings, bot: Bot) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    appointment_id = int(call.data.split(":")[2])
    summary = await get_appointment_admin_summary(appointment_id)
    row = await db_get_appointment_with_client(appointment_id)
    if not row:
        await call.answer("Not found")
        return
    if row["status"] != "booked":
        await call.answer("Запись уже обработана")
        return

    await db_update_appointment_status(appointment_id, "completed")

    if row["first_visit_bonus_applied"] and not row["first_visit_bonus_used"]:
        await db_mark_first_visit_bonus_used(row["client_id"])

    package = await db_get_active_package(row["client_id"])
    if package:
        await db_increment_package_sessions(package["id"])

    if settings.google_review_url and not row["review_sent"]:
        client_lang = await get_lang(row["telegram_id"])
        await bot.send_message(row["telegram_id"], t(client_lang, "review_request", url=settings.google_review_url))
        await db_mark_review_sent(appointment_id)

    await call.message.edit_text("✅ Сеанс завершён.\n\n" + summary, parse_mode="HTML")
    await call.answer("Сеанс завершён")


@router.callback_query(F.data.startswith("admin:no_show:"))
async def admin_no_show(call: CallbackQuery, settings: Settings) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    appointment_id = int(call.data.split(":")[2])
    summary = await get_appointment_admin_summary(appointment_id)
    row = await db_get_appointment_with_client(appointment_id)
    if not row:
        await call.answer("Not found")
        return
    if row["status"] != "booked":
        await call.answer("Запись уже обработана")
        return
    await db_update_appointment_status(appointment_id, "no_show")
    await db_increment_client_no_show_count(row["client_id"])
    await call.message.edit_text("🚫 Отмечено: клиент не пришёл.\n\n" + summary, parse_mode="HTML")
    await call.answer("Отмечено")


@router.callback_query(F.data.startswith("admin:cancel:"))
async def admin_cancel(call: CallbackQuery, settings: Settings, calendar: CalendarClient, bot: Bot) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    appointment_id = int(call.data.split(":")[2])
    summary = await get_appointment_admin_summary(appointment_id)
    row = await db_get_appointment_with_client(appointment_id)
    if not row:
        await call.answer("Not found")
        return
    if row["status"] != "booked":
        await call.answer("Запись уже обработана")
        return

    google_event_id = await db_get_google_event_id(appointment_id)
    if google_event_id:
        calendar.delete_event(google_event_id)

    await db_update_appointment_status(appointment_id, "cancelled")

    client_lang = await get_lang(row["telegram_id"])
    await bot.send_message(
        row["telegram_id"],
        "Ваша запись была отменена администратором.\n\n"
        "Если хотите выбрать другое время, откройте запись в боте.",
        reply_markup=book_shortcut_kb(client_lang, settings.webapp_url),
    )

    await call.message.edit_text("🚫 Запись отменена администратором.\n\n" + summary, parse_mode="HTML")
    await call.answer("Запись отменена")


@router.callback_query(F.data.startswith("admin:reschedule:"))
async def admin_reschedule_start(call: CallbackQuery, settings: Settings, state: FSMContext) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    appointment_id = int(call.data.split(":")[2])
    row = await db_get_appointment_with_client(appointment_id)
    if not row:
        await call.answer("Not found")
        return
    if row["status"] != "booked":
        await call.answer("Запись уже обработана")
        return

    await state.update_data(admin_reschedule_appointment_id=appointment_id)
    await state.set_state(BookingState.admin_reschedule_date)
    await call.message.edit_text("Выберите новую дату для переноса:", reply_markup=dates_kb("ru"))
    await call.answer()


@router.callback_query(F.data.startswith("date:"), BookingState.admin_reschedule_date)
async def admin_reschedule_date(call: CallbackQuery, state: FSMContext, settings: Settings, calendar: CalendarClient) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    data = await state.get_data()
    appointment_id = data.get("admin_reschedule_appointment_id")
    row = await db_get_appointment_with_client(appointment_id)
    if not row:
        await call.answer("Not found")
        return
    if row["status"] != "booked":
        await call.answer("Запись уже обработана")
        return

    day_iso = call.data.split(":", 1)[1]
    slots = await get_free_slots(day_iso, row["duration_minutes"], settings, calendar)
    await state.update_data(admin_reschedule_day_iso=day_iso)
    await state.set_state(BookingState.admin_reschedule_time)
    if not slots:
        await call.message.edit_text("На этот день окон нет. Выберите другую дату:", reply_markup=dates_kb("ru"))
    else:
        await call.message.edit_text("Выберите новое время:", reply_markup=slots_kb(slots, "ru"))
    await call.answer()


@router.callback_query(F.data.startswith("time:"), BookingState.admin_reschedule_time)
async def admin_reschedule_time(call: CallbackQuery, state: FSMContext, settings: Settings, calendar: CalendarClient, bot: Bot) -> None:
    if not is_admin(call.from_user.id, settings):
        await call.answer("No access")
        return

    data = await state.get_data()
    appointment_id = data.get("admin_reschedule_appointment_id")
    day_iso = data.get("admin_reschedule_day_iso")
    slot = call.data.split(":", 1)[1]
    row = await db_get_appointment_with_client(appointment_id)
    if not row or not day_iso:
        await call.answer("Not found")
        return
    if row["status"] != "booked":
        await call.answer("Запись уже обработана")
        return

    slots = await get_free_slots(day_iso, row["duration_minutes"], settings, calendar)
    if slot not in slots:
        await call.answer("Это время уже занято", show_alert=True)
        return

    start = parse_local_datetime(day_iso, slot, settings)
    end = start + timedelta(minutes=row["duration_minutes"] + settings.buffer_minutes)
    await db_update_appointment_time(appointment_id, start.isoformat(), end.isoformat())
    await db_update_appointment_status(appointment_id, "booked")

    title = row["title_ua"] if row["lang"] == "ua" else row["title_ru"]
    final_contact = row["contact"] if "contact" in row.keys() and row["contact"] else row["phone"]
    summary = format_summary(
        lang=row["lang"],
        service_title=title,
        start=start,
        duration=row["duration_minutes"],
        price=row["price_eur"],
        name=row["name"],
        contact=final_contact,
        bonus=bool(row["first_visit_bonus_applied"]),
    )
    description = summary + f"\n\nAppointment ID: {appointment_id}\nBuffer: {settings.buffer_minutes} min"
    if row["google_event_id"]:
        calendar.update_event(
            row["google_event_id"],
            summary=f"Massage - {row['name'] or row['telegram_id']}",
            description=description,
            start=start,
            end=end,
        )
    else:
        google_event_id = calendar.create_event(
            summary=f"Massage - {row['name'] or row['telegram_id']}",
            description=description,
            start=start,
            end=end,
            appointment_id=appointment_id,
        )
        if google_event_id:
            await db_update_appointment_google_event_id(appointment_id, google_event_id)

    try:
        await bot.send_message(
            row["telegram_id"],
            "Ваша запись перенесена администратором:\n\n" + summary,
            reply_markup=book_shortcut_kb(row["lang"], settings.webapp_url),
        )
    except Exception:
        pass

    await state.clear()
    updated_summary = await get_appointment_admin_summary(appointment_id)
    await call.message.edit_text("🔁 Запись перенесена.\n\n" + updated_summary, parse_mode="HTML")
    await call.answer("Запись перенесена")
