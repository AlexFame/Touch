# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Telegram Mini App booking system for a massage studio. Three processes run together:
- **Telegram bot** (`app/`) — aiogram v3, handles booking via inline keyboards + FSM
- **FastAPI backend** (`backend/main.py`) — serves the Mini App's REST API
- **React Mini App** (`miniapp/`) — single-page Vite/React app embedded in Telegram

Google Calendar is the source of truth for busy time. SQLite is used locally; PostgreSQL in production (set `DATABASE_URL`).

## Commands

**Backend:**
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Bot:**
```bash
source .venv/bin/activate
python -m app.main
```

**Mini App (dev):**
```bash
cd miniapp
npm run dev        # http://localhost:5173, proxies /api → :8000
npm run build      # production build
```

**Check Google Calendar connection:**
```bash
curl http://localhost:8000/api/calendar/status
```

## Architecture

### Slot availability logic (`app/booking.py`)
`get_free_slots()` computes available times by subtracting:
1. Already-booked appointments from SQLite
2. Busy ranges from Google Calendar
3. A `buffer_minutes` gap appended to every booked slot's end

First-visit bonus automatically adds 15 min to slot duration if the client has no prior active bookings.

### Authentication (`backend/main.py` → `verify_init_data`)
All API calls are authenticated via Telegram's `initData` HMAC (sent as `X-Telegram-Init-Data` header or `initData` query param). In local development, `DEV_TELEGRAM_ID` in `.env` bypasses this check entirely.

### Database layer (`app/database.py`)
Dual-mode: if `DATABASE_URL` env var is set, uses asyncpg (PostgreSQL); otherwise uses aiosqlite (`massage_bot.sqlite3`). Both share the same function signatures via a `DBRow` adapter. Schema is created on startup via `init_db()`.

### Mini App UI (`miniapp/src/main.jsx`)
Entire UI is one React component with a `step` state string (`"home"`, `"service"`, `"calendar"`, `"slots"`, `"details"`, `"done"`, `"myBookings"`, etc.). No router — just conditional rendering. All styles in `src/styles.css`. Cat sticker PNGs live in `public/`.

### Bot vs. backend overlap
Both `app/handlers.py` and `backend/main.py` implement booking creation — the bot handles bookings made via Telegram inline flow, the backend handles bookings from the Mini App. `app/booking.py` and `app/database.py` are shared between both.

### Scheduled jobs (`app/scheduler.py`)
APScheduler runs in the bot process:
- Every 15 min: 24h reminders
- Every 6h: post-visit follow-ups
- Daily at 03:00: expire old packages

### i18n
`app/i18n.py` — RU/UA strings accessed via `t(lang, key, **kwargs)`. Mini App is Russian-only.
