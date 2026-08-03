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

  # ── Start uvicorn immediately so Render's health-check passes ────────────────
  # Alembic runs AFTER uvicorn is up. On Render free tier the rolling-deploy
  # health-check times out (~130s) before alembic finishes when it runs first.
  # The schema is already applied on the running instance; new deploys almost
  # never add migrations, so deferring alembic by a few seconds is safe.
  echo "[start] Starting server on port ${PORT:-10000}..."
  python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" \
    --log-level info \
    --loop asyncio &
  UVICORN_PID=$!

  # ── Wait for uvicorn to be reachable before running alembic ─────────────────
  echo "[start] Waiting for server to be ready..."
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:${PORT:-10000}/api/healthz" > /dev/null 2>&1; then
      echo "[start] Server is up after ${i}s."
      break
    fi
    sleep 1
  done

  # ── Run DB migrations (retry up to 3 times with back-off) ───────────────────
  echo "[start] Running DB migrations..."
  MIGRATION_OK=0
  for attempt in 1 2 3; do
    echo "[start] Migration attempt $attempt/3..."
    if timeout 60 env -u PYTHONPATH alembic upgrade head; then
      MIGRATION_OK=1
      echo "[start] Migrations succeeded on attempt $attempt."
      break
    fi
    echo "[start] Migration attempt $attempt failed."
    [ "$attempt" -lt 3 ] && sleep 10
  done

  if [ "$MIGRATION_OK" -ne 1 ]; then
    echo "[warn] Migrations failed after 3 attempts — server continues running."
    echo "[warn] Check DB connectivity; schema may be outdated."
  fi

  # ── Hand off: wait for uvicorn (it is now the main process) ─────────────────
  wait $UVICORN_PID
