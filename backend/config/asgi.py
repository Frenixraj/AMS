"""
ASGI config for AssetFlow.
"""

import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
apps_dir = str(BASE_DIR / "apps")
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
