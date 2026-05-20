# Massage Touch Booking Product

Telegram bot + Telegram Mini App + FastAPI backend with Google Calendar as the source of truth.

## What this version does

- Reads real busy time from Google Calendar via Service Account
- Shows available booking slots in the Mini App
- Creates Google Calendar events when clients book
- Saves clients and appointments in SQLite
- Sends Telegram confirmations to client and admin
- Keeps 15-minute buffer after every session
- Applies first-visit bonus: +15 minutes for the first active booking
- Sends 24h reminders and post-visit follow-ups via the bot

## Required setup

1. Enable Google Calendar API in Google Cloud.
2. Create Service Account and download JSON key.
3. Share the massage booking calendar with the Service Account email.
4. Give permission: Make changes to events.
5. Copy Calendar ID from Google Calendar settings.
6. Put JSON key into project root as `service_account.json`.
7. Fill `.env`.

## .env example

```env
BOT_TOKEN=your_new_bot_token
ADMIN_IDS=349353007

BUSINESS_TZ=Europe/Berlin
BUSINESS_START_HOUR=10
BUSINESS_END_HOUR=20
SLOT_STEP_MINUTES=30
BUFFER_MINUTES=15
BOOKING_DAYS_AHEAD=30

WEBAPP_URL=https://your-miniapp-url.ngrok-free.app
DEV_TELEGRAM_ID=349353007

CALENDAR_ENABLED=true
GOOGLE_CALENDAR_ID=your_calendar_id
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
GOOGLE_REVIEW_URL=https://g.page/r/YOUR_GOOGLE_BUSINESS_REVIEW_LINK/review
```

## Run backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Check Calendar connection:

```bash
curl http://localhost:8000/api/calendar/status
```

## Run Mini App locally

```bash
cd miniapp
npm install
npm run dev
```

Open `http://localhost:5173` in browser for local UI preview.

## Run bot

From project root:

```bash
source .venv/bin/activate
python -m app.main
```

## Telegram Mini App URL

For Telegram, the Mini App needs HTTPS. During testing use ngrok:

```bash
ngrok http 5173
```

Put the generated HTTPS URL into `WEBAPP_URL` and restart the bot.
