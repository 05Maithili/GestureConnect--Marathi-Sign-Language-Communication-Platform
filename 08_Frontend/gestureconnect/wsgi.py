"""
WSGI config for GestureConnect project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestureconnect.settings')
application = get_wsgi_application()
