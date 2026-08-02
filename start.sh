#!/bin/bash
  # No set -e — we handle errors explicitly

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

  echo "[start] Running DB migrations (timeout 120s)..."
  # Do not start a partially migrated application. The membership gate depends
  # on the current schema, so a skipped migration can silently bypass it.
  if ! timeout 120 env -u PYTHONPATH alembic upgrade head; then
    echo "[fatal] Database migration failed or timed out; refusing to start."
    exit 1
  fi

  echo "[start] Starting server on port ${PORT:-10000}..."
  exec python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" \
    --log-level info \
    --loop asyncio
  