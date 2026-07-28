"""
Local development settings (SQLite) — no PostgreSQL required.

  python manage.py runserver --settings=config.settings_local
"""

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}
