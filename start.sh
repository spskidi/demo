#!/usr/bin/env bash
# Exit on error and print commands as they are executed
set -ex

# Create necessary directories
mkdir -p staticfiles media
chmod -R 755 staticfiles media

# Install dependencies
echo "=== Installing dependencies ==="
pip install -r requirements.txt

# Apply database migrations
echo "=== Applying database migrations ==="
python manage.py migrate --noinput

# Create superuser if no users exist
echo "=== Checking for superuser ==="
if ! python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.exists() else 1)"; then
    echo "Creating superuser..."
    export DJANGO_SUPERUSER_USERNAME=admin
    export DJANGO_SUPERUSER_EMAIL=admin@example.com
    export DJANGO_SUPERUSER_PASSWORD=admin123
    python manage.py createsuperuser --noinput || echo "Superuser creation failed, continuing..."
else
    echo "Superuser already exists"
fi

# Collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

# Start Gunicorn with detailed logging
echo "=== Starting Gunicorn ==="
exec gunicorn edtech_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 2 \
    --worker-class=sync \
    --log-level=debug \
    --access-logfile - \
    --error-logfile - \
    --timeout 120 \
    --preload

echo "=== Application started successfully ==="
