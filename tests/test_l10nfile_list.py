# -*- coding: utf-8 -*-
from django.test import TestCase
import drfs, json, os
from django.core.files import File
from django.core.files.images import ImageFile
from drfs.models import L10nFile as L10nFileModelClass
from django.core.files.storage import default_storage
from rest_framework.test import APIRequestFactory

BASE_DIR = os.path.dirname(__file__)
RESOURCE_DIR = os.path.join(BASE_DIR, 'resources')



class L10nFileList(TestCase):
    def test_l10nfile_list_viewset(self):
        L10nFileModelClass.objects.all().delete()
        modelClass = drfs.generate_model('TestModelL10nFileList.json')
        viewset = drfs.generate_viewset(modelClass)
        uploadFile = viewset.as_view({'post': 'upload_file_to_list'})
        factory = APIRequestFactory()

        instance = modelClass.objects.create()
        request = APIRequestFactory().post('', {'en': open(os.path.join(RESOURCE_DIR, 'django_logo.png'))}, format='multipart')

        response = uploadFile(request, forModelField='files', pk=instance.id)
        files = response.data
        self.assertEqual(
            len(files),
            1
        )
        self.assertEqual(
            len(files[0]['en']['thumbs']),
            3
        )
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            1
        )

        # загружаем еще 1 файл
        request = APIRequestFactory().post('', {'en': open(os.path.join(RESOURCE_DIR, 'django_logo.png'))}, format='multipart')
        response = uploadFile(request, forModelField='files', pk=instance.id)
        files = response.data
        self.assertEqual(
            len(files),
            2
        )
        self.assertEqual(
            len(files[1]['en']['thumbs']),
            3
        )
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            2
        )
        # загружаем на место 0 файла другой файл
        request = APIRequestFactory().post('', {'en': open(os.path.join(RESOURCE_DIR, 'django_logo.png')), 'options_forIdInList':str(files[0]['id'])}, format='multipart')
        response = uploadFile(request, forModelField='files', pk=instance.id)
        new_files = response.data
        self.assertEqual(
            len(new_files),
            2
        )
        self.assertEqual(
            len(files[0]['en']['thumbs']),
            3
        )
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            2
        )
        # проверяем что имена у первых файлов не совпадают
        if new_files[0]['en']['name'] == files[0]['en']['name']:
            self.fail('new_files[0] and files[0] should not be equal by names')
        self.assertEqual(
            new_files[1]['en']['name'],
            files[1]['en']['name'],
        )
        # теперь удаляем файлы
        deleteFile = viewset.as_view({'patch': 'delete_files_inside_list'})
        request = APIRequestFactory().patch('', [{'id': files[0]['id']}], format='json')
        response = deleteFile(request, forModelField='files', pk=instance.id)
        self.assertEqual(
            L10nFileModelClass.objects.all().count(),
            1
        )
        # полностью удалем объект
        destroy = viewset.as_view({'delete': 'destroy'})
        request = APIRequestFactory().delete('')
        response = destroy(request, pk=instance.id)
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
