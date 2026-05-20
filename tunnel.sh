#!/bin/bash
# Запускает cloudflare tunnel и автоматически обновляет vite.config.js

echo "Запускаем туннель..."
cloudflared tunnel --url http://localhost:5173 2>&1 | while read -r line; do
  echo "$line"
  if [[ "$line" =~ https://([a-z0-9-]+\.trycloudflare\.com) ]]; then
    URL="${BASH_REMATCH[1]}"
    sed -i '' "s/allowedHosts: \[\".*\"\]/allowedHosts: [\"$URL\"]/" miniapp/vite.config.js
    echo ""
    echo "✓ vite.config.js обновлён: $URL"
    echo "✓ Обнови URL в BotFather на: https://$URL"
    echo ""
  fi
done
