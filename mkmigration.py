import django, sys, os
from django.conf import settings


settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
            }
        },
        BASE_DIR=os.path.dirname(__file__),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'rest_framework',
            'rest_framework.authtoken',
            'drfs',
            'migration'
        )
)

django.setup()
