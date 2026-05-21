import re


LINK_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/|\S+\.\S{2,})", re.IGNORECASE)
NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ'’ -]+$")
TELEGRAM_USERNAME_RE = re.compile(r"^@[A-Za-z0-9_]{5,32}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9 ()-]{5,20}[0-9]$")
NAME_UNSUPPORTED_RE = re.compile(r"[^A-Za-zА-Яа-яЁёІіЇїЄєҐґ'’ -]+")


def normalize_name(value: str | None) -> str:
    name = (value or "").strip()
    name = NAME_UNSUPPORTED_RE.sub("", name)
    return re.sub(r"\s+", " ", name).strip()


def valid_name(value: str | None) -> bool:
    raw = value or ""
    name = normalize_name(raw)
    if not 2 <= len(name) <= 60:
        return False
    if LINK_RE.search(raw):
        return False
    if any(ch.isdigit() for ch in raw):
        return False
    return bool(NAME_RE.fullmatch(name)) and any(ch.isalpha() for ch in name)


def normalize_contact(value: str | None) -> str:
    contact = (value or "").strip()
    if not contact:
        return ""
    if contact.startswith("@"):
        return contact
    if any(ch.isdigit() for ch in contact):
        return contact
    return f"@{contact}"


def valid_contact(value: str | None) -> bool:
    contact = normalize_contact(value)
    if not contact:
        return True
    if LINK_RE.search(contact):
        return False
    if contact.startswith("@"):
        return bool(TELEGRAM_USERNAME_RE.fullmatch(contact))
    digits = re.sub(r"\D", "", contact)
    return 7 <= len(digits) <= 15 and bool(PHONE_RE.fullmatch(contact))
