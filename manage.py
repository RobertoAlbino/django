#!/usr/bin/env python
"""Utilitario de linha de comando do Django para tarefas administrativas."""
import os
import sys
from pathlib import Path


def main():
    """Executa tarefas administrativas."""
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Nao foi possivel importar Django. Verifique se ele esta instalado "
            "e disponivel na variavel de ambiente PYTHONPATH. Voce esqueceu de "
            "ativar um ambiente virtual?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
