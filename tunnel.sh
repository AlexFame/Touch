#!/bin/bash
# Запускает бэкенд, бота, miniapp и cloudflare tunnel одной командой

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv/bin/activate"

cleanup() {
  echo ""
  echo "Останавливаем все процессы..."
  kill 0
  exit 0
}
trap cleanup SIGINT SIGTERM

# Бэкенд
echo "[backend] Запуск..."
source "$VENV" && uvicorn backend.main:app --reload --port 8000 &

# Бот
echo "[bot] Запуск..."
source "$VENV" && python -m app.main &

# Miniapp
echo "[miniapp] Запуск..."
cd "$ROOT/miniapp" && npm run dev &
cd "$ROOT"

# Небольшая задержка перед туннелем
sleep 3

# Cloudflare tunnel
echo "[tunnel] Запуск..."
cloudflared tunnel --url http://localhost:5173 2>&1 | while read -r line; do
  echo "$line"
  if [[ "$line" =~ https://([a-z0-9-]+\.trycloudflare\.com) ]]; then
    URL="${BASH_REMATCH[1]}"
    sed -i '' "s/allowedHosts: \[\".*\"\]/allowedHosts: [\"$URL\"]/" "$ROOT/miniapp/vite.config.js"
    echo ""
    echo "✓ URL туннеля: https://$URL"
    echo "✓ Обнови в BotFather: https://$URL"
    echo ""
  fi
done

wait
