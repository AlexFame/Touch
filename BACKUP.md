# Database Backup and Restore

This project uses two database modes:

- Production on Railway: PostgreSQL, selected by `DATABASE_URL`.
- Local development: SQLite file `massage_bot.sqlite3` in the repository root when `DATABASE_URL` is not set.

Backend API and Bot Worker must use the same `DATABASE_URL` in production. If they use different databases, bookings can appear in the Mini App but not in the bot admin panel.

## Locate the Database

### Railway Production

1. Open the Railway project.
2. Open the PostgreSQL service.
3. Open **Variables**.
4. Copy the Postgres connection variable:

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Use the same `DATABASE_URL` reference in both services:

- Backend API
- Bot Worker

### Local Development

If `DATABASE_URL` is empty or unset, the app uses:

```bash
./massage_bot.sqlite3
```

## Create a Backup

### Railway PostgreSQL

Run from your local machine after installing the Railway CLI and PostgreSQL client tools:

```bash
railway link
railway run ./backup_db.sh
```

Or run directly with a database URL:

```bash
DATABASE_URL='postgresql://...' ./backup_db.sh
```

The backup is written to:

```bash
./backups/
```

PostgreSQL backups are saved as custom-format dump files:

```bash
backups/backup_YYYYMMDD_HHMMSS.dump
```

### Local SQLite

Run:

```bash
./backup_db.sh
```

The SQLite backup is copied to:

```bash
backups/massage_bot_YYYYMMDD_HHMMSS.sqlite3
```

## Restore from Backup

Restoring replaces data. Stop or pause services before restoring production data.

### Railway PostgreSQL

1. Make a fresh backup first:

```bash
railway run ./backup_db.sh
```

2. Restore a dump:

```bash
railway run ./restore_db.sh backups/backup_YYYYMMDD_HHMMSS.dump
```

Or with a direct URL:

```bash
DATABASE_URL='postgresql://...' ./restore_db.sh backups/backup_YYYYMMDD_HHMMSS.dump
```

The script uses `pg_restore --clean --if-exists --no-owner --no-privileges`.

### Local SQLite

1. Stop the local bot/backend processes.
2. Restore:

```bash
./restore_db.sh backups/massage_bot_YYYYMMDD_HHMMSS.sqlite3
```

The current `massage_bot.sqlite3` is moved aside before restore.

## Before Deploying Updates

1. Confirm Backend API and Bot Worker use the same production database:

```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

2. Create a backup:

```bash
railway run ./backup_db.sh
```

3. Confirm the backup file exists in `backups/`.
4. Deploy Backend API and Bot Worker.
5. Check the Mini App can create a new booking.
6. Check the bot admin panel can see that booking.

## Verify Data After Restore

### PostgreSQL

Run:

```bash
railway run psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM appointments;"
railway run psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM clients;"
railway run psql "$DATABASE_URL" -c "SELECT starts_at, status FROM appointments ORDER BY starts_at DESC LIMIT 5;"
```

Then verify in Telegram:

1. Open the bot.
2. Open **Админка**.
3. Open **Все записи** or **Записи по дате**.
4. Confirm expected bookings are visible.

### SQLite

Run:

```bash
sqlite3 massage_bot.sqlite3 "SELECT COUNT(*) FROM appointments;"
sqlite3 massage_bot.sqlite3 "SELECT COUNT(*) FROM clients;"
sqlite3 massage_bot.sqlite3 "SELECT starts_at, status FROM appointments ORDER BY starts_at DESC LIMIT 5;"
```

## Common Issues

### Bot Admin Shows No Bookings

Backend API and Bot Worker are probably not using the same database. Check `DATABASE_URL` on both Railway services.

### Backup Command Cannot Find `pg_dump`

Install PostgreSQL client tools locally, or run the command from an environment that includes them.

### Restore Command Cannot Find `pg_restore`

Install PostgreSQL client tools locally, or use Railway shell/tools with Postgres utilities available.

### SQLite Backup Is Empty or Old

Make sure local processes are stopped or idle, then run the backup again.
