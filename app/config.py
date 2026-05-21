import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: list[int]
    business_tz: str
    business_start_hour: int
    business_end_hour: int
    slot_step_minutes: int
    buffer_minutes: int
    webapp_url: str
    dev_telegram_id: int | None
    calendar_enabled: bool
    google_calendar_id: str
    google_service_account_file: str
    google_review_url: str
    booking_days_ahead: int
    app_env: str
    allowed_origins: list[str]

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.business_tz)


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Add it to .env")

    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip()]
    if not admin_ids:
        raise RuntimeError("ADMIN_IDS is missing. Add your Telegram user id to .env")

    dev_raw = os.getenv("DEV_TELEGRAM_ID", "").strip()
    app_env = os.getenv("APP_ENV", "development").strip().lower()

    # DEV_TELEGRAM_ID must never work in production regardless of what's in .env
    dev_telegram_id = int(dev_raw) if dev_raw and app_env != "production" else None

    origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    if origins_raw:
        allowed_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    elif app_env == "production":
        allowed_origins = []
    else:
        allowed_origins = ["*"]

    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        business_tz=os.getenv("BUSINESS_TZ", "Europe/Berlin"),
        business_start_hour=_int("BUSINESS_START_HOUR", 10),
        business_end_hour=_int("BUSINESS_END_HOUR", 20),
        slot_step_minutes=_int("SLOT_STEP_MINUTES", 30),
        buffer_minutes=_int("BUFFER_MINUTES", 15),
        webapp_url=os.getenv("WEBAPP_URL", "").strip(),
        dev_telegram_id=dev_telegram_id,
        calendar_enabled=_bool("CALENDAR_ENABLED", False),
        google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"),
        google_review_url=os.getenv("GOOGLE_REVIEW_URL", ""),
        booking_days_ahead=_int("BOOKING_DAYS_AHEAD", 30),
        app_env=app_env,
        allowed_origins=allowed_origins,
    )
