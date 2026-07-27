#!/usr/bin/env bash
# Start FastAPI + Vite for local development.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/.local/bin:${PATH}"
export PYTHONPATH="${ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"

cleanup() {
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

echo "API  http://127.0.0.1:${API_PORT}"
echo "Web  http://127.0.0.1:${WEB_PORT}"

(
  cd "${ROOT}/backend"
  uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT}"
) &
(
  cd "${ROOT}/frontend"
  npm run dev -- --host 0.0.0.0 --port "${WEB_PORT}"
) &
wait
