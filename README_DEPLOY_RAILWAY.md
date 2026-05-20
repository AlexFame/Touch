# Deploying to Railway

This project is configured to run on Railway as three separate services:
1. **Backend API** (FastAPI)
2. **Bot Worker** (Telegram bot using aiogram)
3. **Mini App** (React frontend)

## Prerequisites

- A Railway account (https://railway.app)
- A GitHub repository containing this codebase
- Your Telegram Bot Token (`BOT_TOKEN`)
- Google Calendar Service Account credentials

## Step 1: Create a PostgreSQL Database

1. In your Railway project, click **New** -> **Database** -> **Add PostgreSQL**.
2. Railway will provision a database and provide a `DATABASE_URL` environment variable.
3. This single database will be shared between the API and the Bot worker. The schema will be created automatically upon the first startup.

## Step 2: Deploy the Backend API

1. Click **New** -> **GitHub Repo** and select your repository.
2. Go to the new service settings and rename it to `backend-api`.
3. Under **Variables**, link the `DATABASE_URL` from the PostgreSQL service.
4. Add the following environment variables:
   - `BOT_TOKEN`: Your Telegram bot token
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: The raw JSON content of your `service_account.json` file.
   - Any other required variables from your `.env` file (e.g. `ADMIN_IDS`, `BUSINESS_TZ`, `CALENDAR_ENABLED`).
5. Under **Settings** -> **Build**, ensure it uses the Python Nixpacks builder.
6. Under **Settings** -> **Deploy**, set the Start Command to:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```
7. Click **Generate Domain** to get a public URL for your API.

## Step 3: Deploy the Bot Worker

1. Click **New** -> **GitHub Repo** and select your repository again.
2. Rename this service to `bot-worker`.
3. Under **Variables**, add all the exact same environment variables as the backend API (`DATABASE_URL`, `BOT_TOKEN`, `GOOGLE_SERVICE_ACCOUNT_JSON`, etc.).
   *Crucial: Also add `WEBAPP_URL` and set it to the public domain of the Mini App (which you will set up in Step 4).*
4. Under **Settings** -> **Deploy**, set the Start Command to:
   ```bash
   python -m app.main
   ```
5. Do *not* generate a domain for this service, as it runs via long-polling in the background.

## Step 4: Deploy the Mini App (Frontend)

1. Click **New** -> **GitHub Repo** and select your repository.
2. Rename this service to `miniapp-frontend`.
3. Under **Settings** -> **Build**, change the Root Directory to `/miniapp`.
4. The Build Command should be:
   ```bash
   npm run build
   ```
5. Set the Start Command to a static server, for example:
   ```bash
   npx serve -s dist -p $PORT
   ```
6. Click **Generate Domain** to get a public URL for your Mini App.
7. Important: Update the `bot-worker` environment variables to set `WEBAPP_URL` to this newly generated domain. Also, ensure the API URL in the frontend points to your `backend-api` domain if it is not relative.

## Notes
- **Local Development**: If you run the project locally without `DATABASE_URL` set, the app will automatically fall back to using SQLite (`massage_bot.sqlite3`) and the local `service_account.json` file.
- **Database Schema**: The schema for PostgreSQL is built independently and natively using `SERIAL` and proper `TIMESTAMP` data types, ensuring optimal performance.

---

## Local Development (all services at once)

Use [honcho](https://honcho.readthedocs.io/) to start all three services with a single command.

### Setup

```bash
# Install Python dependencies (including honcho)
pip install -r requirements.txt

# Install frontend dependencies
cd miniapp && npm install && cd ..

# Copy and fill in your environment variables
cp .env.example .env   # or create .env manually
```

### Run

```bash
honcho start -f Procfile.dev
```

This starts:
- `backend` — FastAPI on http://localhost:8000 (hot-reload enabled)
- `bot` — Telegram bot worker (long-polling)
- `miniapp` — Vite dev server on http://localhost:5173

Press `Ctrl+C` to stop all processes at once.
