from .settings import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}

# The legacy apps contain MySQL-only migrations. Their models are synchronized
# directly for isolated app tests; forestal_bot migrations remain enabled.
MIGRATION_MODULES = {
    "produccion": None,
    "mantenimiento": None,
}
