from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from django.db.models.fields.related import ForeignKey
from rest_framework import filters
import drfs, json
from drfs.transform import FIELD_MAP
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
            is_staff=True
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
                "DRFS: you don't have permission"
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
            "DRFS: you don't have permission"
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
            "DRFS: you don't have permission"
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
            "DRFS: you don't have permission"
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
            "DRFS: you don't have permission"
        )

    def test_complex_acl(self):
        def test_user(user, apiPoint, expectCode):
            request.user = user
            func = viewset.as_view(apiPoint)
            p = apiPoint.items()[0][1]
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
        viewset = drfs.generate_viewset(modelClass, acl = [
            {
                "principalId": "$unauthenticated",
                "property": ".+",
                "permission": "DENY"
            }, {
                "principalId": "$authenticated",
                "property": "create",
                "permission": "ALLOW"
            }, {
                "principalId": "$authenticated",
                "property": "list",
                "permission": "ALLOW"
            },{
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
