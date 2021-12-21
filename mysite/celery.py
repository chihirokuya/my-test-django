
import os
from celery import Celery

# celeryで使うDjangoの設定ファイル(settings.py)を指定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

app = Celery('mysite')

# Djangoのconfigファイルをceleryのconfigとして使う宣言、celery用のconfigファイルを作ってもいい。
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()