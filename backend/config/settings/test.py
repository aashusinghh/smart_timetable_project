from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Remove daphne in tests to avoid Twisted reactor network interface hanging in sandbox
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'daphne']

# Explicitly force SQLite for tests so running pytest or manage.py test never requires MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# In-memory channels so tests never require a live Redis instance
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# In-memory cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Run all Celery tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
