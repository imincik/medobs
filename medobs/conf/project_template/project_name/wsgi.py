"""
WSGI config for webgis project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "devproj.settings")

from medobs.reservations.models import Command
Command.objects.select_for_update().update(is_running=False)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
