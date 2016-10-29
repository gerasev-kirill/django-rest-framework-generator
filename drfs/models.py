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
        path = str(self.file_data)
        for thumb in self.thumbs or []:
            localFilePath = path+".thumb."+thumb+".jpg"
            if not os.path.isabs(localFilePath):
                localFilePath = os.path.join(settings.MEDIA_ROOT, localFilePath)
            try:
                os.remove(localFilePath)
            except:
                pass
        self.file_data.delete(save=False)

    def save(self, *args, **kwargs):
        if self.file_data and not kwargs.get('ignore_processing', False):
            self.file_data.save(self.file_data.name, self.file_data, save=False)
            helpers.process_l10nFile(self)
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
