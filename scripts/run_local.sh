#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8501}"
ADDRESS="${ADDRESS:-127.0.0.1}"

if [ ! -x ".venv/bin/streamlit" ]; then
  echo "Virtual environment is not ready. Running setup first..."
  scripts/setup_local.sh
fi

echo "Starting Streamlit at http://${ADDRESS}:${PORT}"
.venv/bin/streamlit run app.py \
  --server.address "$ADDRESS" \
  --server.port "$PORT" \
  --server.headless true
