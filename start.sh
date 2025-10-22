#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies if not already installed
pip install -r requirements.txt

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
cat <<EOF | python manage.py shell || true
import os
from django.contrib.auth import get_user_model

User = get_user_model()

# Only create if no users exist
if not User.objects.exists():
    User.objects.create_superuser(
        username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
        email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'changeme123')
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn edtech_project.wsgi:application \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 2 \
    --worker-class gthread \
    --threads 4 \
    --log-level=info \
    --log-file - \
    --access-logfile - \
    --error-logfile - \
    --timeout 120
