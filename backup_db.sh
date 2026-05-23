#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [[ -n "${DATABASE_URL:-}" ]]; then
  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "pg_dump is required for PostgreSQL backups." >&2
    exit 1
  fi

  OUT="$BACKUP_DIR/backup_$TIMESTAMP.dump"
  pg_dump "$DATABASE_URL" --format=custom --no-owner --no-privileges --file "$OUT"
  echo "PostgreSQL backup written to: $OUT"
  exit 0
fi

DB_PATH="${SQLITE_DB_PATH:-$ROOT_DIR/massage_bot.sqlite3}"
if [[ ! -f "$DB_PATH" ]]; then
  echo "SQLite database not found: $DB_PATH" >&2
  exit 1
fi

OUT="$BACKUP_DIR/massage_bot_$TIMESTAMP.sqlite3"
cp "$DB_PATH" "$OUT"
echo "SQLite backup written to: $OUT"
