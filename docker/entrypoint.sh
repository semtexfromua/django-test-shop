#!/bin/sh
set -e

echo "→ Database migrations..."
python manage.py migrate --noinput

echo "→ Collecting static files..."
python manage.py collectstatic --noinput

echo "→ Seeding demo catalog..."
python manage.py seed_catalog

exec "$@"
