from django.core.management import call_command
from django.apps import AppConfig



class MigrationAppConfig(AppConfig):
    name = 'migration'
    verbose_name = "Application"
    def ready(self):
        call_command('makemigrations', 'drfs')

default_app_config= 'migration.MigrationAppConfig'
