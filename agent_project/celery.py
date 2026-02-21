import os
from celery import Celery

# Define o módulo de settings padrão do Django para o Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_project.settings')

app = Celery('agent_project')

# Carrega configuração do Django settings usando o namespace CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descobre tasks em todos os INSTALLED_APPS
app.autodiscover_tasks()
