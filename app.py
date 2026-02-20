import os
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'student.settings')

# This is the WSGI application object that Gunicorn will use
app = get_wsgi_application()

# Also provide 'application' for standard Django tools
application = app
