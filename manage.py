#!/usr/bin/env python
"""Командна утиліта Django."""
import os
import sys


def main() -> None:
    """Точка входу для адміністративних команд Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не вдалося імпортувати Django. Активуй середовище або запускай через `uv run`."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
