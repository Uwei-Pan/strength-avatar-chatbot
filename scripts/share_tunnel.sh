#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8501}"
ORIGIN_URL="http://127.0.0.1:${PORT}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed."
  echo "Install it first, for example: brew install cloudflared"
  exit 1
fi

if ! curl -fsS -I "$ORIGIN_URL" >/dev/null 2>&1; then
  echo "Streamlit is not responding at ${ORIGIN_URL}."
  echo "Open another terminal and run: scripts/run_local.sh"
  exit 1
fi

echo "Creating public tunnel for ${ORIGIN_URL}"
cloudflared tunnel --url "$ORIGIN_URL" --protocol http2
