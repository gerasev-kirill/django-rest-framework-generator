import drfs, json
from django.test import TestCase, RequestFactory
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User as UserModel

from . import models


class Viewset(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserModel.objects.create(username='Viewset-test')

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

    def test_selializergen_with_expand(self):
        modelClass = models.TestModelWithRelations_Flat
        modelClass.DRFS_MODEL_DEFINITION['serializer'] = {
            'expandableFields': {
                'belongs_to_field': {
                    'visible_fields': ['id', 'username']
                }
            }
        }
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

        modelClass.objects.create(belongs_to_field=self.user)

        request = self.factory.get('/?expand=' + json.dumps({'belongs_to_field': True}))
        request.query_params = {
            'expand': json.dumps({'belongs_to_field': True})
        }
        response = viewset.as_view({'get': 'list'})(request)
        self.assertListEqual(response.data, [{
            "id": 1,
            "belongs_to_field": 1,
            "$belongs_to_field": {
                "id": 1,
                "username": "Viewset-test"
            },
            "has_one": None,
            "has_many": []
        }])
