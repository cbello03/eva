"""Root conftest for pytest-django.

Overrides the database to use an in-memory SQLite instance so tests
can run without a PostgreSQL server. Also swaps Redis-backed caches
and channel layers for in-memory alternatives.
"""

import django
from django.conf import settings


def pytest_configure(config) -> None:
    # Override DB before Django fully initializes
    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    # Use a simple in-memory cache (no Redis needed for tests)
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    # Disable channel layers for unit tests
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }
