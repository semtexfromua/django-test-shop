#!/bin/sh
set -e

echo "→ Міграції бази даних..."
python manage.py migrate --noinput

echo "→ Збір статики..."
python manage.py collectstatic --noinput

exec "$@"
