import drfs, json
from django.test import TestCase
from rest_framework.permissions import AllowAny

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
            ()
        )
        self.assertEqual(
            viewset.permission_classes,
            [AllowAny]
        )
