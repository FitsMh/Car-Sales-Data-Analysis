import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '基于Django系统.settings')

application = get_wsgi_application()
