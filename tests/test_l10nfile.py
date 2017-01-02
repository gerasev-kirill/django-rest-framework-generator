from django.test import TestCase
import drfs, json, os
from django.core.files import File
from django.core.files.images import ImageFile
from drfs.models import L10nFile as L10nFileModelClass
from django.core.files.storage import default_storage
from rest_framework.test import APIRequestFactory

BASE_DIR = os.path.dirname(__file__)
RESOURCE_DIR = os.path.join(BASE_DIR, 'resources')



class L10nFile(TestCase):
    def test_l10nfile(self):
        ffile = ImageFile(open(os.path.join(RESOURCE_DIR, 'django_logo.png')))
        ffile.name = os.path.basename(ffile.name)
        meta = {
            'size': ffile.size,
            'originalName': ffile.name,
            'type': 'image/png'
        }
        l10nFile = L10nFileModelClass(file_data=ffile, meta_data=meta)
        l10nFile.save()
        l10nFile.delete_file_data()
        l10nFile.delete()

    def test_l10nfile_viewset(self):
        L10nFileModelClass.objects.all().delete()
        modelClass = drfs.generate_model('TestModelL10nFile.json')
        viewset = drfs.generate_viewset(modelClass)
        uploadFile = viewset.as_view({'post': 'upload_file'})
        factory = APIRequestFactory()

        instance = modelClass.objects.create()
        request = APIRequestFactory().post('', {'en': open(os.path.join(RESOURCE_DIR, 'django_logo.png'))}, format='multipart')

        response = uploadFile(request, forModelField='mainImg', pk=instance.id)

        self.assertEqual(
            len(response.data['en']['thumbs']),
            3
        )
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            1
        )

        deleteFile = viewset.as_view({'patch': 'delete_file'})
        request = APIRequestFactory().patch('')
        response = deleteFile(request, forModelField='mainImg', pk=instance.id)
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            0
        )

    def test_l10nfile_viewset_options(self):
        L10nFileModelClass.objects.all().delete()
        modelClass = drfs.generate_model('TestModelL10nFile.json')
        viewset = drfs.generate_viewset(modelClass)
        uploadFile = viewset.as_view({'post': 'upload_file'})
        factory = APIRequestFactory()

        thumbSizes = ["20x40", "900x30"]
        instance = modelClass.objects.create()
        request = APIRequestFactory().post('', {
            'en': open(os.path.join(RESOURCE_DIR, 'django_logo.png')),
            'options_thumbSizes': json.dumps(thumbSizes)
        }, format='multipart')

        response = uploadFile(request, forModelField='mainImg', pk=instance.id)

        self.assertEqual(
            set(response.data['en']['thumbs']),
            set(thumbSizes)
        )
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            1
        )

        deleteFile = viewset.as_view({'patch': 'delete_file'})
        request = APIRequestFactory().patch('')
        response = deleteFile(request, forModelField='mainImg', pk=instance.id)
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            0
        )
