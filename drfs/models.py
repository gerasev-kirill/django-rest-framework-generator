from django.db import models
from django.dispatch import receiver
from jsonfield import JSONField
from django.conf import settings
import os

from . import helpers




class L10nFile(models.Model):
    meta_data = JSONField(default={})
    title = models.CharField(max_length=30, blank=True)
    description = models.CharField(max_length=30, blank=True)
    thumbs = JSONField(default=[])
    file_data = models.FileField()

    def delete_file_data(self):
        if not self.file_data:
            return
        helpers.delete_l10nFile(self)
        self.file_data.delete(save=False)

    def save(self, *args, **kwargs):
        options = kwargs.get('options', {})
        if kwargs.has_key('options'):
            del kwargs['options']

        if self.file_data and not kwargs.get('ignore_processing', False):
            helpers.process_l10nFile(self, options=options)
            super(L10nFile, self).save(*args, **kwargs)
        else:
            if kwargs.has_key('ignore_processing'):
                del kwargs['ignore_processing']
            super(L10nFile, self).save(*args, **kwargs)




@receiver(models.signals.pre_delete, sender=L10nFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes file from filesystem
    when corresponding `L10nFile` object is deleted.
    """
    instance.delete_file_data()
