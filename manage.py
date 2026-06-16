#!/usr/bin/env python
"""Django command-line utility."""
import os
import sys


def main() -> None:
    """Entry point for Django administrative commands."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate your environment or run via `uv run`."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
