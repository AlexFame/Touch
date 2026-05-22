from datetime import date, timedelta

from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.i18n import t


def open_miniapp_kb(webapp_url: str, is_admin: bool = False, lang: str = "ru") -> InlineKeyboardMarkup | None:
    if not webapp_url and not is_admin:
        return None
    kb = InlineKeyboardBuilder()
    if webapp_url:
        kb.button(text="Відкрити" if lang == "ua" else "Открыть", web_app=WebAppInfo(url=webapp_url))
    if is_admin:
        kb.button(text="👨‍💼 Админка", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


def language_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Русский", callback_data="lang:ru")
    kb.button(text="Українська", callback_data="lang:ua")
    kb.adjust(2)
    return kb.as_markup()


def main_menu_kb(lang: str, webapp_url: str = "", is_admin: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if webapp_url:
        kb.button(text=t(lang, "book"), web_app=WebAppInfo(url=webapp_url))
    kb.button(text=t(lang, "my_booking"), callback_data="menu:my_booking")
    kb.button(text=t(lang, "prices"), callback_data="menu:prices")
    kb.button(text=t(lang, "contacts"), callback_data="menu:contacts")
    kb.button(text=t(lang, "my_package"), callback_data="menu:package")
    if is_admin:
        kb.button(text="👨‍💼 Админка", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()


def services_kb(services: list, lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    title_key = "title_ua" if lang == "ua" else "title_ru"
    for s in services:
        kb.button(text=s[title_key], callback_data=f"service:{s['id']}")
    kb.button(text=t(lang, "back"), callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def dates_kb(lang: str, days: int = 14) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    today = date.today()
    for i in range(days):
        d = today + timedelta(days=i)
        label = d.strftime("%d.%m")
        kb.button(text=label, callback_data=f"date:{d.isoformat()}")
    kb.button(text=t(lang, "back"), callback_data="menu:book")
    kb.adjust(3)
    return kb.as_markup()


def slots_kb(slots: list[str], lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for slot in slots:
        kb.button(text=slot, callback_data=f"time:{slot}")
    kb.button(text=t(lang, "back"), callback_data="menu:dates")
    kb.adjust(3)
    return kb.as_markup()


def confirm_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "confirm"), callback_data="booking:confirm")
    kb.button(text=t(lang, "cancel"), callback_data="booking:cancel")
    kb.adjust(1)
    return kb.as_markup()


def admin_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Сегодня", callback_data="admin:today")
    kb.button(text="📆 Завтра", callback_data="admin:tomorrow")
    kb.button(text="🗓 Ближайшие записи", callback_data="admin:upcoming")
    kb.button(text="⬅️ Главное меню", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def admin_appointment_kb(appointment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Сеанс завершён", callback_data=f"admin:complete:{appointment_id}")
    kb.button(text="🔁 Перенести", callback_data=f"admin:reschedule:{appointment_id}")
    kb.button(text="❌ Отменить", callback_data=f"admin:cancel:{appointment_id}")
    kb.button(text="🚫 Клиент не пришёл", callback_data=f"admin:no_show:{appointment_id}")
    kb.adjust(1)
    return kb.as_markup()



def reminder_kb(appointment_id: int, lang: str, webapp_url: str = "") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "reminder_ok"), callback_data=f"client:ok:{appointment_id}")
    if webapp_url:
        kb.button(text=t(lang, "reminder_reschedule"), web_app=WebAppInfo(url=webapp_url))
    kb.button(text=t(lang, "reminder_cancel"), callback_data=f"client:cancel:{appointment_id}")
    kb.adjust(1)
    return kb.as_markup()


def book_shortcut_kb(lang: str, webapp_url: str = "") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if webapp_url:
        kb.button(text=t(lang, "book"), web_app=WebAppInfo(url=webapp_url))
    kb.adjust(1)
    return kb.as_markup()


def main_menu_webapp_kb(lang: str, webapp_url: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if webapp_url:
        kb.button(text="🐾 Открыть запись" if lang == "ru" else "🐾 Відкрити запис", web_app=WebAppInfo(url=webapp_url))
    kb.button(text=t(lang, "my_booking"), callback_data="menu:my_booking")
    kb.button(text=t(lang, "prices"), callback_data="menu:prices")
    kb.button(text=t(lang, "contacts"), callback_data="menu:contacts")
    kb.button(text=t(lang, "my_package"), callback_data="menu:package")
    if is_admin:
        kb.button(text="👨‍💼 Админка", callback_data="admin:menu")
    kb.adjust(1)
    return kb.as_markup()
