#!/usr/bin/env sh
set -e

echo "Waiting for database, then applying migrations..."
# Retry alembic a few times so we tolerate MySQL still warming up.
n=0
until alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 10 ]; then
    echo "Migrations failed after $n attempts." >&2
    exit 1
  fi
  echo "Migration attempt $n failed; retrying in 3s..."
  sleep 3
done

if [ "$SEED" = "true" ]; then
  echo "Seeding database (SEED=true)..."
  python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
