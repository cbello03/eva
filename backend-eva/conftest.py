"""Root conftest for pytest-django.

Overrides the database to use an in-memory SQLite instance so tests
can run without a PostgreSQL server. Also swaps Redis-backed caches
and channel layers for in-memory alternatives.
"""

import pytest

_SQLITE_DB = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


def pytest_configure(config) -> None:
    from django.conf import settings

    # Override DB to SQLite in-memory
    settings.DATABASES = _SQLITE_DB

    # Use a simple in-memory cache (no Redis needed for tests)
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "memory://localhost",
        }
    }
    # Use in-memory channel layer for tests
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

    # Prevent Celery/Redis connections during tests
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "cache+memory://"

    # Replace the connection handler entirely so it uses the SQLite config
    import django.db
    django.db.connections = django.db.ConnectionHandler(_SQLITE_DB)


@pytest.fixture(scope="session")
def django_db_modify_db_settings():
    """Ensure SQLite in-memory is used (called by pytest-django before DB setup)."""
    from django.conf import settings
    import django.db

    settings.DATABASES = _SQLITE_DB
    django.db.connections = django.db.ConnectionHandler(_SQLITE_DB)
