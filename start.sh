#!/bin/bash
  # No set -e — we handle errors explicitly so alembic hangs don't kill the script

  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$SCRIPT_DIR"

  export SECRET_KEY="${SECRET_KEY:-change-this-secret-key-in-production}"
  export API_KEY="${API_KEY:-change-this-api-key-in-production}"
  export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
  export REDIS_QUEUE_URL="${REDIS_QUEUE_URL:-redis://localhost:6379/1}"

  # Fix DATABASE_URL format for asyncpg (only if DATABASE_URL is non-empty)
  if [ -n "${DATABASE_URL:-}" ]; then
    DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g; s|postgres://|postgresql+asyncpg://|g')
    DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|?sslmode=disable||g; s|&sslmode=disable||g; s|?sslmode=require||g; s|&sslmode=require||g')
    export DATABASE_URL
    echo "[start] DATABASE_URL driver: ${DATABASE_URL%%://*}"
  else
    echo "[start] WARNING: DATABASE_URL is not set — using fallback in config"
  fi

  mkdir -p sessions data/training logs

  echo "[start] Running DB migrations (timeout 45s)..."
  # Use timeout so a hung DB connection doesn't block startup forever
  timeout 45 env -u PYTHONPATH alembic upgrade head 2>&1 || echo "[warn] Migration skipped or timed out — continuing anyway"

  echo "[start] Starting server on port ${PORT:-10000}..."
  exec python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" \
    --log-level info \
    --loop asyncio
  