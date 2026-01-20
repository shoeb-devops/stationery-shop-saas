#!/bin/bash

# Exit on error
set -e

echo "Waiting for PostgreSQL..."

# Wait for database to be ready
while ! nc -z db 5432; do
    sleep 0.1
done

echo "PostgreSQL started"

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Execute the main command
exec "$@"
