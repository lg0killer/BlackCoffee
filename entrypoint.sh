#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate

exec "$@"
