"""
WSGI config for {{ project_name }} project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from medobs.reservations.models import Command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

Command.objects.select_for_update().update(is_running=False)

application = get_wsgi_application()
