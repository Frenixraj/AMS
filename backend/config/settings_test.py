"""
SQLite test settings — use when PostgreSQL is unavailable locally.

  python manage.py test --settings=config.settings_test
"""

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
