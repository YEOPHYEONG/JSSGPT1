import os
from celery import Celery
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jssgpt_project.settings')
django.setup()  # Django 앱을 초기화합니다.

app = Celery('jssgpt_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
