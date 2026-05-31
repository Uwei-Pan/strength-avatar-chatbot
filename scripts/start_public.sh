#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8501}"
ORIGIN_URL="http://127.0.0.1:${PORT}"
STREAMLIT_PID=""

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed."
  echo "Install it first, for example: brew install cloudflared"
  exit 1
fi

if [ ! -x ".venv/bin/streamlit" ]; then
  echo "Virtual environment is not ready. Running setup first..."
  scripts/setup_local.sh
fi

cleanup() {
  if [ -n "$STREAMLIT_PID" ] && kill -0 "$STREAMLIT_PID" >/dev/null 2>&1; then
    echo "Stopping Streamlit..."
    kill "$STREAMLIT_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

if curl -fsS -I "$ORIGIN_URL" >/dev/null 2>&1; then
  echo "Using existing Streamlit at ${ORIGIN_URL}"
else
  echo "Starting Streamlit at ${ORIGIN_URL}"
  .venv/bin/streamlit run app.py \
    --server.address 127.0.0.1 \
    --server.port "$PORT" \
    --server.headless true &
  STREAMLIT_PID="$!"

  for _ in $(seq 1 30); do
    if curl -fsS -I "$ORIGIN_URL" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

if ! curl -fsS -I "$ORIGIN_URL" >/dev/null 2>&1; then
  echo "Streamlit did not start at ${ORIGIN_URL}."
  exit 1
fi

echo "Creating public tunnel for ${ORIGIN_URL}"
cloudflared tunnel --url "$ORIGIN_URL" --protocol http2
