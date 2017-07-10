from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User as UserModel
from rest_framework.viewsets import ModelViewSet
from rest_framework import filters
from django.http import Http404

import drfs, json







class CountMixin(TestCase):
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



class FindOneMixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_find(self):
        class FindOneMixinTest(drfs.mixins.FindOneModelMixin, ModelViewSet):
            queryset = UserModel.objects.all()
            serializer_class = drfs.generate_serializer(UserModel, visible_fields=[
                'username',
                'id'
            ])
            filter_backends = (filters.DjangoFilterBackend,)
            filter_fields = {'username':['contains'], }

        for s in ["test string 1", "test string 2", "another string 3"]:
            UserModel.objects.create(
                username=s,
                email=s+"@mail.com",
                password="1"
            )

        request = self.factory.get('/')
        response = FindOneMixinTest.as_view({'get': 'find_one'})(request)

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data['id'],
            1
        )


        request = self.factory.get('/?username__contains=2')
        response = FindOneMixinTest.as_view({'get': 'find_one'})(request)

        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data['id'],
            2
        )
        ##
        #  http 404
        ##
        request = self.factory.get('/?username__contains=http404_name')
        response = FindOneMixinTest.as_view({'get': 'find_one'})(request)

        self.assertEqual(
            response.status_code,
            404
        )
        self.assertEqual(
            response.data['detail'],
            'Not found.'
        )


class UserRegisterLoginLogoutMixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.userFullSerializer = drfs.generate_serializer(
            UserModel,
            visible_fields=[
                'id', 'last_login', 'is_superuser', 'username',
                'first_name', 'last_name', 'email', 'is_staff',
                'is_active', 'date_joined', 'groups', 'user_permissions']
        )
        self.userData = {
            'username': 'Test_User',
            'email': 'Test-email@mail.com',
            'password':'1'
        }

    def test_register(self):

        class UserRegisterLoginLogoutMixinTest(drfs.mixins.UserRegisterLoginLogoutMixin, ModelViewSet):
            queryset = UserModel.objects.all()
            serializer_class = drfs.generate_serializer(UserModel)
            user_serializer_class = self.userFullSerializer

        request = self.factory.post('/', self.userData)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)
        self.assertEqual(
            response.status_code,
            201
        )
        user = response.data['user']
        for key in ['username', 'email']:
            self.assertEqual(
                user[key],
                self.userData[key]
            )
        self.assertEqual(
            user['id'],
            1
        )
        self.assertEqual(
            response.data['userId'],
            1
        )
        self.assertEqual(
            len(response.data['token']),
            40
        )

        data = self.userData.copy()
        del data['password']
        request = self.factory.post('/', data)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data,
            {'password': [u'This field is required.']}
        )


        data = self.userData.copy()
        del data['email']
        request = self.factory.post('/', data)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data,
            {'email': [u'This field is required.']}
        )

        data = self.userData.copy()
        del data['username']
        request = self.factory.post('/', data)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data,
            {'username': [u'This field is required.']}
        )

        # mark username unique for registration

        UserRegisterLoginLogoutMixinTest.user_register_serializer_class = drfs.serializers.rest.UserRegisterEmailUniqueSerializer
        request = self.factory.post('/', self.userData)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)

        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data['non_field_errors'],
            [u'"email" field should be unique.']
        )
        UserModel.objects.all().delete()


    def test_login(self):

        class UserRegisterLoginLogoutMixinTest(drfs.mixins.UserRegisterLoginLogoutMixin, ModelViewSet):
            queryset = UserModel.objects.all()
            serializer_class = drfs.generate_serializer(UserModel)
            user_serializer_class = self.userFullSerializer

        request = self.factory.post('/', self.userData)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)



        request = self.factory.post('/', {
            'username': self.userData['username'],
            'password': self.userData['password']
        })
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'login'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        user = response.data['user']
        for key in ['username', 'email']:
            self.assertEqual(
                user[key],
                self.userData[key]
            )
        self.assertEqual(
            user['id'],
            1
        )
        self.assertEqual(
            response.data['userId'],
            1
        )
        self.assertEqual(
            len(response.data['token']),
            40
        )

        request = self.factory.post('/', {
            'username': self.userData['username'],
            'password': "WRONGPASS"
        })
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'login'})(request)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data['non_field_errors'],
            [u'Unable to log in with provided credentials.']
        )

        request = self.factory.post('/', {
            'username': 'NOUSER',
            'password': "WRONGPASS"
        })
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'login'})(request)
        self.assertEqual(
            response.status_code,
            400
        )
        self.assertEqual(
            response.data['non_field_errors'],
            [u'Unable to log in with provided credentials.']
        )
        UserModel.objects.all().delete()


    def test_logout(self):

        class UserRegisterLoginLogoutMixinTest(drfs.mixins.UserRegisterLoginLogoutMixin, ModelViewSet):
            queryset = UserModel.objects.all()
            serializer_class = drfs.generate_serializer(UserModel)
            user_serializer_class = self.userFullSerializer

        request = self.factory.post('/', self.userData)
        response = UserRegisterLoginLogoutMixinTest.as_view({'post': 'register'})(request)

        token = response.data['token']

        request = self.factory.delete('/', HTTP_AUTHORIZATION="Token " + token)
        response = UserRegisterLoginLogoutMixinTest.as_view({'delete': 'logout'})(request)
        self.assertEqual(
            response.status_code,
            204
        )
        self.assertEqual(
            response.data,
            {}
        )


        request = self.factory.delete('/', HTTP_AUTHORIZATION="Token " + token)
        response = UserRegisterLoginLogoutMixinTest.as_view({'delete': 'logout'})(request)
        self.assertEqual(
            response.data,
            {u'detail': u'Invalid token.'}
        )


class QuerysetExistsMixin(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_count(self):
        class QuerysetExistsMixinTest(drfs.mixins.QuerysetExistsModelMixin, ModelViewSet):
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
        response = QuerysetExistsMixinTest.as_view({'get': 'queryset_exists'})(request)
        self.assertEqual(
            response.data['exists'],
            True
        )

        request = self.factory.get('/?username__contains=test')
        response = QuerysetExistsMixinTest.as_view({'get': 'queryset_exists'})(request)
        self.assertEqual(
            response.data['exists'],
            True
        )

        request = self.factory.get('/?username__contains=NONAME')
        response = QuerysetExistsMixinTest.as_view({'get': 'queryset_exists'})(request)
        self.assertEqual(
            response.data['exists'],
            False
        )
