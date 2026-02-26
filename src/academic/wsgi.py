"""
Configuracao WSGI para o projeto academic.

Expoe o objeto WSGI em nivel de modulo com o nome ``application``.

Para mais informacoes, veja:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic.settings')

application = get_wsgi_application()
