"""
WSGI config for Vajra project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""
# this uses the guvicorn,uwsgi 
import os
# its a server btw the webserve rand the django application 
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Vajra.settings")

application = get_wsgi_application()

# Expose 'app' for Vercel deployment
app = application
