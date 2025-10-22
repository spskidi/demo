#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create database directory if it doesn't exist
DB_DIR=$(dirname "$(find . -name db.sqlite3 | head -1)" 2>/dev/null || echo "db")
mkdir -p "$DB_DIR"

# Apply database migrations
echo "=== Applying database migrations ==="
python manage.py migrate --noinput

# Create superuser if no users exist
echo "=== Checking for superuser ==="
if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('SUPERUSER_EXISTS' if User.objects.exists() else 'SUPERUSER_NOT_FOUND')" | grep -q 'SUPERUSER_NOT_FOUND'; then
    echo "Creating superuser..."
    export DJANGO_SUPERUSER_USERNAME=admin
    export DJANGO_SUPERUSER_EMAIL=admin@example.com
    export DJANGO_SUPERUSER_PASSWORD=admin123
    python manage.py createsuperuser --noinput
    echo "Superuser created successfully"
else
    echo "Superuser already exists"
fi

# Collect static files
echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

# Set proper permissions
chmod -R 755 staticfiles
chmod -R 755 media

# Start Gunicorn
echo "=== Starting Gunicorn ==="
exec gunicorn edtech_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 3 \
    --log-level=info \
    --timeout 120 \
    --worker-class=gthread \
    --threads 4

echo "=== Application started successfully ==="
