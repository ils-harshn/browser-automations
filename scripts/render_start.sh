#!/usr/bin/env bash
set -euo pipefail

export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/opt/render/project/src/.playwright-browsers}"

# Browsers from the build step may not be on disk at runtime; install into the app directory.
python -m playwright install chromium

exec gunicorn --bind "0.0.0.0:${PORT}" --timeout 120 --workers 1 app:app
