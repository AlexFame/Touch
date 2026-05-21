# Touch Client Setup Checklist

Use this checklist when setting up a new Touch massage booking client.

## Required Client Info

- Studio/client name for Telegram bot and Mini App.
- Telegram bot token from BotFather.
- Telegram admin user IDs for `ADMIN_IDS`.
- Public Mini App name, short description, and image for BotFather if needed.
- Business timezone, usually `Europe/Berlin`.
- Business hours: start hour, end hour, slot step, booking days ahead, buffer minutes.
- Google Calendar ID.
- Google service account JSON with access to the calendar.
- Google review URL.
- Studio address and client-facing contact details.
- Service list, durations, prices, packages, and languages required by the client.

## Railway Services

Create one Railway project with four services/resources:

- PostgreSQL database.
- Backend API service.
- Bot Worker service.
- Mini App frontend service.

Do not deploy the repository root as one combined app.

## PostgreSQL

1. In Railway, create **New -> Database -> PostgreSQL**.
2. Use its `DATABASE_URL` in both Python services:
   - Backend API
   - Bot Worker

## Backend API Service

- Service type: GitHub repo service.
- Root Directory: `/`
- Build Command: leave empty, or use Railway/Nixpacks default.
- Start Command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Required variables:

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

Generate a public Railway domain for this service. This is the Backend API URL.

## Bot Worker Service

- Service type: GitHub repo service.
- Root Directory: `/`
- Build Command: leave empty, or use Railway/Nixpacks default.
- Start Command:

```bash
python -m app.main
```

Required variables:

Use the same variables as Backend API, including the same `DATABASE_URL`,
`BOT_TOKEN`, `ADMIN_IDS`, `WEBAPP_URL`, Google Calendar variables, and business
settings.

Do not generate a public Railway domain for the Bot Worker. It runs via Telegram
long polling.

## Mini App Service

- Service type: GitHub repo service.
- Root Directory: `/miniapp`
- Build Command:

```bash
npm run build
```

- Start Command:

```bash
npm run preview
```

Required variables:

```env
VITE_API_URL=https://your-backend-api-domain.up.railway.app
```

Generate a public Railway domain for this service. This is the Mini App URL.

## Domain Flow

1. Deploy Backend API first and generate its Railway domain.
2. Put the Backend API URL into the Mini App service:

```env
VITE_API_URL=https://your-backend-api-domain.up.railway.app
```

3. Redeploy the Mini App service so Vite builds with the correct API URL.
4. Generate the Mini App Railway domain.
5. Put the Mini App URL into Backend API and Bot Worker:

```env
WEBAPP_URL=https://your-miniapp-domain.up.railway.app
```

6. Redeploy/restart Backend API and Bot Worker.
7. In BotFather, set the Mini App/Web App URL to the Mini App URL.

## Testing Checklist

- Backend API service is online.
- Mini App service is online.
- PostgreSQL is online and connected through `DATABASE_URL`.
- Bot Worker logs show no token/config errors.
- Open Backend API `/api/calendar/status` and confirm it responds.
- Open Mini App URL in browser and confirm the app loads.
- Open the bot in Telegram and press `/start`.
- Press **Открыть** and confirm the Mini App opens inside Telegram.
- Confirm services load in the Mini App.
- Create a test booking from Telegram Mini App.
- Confirm the booking appears in PostgreSQL/backend data.
- Confirm busy time appears in Google Calendar if calendar is enabled.
- Confirm **Мои записи** loads.
- Test cancel/reschedule if the client needs those flows.
- Confirm admin Telegram IDs can see admin controls.
- Confirm regular clients cannot see admin controls.

## Common Errors And Fixes

### `BOT_TOKEN` Missing Or Invalid

Symptoms:
- Backend or Bot Worker fails on startup.
- Logs mention bot token validation or unauthorized Telegram API calls.

Fix:
- Add the correct `BOT_TOKEN` from BotFather to Backend API and Bot Worker.
- Redeploy/restart both Python services.

### `package-lock.json` Mismatch

Symptoms:
- Railway Mini App build fails during `npm ci`.
- Logs mention `package.json` and `package-lock.json` are out of sync.

Fix:
- Run `npm install` inside `/miniapp`.
- Commit the updated `miniapp/package-lock.json`.
- Push and redeploy.

### Vite Blocked Host

Symptoms:
- Browser shows `Blocked request. This host (...) is not allowed.`
- The Mini App service is online but Vite refuses the Railway domain.

Fix:
- Check `miniapp/vite.config.js`.
- Ensure Vite preview allows Railway hosts.
- Redeploy the Mini App service after pushing the config.

### Wrong API URL

Symptoms:
- Mini App loads, but shows `Не удалось выполнить запрос`.
- `/api/...` requests go to the Mini App domain and return 502/404.

Fix:
- Set `VITE_API_URL` in the Mini App service to the Backend API URL.
- Redeploy the Mini App service, because Vite reads this at build time.

### Old Railway Commit

Symptoms:
- GitHub has the fix, but Railway still behaves like old code.
- Recent commits do not appear in Railway deployment details.

Fix:
- Confirm Railway service points to `master` and the correct repository.
- Trigger **Redeploy** on the correct service.
- If needed, push an empty commit to force a fresh deployment.

### `.DS_Store`

Symptoms:
- macOS metadata files appear in `git status`.
- Diff includes binary `.DS_Store` changes.

Fix:
- Keep `.DS_Store` in `.gitignore`.
- Do not commit `.DS_Store`.
- If already tracked, remove from Git index with `git rm --cached`.
