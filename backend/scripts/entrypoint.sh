#!/bin/sh
set -e

echo "Waiting for database..."
python <<'PY'
import os, time
import psycopg2

host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
name = os.environ.get("DB_NAME", "assetflow")
user = os.environ.get("DB_USER", "assetflow")
password = os.environ.get("DB_PASSWORD", "assetflow")

for attempt in range(60):
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=name, user=user, password=password
        )
        conn.close()
        print("Database is ready.")
        break
    except Exception as exc:
        print(f"DB not ready ({attempt + 1}/60): {exc}")
        time.sleep(1)
else:
    raise SystemExit("Database never became ready.")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${SEED_DEMO_USERS:-false}" = "true" ]; then
  python manage.py seed_demo_users || true
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 120
