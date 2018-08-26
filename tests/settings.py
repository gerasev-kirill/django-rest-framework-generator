import os

BASE_DIR = os.path.dirname(__file__)
SECRET_KEY = '--'

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'db.sqlite3'),
    }
}
MEDIA_ROOT = os.path.join(BASE_DIR, 'storage-tests')
MEDIA_URL = 'storage/'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'rest_framework',
    'rest_framework.authtoken',
    'drfs',
    'django_gcs',

    'tests'
]

DJANGO_GCS_BUCKET = 'ffffaaaaaaake-bucket',
DJANGO_GCS_PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'key.json')
DJANGO_GCS_BLOB_MAKE_PUBLIC = True
DEFAULT_FILE_STORAGE = 'django_gcs.storage.GoogleCloudStorage'
