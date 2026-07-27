import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharm_system.settings')

application = get_wsgi_application()

# Exposed for Vercel Serverless Function handler
app = application
