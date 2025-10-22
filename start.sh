#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create database directory if it doesn't exist
mkdir -p $(dirname "$(find . -name db.sqlite3 | head -1)" 2>/dev/null || echo "db")

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create superuser if no users exist
echo "Creating superuser if needed..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.exists():
    username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created successfully')
else:
    print('Superuser already exists'
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn edtech_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 1 \
    --log-level=info \
    --timeout 120
