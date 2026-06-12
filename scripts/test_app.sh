#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

"$PYTHON_BIN" -m unittest discover -s tests
"$PYTHON_BIN" -m py_compile app/__init__.py app/booking.py app/calendar_client.py app/config.py app/database.py app/handlers.py app/i18n.py app/keyboards.py app/main.py app/scheduler.py app/states.py app/validation.py backend/__init__.py backend/main.py
(cd miniapp && npm run build)
