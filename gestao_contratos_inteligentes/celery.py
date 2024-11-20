from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Configuração padrão do Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestao_contratos_inteligentes.settings')

app = Celery('gestao_contratos_inteligentes')

# Carregar configurações do Django usando o namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir automaticamente tarefas em apps instalados
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
