from django.test import TestCase
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey
from rest_framework import filters
import drfs, json
from drfs.transform import FIELD_MAP
from . import models


class Viewset(TestCase):

    def test_selializergen(self):
        modelClass = models.TestModel
        serializerClass = drfs.generate_serializer(modelClass)
        viewset = drfs.generate_viewset(modelClass)

        self.assertEqual(
            viewset.queryset.model,
            modelClass
        )
        self.assertEqual(
            viewset.serializer_class.Meta.fields,
            serializerClass.Meta.fields
        )
        self.assertEqual(
            viewset.serializer_class.Meta.model,
            modelClass
        )
        self.assertEqual(
            viewset.filter_backends,
            (filters.DjangoFilterBackend,)
        )
        self.assertEqual(
            viewset.permission_classes,
            [drfs.permissions.django.Everyone]
        )
        print viewset.__dict__
