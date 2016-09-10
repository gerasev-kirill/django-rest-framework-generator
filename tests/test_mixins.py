from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User as UserModel
from rest_framework.viewsets import ModelViewSet
from rest_framework import filters

import drfs, json






class Mixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_count(self):
        class CountMixinTest(drfs.mixins.CountModelMixin, ModelViewSet):
            queryset = UserModel.objects.all()
            serializer_class = drfs.generate_serializer(UserModel)
            filter_backends = (filters.DjangoFilterBackend,)
            filter_fields = {'username':['contains'], }

        for s in ["test string 1", "test string 2", "another string 3"]:
            UserModel.objects.create(
                username=s,
                email=s+"@mail.com",
                password="1"
            )

        request = self.factory.get('/')
        response = CountMixinTest.as_view({'get': 'count'})(request)

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data['count'],
            3
        )


        request = self.factory.get('/?username__contains=test')
        response = CountMixinTest.as_view({'get': 'count'})(request)

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data['count'],
            2
        )
