# Railway Deployment

Do not deploy this repository root as one service. It is a monorepo:

- `backend/` + `app/` are Python backend/bot code and run from the repository root.
- `miniapp/` is the Vite/React Telegram Mini App and runs from `/miniapp`.

Use a Railway PostgreSQL database and separate services.

## Current working Railway deployment

- Backend API: https://observant-adaptation-production-918f.up.railway.app
- Mini App: https://unique-blessing-production.up.railway.app
- Status: Backend API, Mini App, and Postgres are online.

## 1. PostgreSQL

Create a Railway PostgreSQL database first. Use its `DATABASE_URL` in the
Backend API and Bot Worker services.

## 2. Backend API Service

- Root Directory: `/`
- Build Command: leave empty, or use Railway/Nixpacks default
- Start Command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Variables:

```env
BOT_TOKEN=...
ADMIN_IDS=349353007
DATABASE_URL=${{Postgres.DATABASE_URL}}
WEBAPP_URL=https://your-miniapp-domain.up.railway.app
BUSINESS_TZ=Europe/Berlin
BUSINESS_START_HOUR=10
BUSINESS_END_HOUR=20
SLOT_STEP_MINUTES=30
BUFFER_MINUTES=15
BOOKING_DAYS_AHEAD=30
CALENDAR_ENABLED=true
GOOGLE_CALENDAR_ID=...
GOOGLE_SERVICE_ACCOUNT_JSON={...}
GOOGLE_REVIEW_URL=...
```

Generate a public Railway domain for this service. The Mini App uses this URL
as `VITE_API_URL`.

## 3. Bot Worker Service

- Root Directory: `/`
- Build Command: leave empty, or use Railway/Nixpacks default
- Start Command:

```bash
python -m app.main
```

Variables: same as Backend API, including the same `DATABASE_URL` and
`WEBAPP_URL`.

Do not generate a domain for this service. It uses Telegram long polling.

## 4. Mini App Frontend Service

- Root Directory: `/miniapp`
- Build Command:

```bash
npm run build
```

- Start Command:

```bash
npm run preview
```

Variables:

```env
VITE_API_URL=https://your-backend-api-domain.up.railway.app
```

Generate a public Railway domain for this service. Then copy that Mini App URL
into `WEBAPP_URL` for both Python services and restart/redeploy them.

## Notes

- `GOOGLE_SERVICE_ACCOUNT_JSON` should be the raw JSON content from Google
  Cloud. Do not commit `service_account.json`.
- For local development without `DATABASE_URL`, the app uses SQLite.
- Optional config examples are included as `railway.backend.json`,
  `railway.bot.json`, and `miniapp/railway.json`, but Railway UI settings above
  are the source of truth.
