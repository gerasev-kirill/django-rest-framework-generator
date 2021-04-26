from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from rest_framework.response import Response
import drfs
from drfs.decorators import action
from . import models


class ViewsetAcl(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.anonymous = AnonymousUser()
        self.user = User.objects.create_user(
            username='test',
            email='test@mail.com',
            password='test'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@mail.com',
            password='admin',
            is_superuser=True
        )

    def test_everyone(self):
        def test_user_deny(user):
            request.user = user
            response = viewset.as_view({'get': 'list'})(request)
            self.assertEqual(
                response.status_code,
                403
            )
            self.assertEqual(
                response.data['detail'],
                "DRFS: Permission denied by acl"
            )

        def test_user_allow(user):
            request.user = user
            response = viewset.as_view({'get': 'list'})(request)
            self.assertEqual(
                response.status_code,
                200
            )
            self.assertEqual(
                response.data,
                []
            )


        modelClass = models.TestModel
        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$everyone",
            "property": ".+",
            "permission": "DENY"
        }])

        request = self.factory.get('/')
        test_user_deny(self.anonymous)
        test_user_deny(self.user)
        test_user_deny(self.admin)

        #

        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$everyone",
            "property": ".+",
            "permission": "ALLOW"
        }])

        request = self.factory.get('/')
        test_user_allow(self.anonymous)
        test_user_allow(self.user)
        test_user_allow(self.admin)



    def test_unauthenticated(self):
        modelClass = models.TestModel
        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$unauthenticated",
            "property": ".+",
            "permission": "DENY"
        }])
        request = self.factory.get('/')

        request.user = self.anonymous
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertEqual(
            response.data['detail'],
            "DRFS: Permission denied by acl"
        )

        request.user = self.user
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data,
            []
        )



    def test_authenticated(self):
        modelClass = models.TestModel
        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$authenticated",
            "property": ".+",
            "permission": "DENY"
        }])
        request = self.factory.get('/')

        request.user = self.anonymous
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data,
            []
        )

        request.user = self.user
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertEqual(
            response.data['detail'],
            "DRFS: Permission denied by acl"
        )


    def test_owner(self):
        modelClass = models.TestModelWithOwner
        obj = modelClass.objects.create(
            owner = self.user
        )
        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$owner",
            "property": ".+",
            "permission": "DENY"
        }])
        request = self.factory.get('/')

        request.user = self.anonymous
        response = viewset.as_view({'get': 'retrieve'})(request, pk=obj.pk)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data['owner'],
            obj.pk
        )

        request.user = self.user
        response = viewset.as_view({'get': 'retrieve'})(request, pk=obj.pk)
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertEqual(
            response.data['detail'],
            "DRFS: Permission denied by acl"
        )
        obj.delete()


    def test_admin(self):
        modelClass = models.TestModel
        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$admin",
            "property": ".+",
            "permission": "DENY"
        }])
        request = self.factory.get('/')

        request.user = self.anonymous
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data,
            []
        )

        request.user = self.user
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data,
            []
        )

        request.user = self.admin
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertEqual(
            response.data['detail'],
            "DRFS: Permission denied by acl"
        )


    def test_django_permissions(self):
        modelClass = models.TestModel
        viewset = drfs.generate_viewset(modelClass, acl = [{
            "principalId": "$everyone",
            "property": ".+",
            "permission": "DENY"
        },{
            "principalId": "$djangoPermissions",
            "requiredCodename": "tests.view_testmodel",
            "property": ".+",
            "permission": "ALLOW"
        }])
        request = self.factory.get('/')

        # anon
        request.user = self.anonymous
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertEqual(
            response.data['detail'],
            "DRFS: Permission denied by acl"
        )
        # user without permission
        request.user = self.user
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            403
        )
        self.assertEqual(
            response.data['detail'],
            "DRFS: Permission denied by acl"
        )
        # user with permission
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from .models import TestModel
        user = self.user
        permission, created = Permission.objects.get_or_create(
            codename='view_testmodel',
            content_type=ContentType.objects.get(model=TestModel.__name__.lower())
        )
        user.user_permissions.add(permission)

        request.user = User.objects.get(username='test')
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data,
            []
        )

        # admin (allow all)
        request.user = self.admin
        response = viewset.as_view({'get': 'list'})(request)
        self.assertEqual(
            response.status_code,
            200
        )
        self.assertEqual(
            response.data,
            []
        )



    def test_complex_acl(self):
        def test_user(user, apiPoint, expectCode):
            request.user = user
            func = viewset.as_view(apiPoint)
            p = list(apiPoint.items())[0][1]
            if p in ['list', 'create']:
                response = func(request)
            else:
                response = func(request, pk=obj.pk)
            self.assertEqual(
                response.status_code,
                expectCode
            )
            return response.data


        modelClass = models.TestModelWithOwner
        obj = modelClass.objects.create(
            owner = self.user
        )

        class SpecialMixin(object):
            @action(detail=False)
            def my_custom_action(self, *args, **kwargs):
                return Response('success')

            @action(methods=['get', 'post'], detail=False)
            def my_custom_action2(self, *args, **kwargs):
                return Response('success')


        viewset = drfs.generate_viewset(modelClass, mixins=[SpecialMixin], acl=[
            {
                "principalId": "$everyone",
                "property": ".+",
                "permission": "DENY"
            }, {
                "principalId": "$authenticated",
                "property": "create",
                "permission": "ALLOW"
            }, {
                "principalId": "$authenticated",
                "property": ["list", "my_custom_action"],
                "permission": "ALLOW"
            }, {
                "principalId": "$unauthenticated",
                "property": "my_custom_action2",
                "permission": "ALLOW"
            } ,{
                "principalId": "$owner",
                "property": "update",
                "permission": "ALLOW"
            }, {
                "principalId": "$owner",
                "property": "destroy",
                "permission": "ALLOW"
            }, {
                "principalId": "$admin",
                "property": ".+",
                "permission": "ALLOW"
            }
        ])

        request = self.factory.get('/')
        test_user(self.anonymous, {'get': 'list'}, 403)
        test_user(self.anonymous, {'get': 'retrieve'}, 403)
        test_user(self.anonymous, {'get': 'my_custom_action'}, 403)
        test_user(self.anonymous, {'get': 'my_custom_action2'}, 200)
        test_user(self.user, {'get': 'my_custom_action2'}, 403)

        request = self.factory.post('/')
        test_user(self.anonymous, {'post': 'my_custom_action2'}, 200)
