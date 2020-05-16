#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
    if os.environ.get("VSCODE_DEBUGGER", False):
        import ptvsd

        ptvsd_port = os.environ.get("PORT_PTVSD", 5678)

        try:
            ptvsd.enable_attach(address=("0.0.0.0", ptvsd_port))
            print("Started ptvsd at port %s." % ptvsd_port)
        except OSError:
            print("ptvsd port %s already in use." % ptvsd_port)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
