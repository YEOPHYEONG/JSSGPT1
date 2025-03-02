# jssgpt_project/celery.py
import os
from celery import Celery

# Django settings 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jssgpt_project.settings')

app = Celery('jssgpt_project')

# Django settings의 CELERY 관련 설정을 사용 (namespace='CELERY')
app.config_from_object('django.conf:settings', namespace='CELERY')

# INSTALLED_APPS 내 모든 앱의 tasks.py를 자동으로 로드합니다.
app.autodiscover_tasks()
