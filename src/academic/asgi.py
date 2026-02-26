"""
Configuracao ASGI para o projeto academic.

Expoe o objeto ASGI em nivel de modulo com o nome ``application``.

Para mais informacoes, veja:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic.settings')

application = get_asgi_application()
