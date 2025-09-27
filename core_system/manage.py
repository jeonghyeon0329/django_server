#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import operator
from dotenv import load_dotenv

load_dotenv()

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_system.settings')

    try:
        if operator.eq(len(sys.argv), 2) and operator.eq(sys.argv[1], "runserver"):
            host = os.getenv("DJANGO_RUN_IP")
            port = os.getenv("DJANGO_RUN_PORT")
            sys.argv.append(f"{host}:{port}")
    except Exception as e:
        print(f"[manage.py] failed to inject host/port: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
