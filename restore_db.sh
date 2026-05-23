#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_FILE="${1:-}"

if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: ./restore_db.sh <backup-file>" >&2
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
  if ! command -v pg_restore >/dev/null 2>&1; then
    echo "pg_restore is required for PostgreSQL restores." >&2
    exit 1
  fi

  echo "About to restore PostgreSQL database from: $BACKUP_FILE"
  echo "This can overwrite production data."
  read -r -p "Type RESTORE to continue: " CONFIRM
  if [[ "$CONFIRM" != "RESTORE" ]]; then
    echo "Restore cancelled."
    exit 1
  fi

  pg_restore "$BACKUP_FILE" --dbname "$DATABASE_URL" --clean --if-exists --no-owner --no-privileges
  echo "PostgreSQL restore completed."
  exit 0
fi

DB_PATH="${SQLITE_DB_PATH:-$ROOT_DIR/massage_bot.sqlite3}"
if [[ -f "$DB_PATH" ]]; then
  SAFETY_COPY="$DB_PATH.before_restore_$(date +%Y%m%d_%H%M%S)"
  mv "$DB_PATH" "$SAFETY_COPY"
  echo "Previous SQLite database moved to: $SAFETY_COPY"
fi

cp "$BACKUP_FILE" "$DB_PATH"
echo "SQLite restore completed: $DB_PATH"
