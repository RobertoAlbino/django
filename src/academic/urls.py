"""
Configuracao de URLs para o projeto academic.

A lista `urlpatterns` mapeia URLs para views. Para mais informacoes, veja:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]
