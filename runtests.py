import django, sys, os
from django.conf import settings

BASE_DIR = os.path.dirname(__file__)

settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
            }
        },
        BASE_DIR=BASE_DIR,
        MEDIA_ROOT=os.path.join(BASE_DIR, 'storage-tests'),
        MEDIA_URL='storage/',
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'rest_framework',
            'rest_framework.authtoken',
            'drfs',
            'django_gcs',

            'tests'
        ),
        DJANGO_GCS_BUCKET='ffffaaaaaaake-bucket',
        DJANGO_GCS_PRIVATE_KEY_PATH=os.path.join(BASE_DIR, 'key.json'),
        DJANGO_GCS_BLOB_MAKE_PUBLIC=True,
        DEFAULT_FILE_STORAGE='django_gcs.storage.GoogleCloudStorage'
)

try:
    # Django <= 1.8
    from django.test.simple import DjangoTestSuiteRunner
    test_runner = DjangoTestSuiteRunner(verbosity=1)
except ImportError:
    # Django >= 1.8
    django.setup()
    from django.test.runner import DiscoverRunner
    test_runner = DiscoverRunner(verbosity=1)

failures = test_runner.run_tests(['tests.test_embedded_models'])
#failures = test_runner.run_tests(['tests'])
if failures:
    sys.exit(failures)
