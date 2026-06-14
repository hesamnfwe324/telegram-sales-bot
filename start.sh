#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export SECRET_KEY="${SECRET_KEY:-change-this-secret-key-in-production}"
export API_KEY="${API_KEY:-change-this-api-key-in-production}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export REDIS_QUEUE_URL="${REDIS_QUEUE_URL:-redis://localhost:6379/1}"

# Fix DATABASE_URL: must replace postgresql:// BEFORE postgres:// to avoid
# partial match (postgres:// is a substring of postgresql://).
# Also strip sslmode query params that asyncpg does not support.
export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|postgresql://|postgresql+asyncpg://|g; s|postgres://|postgresql+asyncpg://|g')
export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|?sslmode=disable||g; s|&sslmode=disable||g; s|?sslmode=require||g; s|&sslmode=require||g')

mkdir -p sessions data/training logs

echo "[start] Running DB migrations..."
alembic upgrade head || echo "[warn] Migration warning — may already be up to date"

echo "[start] Starting server on port ${PORT:-10000}..."
exec python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}" \
  --log-level info \
  --loop asyncio
