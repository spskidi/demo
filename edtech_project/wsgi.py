"""
WSGI config for edtech_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_path = Path(__file__).parent
if str(project_path) not in sys.path:
    sys.path.append(str(project_path))

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edtech_project.settings')

# This application object is used by the development server and any WSGI server
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
