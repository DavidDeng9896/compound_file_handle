#!/usr/bin/env bash
# Expose local Vite (default :5173, proxies /api) via Cloudflare quick tunnel.
set -euo pipefail
WEB_PORT="${WEB_PORT:-5173}"
TARGET="http://127.0.0.1:${WEB_PORT}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found. Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/" >&2
  exit 1
fi

if ! curl -sf --connect-timeout 2 "${TARGET}/" >/dev/null; then
  echo "Frontend not reachable at ${TARGET}." >&2
  echo "Start the app first: ./scripts/dev.sh" >&2
  exit 1
fi

echo "Tunneling ${TARGET} (Ctrl+C to stop)…"
exec cloudflared tunnel --url "${TARGET}" --no-autoupdate
