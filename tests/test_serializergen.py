from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey
from rest_framework import exceptions
import drfs, json


class Serializer(TestCase):

    def test_selializergen(self):
        modelClass = drfs.generate_model('TestModel.json')
        with open('./tests/models.json/TestModel.json') as f:
            modelJson = json.load(f)
        serializerClass = drfs.generate_serializer(modelClass)
        opts = serializerClass.Meta
        self.assertEqual(
            opts.model,
            modelClass
        )

        fields = [
            "id",
            "TestModelWithRelations_Flat_by_hasOne",
            "TestModelWithRelations_Flat_by_hasMany",
            "TestModelWithRelations_Nested_by_hasOne",
            "TestModelWithRelations_Nested_by_hasMany"
        ] + list(modelJson['properties'].keys())

        serializer_fields = opts.fields
        fields.sort()
        serializer_fields.sort()

        self.assertEqual(fields, serializer_fields)


    def test_serializergen_with_django_model(self):
        serializerClass = drfs.generate_serializer(UserModel)
        opts = serializerClass.Meta
        self.assertEqual(
            opts.model,
            UserModel
        )
        fields = [
            u'auth_token', 'testmodelwithowner',
            'testmodelwithrelations_flat', 'testmodelwithrelations_nested',
            'testmodelralationbelongsto',
            'testmodelralationbelongsto_withignore404object',
            'testmodelralationhasone',
            u'id', 'password', 'last_login',
            'is_superuser', 'username', 'first_name', 'last_name', 'email',
            'is_staff', 'is_active', 'date_joined', 'groups', 'user_permissions',
        ]
        serializer_fields = opts.fields

        fields.sort()
        serializer_fields.sort()
        self.assertEqual(serializer_fields, fields)


    def test_visible_fields(self):
        serializerClass = drfs.generate_serializer(
            'TestModel.json',
            visible_fields=['int_field', 'string_field']
        )
        opts = serializerClass.Meta
        self.assertEqual(
            sorted(opts.fields),
            ['int_field', 'string_field']
        )


    def test_hidden_fields(self):
        serializerClass = drfs.generate_serializer(
            'TestModel.json',
            hidden_fields=[
                "int_field", "string_field",
                "TestModelWithRelations_Flat_by_hasOne",
                "TestModelWithRelations_Flat_by_hasMany",
                "TestModelWithRelations_Nested_by_hasOne",
                "TestModelWithRelations_Nested_by_hasMany"
            ]
        )
        opts = serializerClass.Meta
        fields = [
            u'id', u'object_field', u'array_field',
            u'datetime_field', u'bool_field'
        ]
        serializer_fields = opts.fields
        fields.sort()
        serializer_fields.sort()

        self.assertEqual(serializer_fields, fields)


    def test_visible_and_hidden_fields(self):
        self.assertRaisesMessage(
            ValueError,
            "You cant use both visible_fields and hidden_fields options with model 'TestModel'",
            drfs.generate_serializer,
            'TestModel.json',
            hidden_fields=['int_field', 'string_field'],
            visible_fields=['int_field']
        )


    def test_hidden_fields_in_json_model(self):
        serializerClass = drfs.generate_serializer('TestModelSerializerHiddenFields.json')
        opts = serializerClass.Meta
        self.assertEqual(
            sorted(opts.fields),
            ['array_field', 'bool_field', 'datetime_field', 'id']
        )



class Operations(TestCase):

    def setUp(self):
        self.user = UserModel.objects.create(
            username='serializer_user',
            email='serializer_user@mail.com'
        )
        self.model_class = drfs.generate_model('TestModelRalationBelongsTo.json')
        self.model_class_wt_ignore = drfs.generate_model('TestModelRalationBelongsTo_withIgnore404Object.json')

    def test_create(self):
        self.assertEqual(
            self.model_class.objects.count(),
            0
        )
        serializerClass = drfs.generate_serializer('TestModelRalationBelongsTo.json')
        ser = serializerClass(data={
            'belongs_to_field': self.user.pk
        })
        self.assertEqual(
            ser.is_valid(),
            True
        )
        instance = ser.create(ser.validated_data)
        self.assertEqual(
            instance.belongs_to_field,
            self.user
        )
        self.model_class.objects.all().delete()

    def test_user_not_found_create(self):
        self.assertEqual(
            self.model_class.objects.count(),
            0
        )
        ##
        #    fail
        ##
        serializerClass = drfs.generate_serializer('TestModelRalationBelongsTo.json')
        ser = serializerClass(data={
            'belongs_to_field': self.user.pk+2
        })
        self.assertEqual(
            ser.is_valid(),
            False
        )
        self.assertEqual(
            ser.errors['belongs_to_field'][0],
            'Invalid pk "'+str(self.user.pk+2)+'" - object does not exist.'
        )

        ###
        #   success
        ###
        serializerClass = drfs.generate_serializer('TestModelRalationBelongsTo_withIgnore404Object.json')
        ser = serializerClass(data={
            'belongs_to_field': self.user.pk+2
        })
        self.assertEqual(
            ser.is_valid(),
            True
        )
        instance = ser.create(ser.validated_data)
        self.assertEqual(
            instance.belongs_to_field,
            None
        )
        self.model_class.objects.all().delete()



class Relations(TestCase):
    def setUp(self):
        self.user = UserModel.objects.create(
            username='serializer_relations_user',
            email='serializer_relations_user@mail.com'
        )
        self.user2 = UserModel.objects.create(
            username='serializer_relations_user2',
            email='serializer_relations_user2@mail.com'
        )
        self.test_model_class = drfs.generate_model('TestModel.json')
        self.test = self.test_model_class.objects.create(string_field='my string')
        self.test_many = [
            self.test_model_class.objects.create(string_field='string 1', int_field=2),
            self.test_model_class.objects.create(string_field='string 2', int_field=3),
            self.test_model_class.objects.create(string_field='string 3', int_field=4),
        ]
        self.test_many_data = [
            {'id': self.test_many[0].pk, 'string_field': 'string 1', 'int_field':2},
            {'id': self.test_many[1].pk, 'string_field': 'string 2', 'int_field':3},
            {'id': self.test_many[2].pk, 'string_field': 'string 3', 'int_field':4},
        ]
        self.maxDiff = None

    def test_relations_flat(self):
        modelClass = drfs.generate_model('TestModelWithRelations_Flat.json')
        serializerClass = drfs.generate_serializer(modelClass)

        instance = modelClass.objects.create(
            belongs_to_field=self.user,
            has_one=self.test,
        )
        instance.has_many.add(*self.test_many)
        instance.save()
        ser = serializerClass(instance)
        ##
        #   serialize
        ##
        self.assertDictEqual(
            dict(ser.data),
            {
                'id': instance.pk,
                'has_one': self.test.pk,
                'has_many': [o.pk for o in self.test_many],
                'belongs_to_field': self.user.pk
            }
        )
        ##
        #   create
        ##
        has_many = [self.test_many[0].pk, self.test_many[2].pk, self.test.pk]
        ser = serializerClass(data={
            'belongs_to_field': self.user.pk,
            'has_many': has_many
        })
        ser.is_valid()
        instance = ser.create(ser.validated_data)

        self.assertEqual(instance.belongs_to_field, self.user)
        self.assertEqual(
            len(instance.has_many.all()),
            3
        )
        pks = [o.pk for o in instance.has_many.all()]
        pks.sort()
        has_many.sort()
        self.assertEqual(pks, has_many)
        ##
        #      update
        ##
        ser = serializerClass(data={
            'id': instance.pk,
            'belongs_to_field': self.user2.pk,
            'has_many': [self.test.pk]
        })
        ser.is_valid()
        instance_updated = ser.update(instance, ser.validated_data)
        self.assertEqual(instance_updated.belongs_to_field, self.user2)
        self.assertEqual(
            len(instance_updated.has_many.all()),
            1
        )
        self.assertEqual(
            instance_updated.has_many.all()[0],
            self.test
        )

    def test_relations_nested(self):
        modelClass = drfs.generate_model('TestModelWithRelations_Nested.json')
        serializerClass = drfs.generate_serializer(modelClass)

        instance = modelClass.objects.create(
            belongs_to_field=self.user,
            has_one=self.test,
        )
        instance.has_many.add(*self.test_many)
        instance.save()
        ser = serializerClass(instance)


        self.assertDictEqual(
            dict(ser.data),
            {
                'id': instance.pk,
                'has_one': {
                    'id': self.test.pk,
                    'string_field': 'my string'
                },
                'has_many': self.test_many_data,
                'belongs_to_field': {
                    'id': self.user.pk,
                    'username': 'serializer_relations_user',
                    'email': 'serializer_relations_user@mail.com'
                }
            }
        )


    def test_embedsManyAsObject(self):
        modelClass = drfs.generate_model('TestModelWithEmbeddedManyAsObject.json')
        TestModel = drfs.generate_model('TestModel.json')
        serializerClass = drfs.generate_serializer(modelClass)

        test_model_id = TestModel.objects.last().id
        instance = modelClass.objects.create(
            many_embedded_as_object={
                '1': {
                    'estring': 'test'
                }
            },
            nested_many_embedded_as_object={
                '1': {
                    'estring': 'test2',
                    'one_embedded2': {
                        "eint2": 200
                    }
                }
            },
            many_embedded_as_object_with_model_key={
                str(test_model_id): {
                    'estring': 'test3',
                    'one_embedded2': {
                        "eint2": 100
                    }
                },
                '500': {
                    'estring': 'test4',
                    'one_embedded2': {
                        "eint2": 100
                    }
                }
            }
        )


        ser = serializerClass(instance)
        self.assertDictEqual(
            ser.data['many_embedded_as_object'],
            {
                "1": {
                    "estring": "test",
                    "eint": 90
                }
            }
        )
        self.assertDictEqual(
            ser.data['nested_many_embedded_as_object'],
            {
                "1": {
                    "estring": "test2",
                    "one_embedded2": {
                        "eint2": 200
                    },
                    "eint": 90
                }
            }
        )
        self.assertDictEqual(
            ser.data['many_embedded_as_object_with_model_key'],
            {
                str(test_model_id): {
                    "estring": "test3",
                    "one_embedded2": {
                        "eint2": 100
                    },
                    "eint": 90
                }
            }
        )

        ##
        #      update
        ##
        ser = serializerClass(data={
            'many_embedded_as_object_with_model_key':{
                str(test_model_id): {
                    'eint': 5,
                    'one_embedded2': {}
                },
                'nnnnooooonn': {
                    'eint': 6,
                }
            }
        })
        ser.is_valid()
        instance_updated = ser.update(instance, ser.validated_data)

        self.assertDictEqual(
            ser.validated_data['many_embedded_as_object_with_model_key'],
            {str(test_model_id): {'eint': 5, 'one_embedded2': {'eint2': 90}}}
        )
        self.assertDictEqual(
            instance_updated.many_embedded_as_object_with_model_key,
            {str(test_model_id): {'eint': 5, 'one_embedded2': {'eint2': 90}}}
        )



class SerializerExpandable(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserModel.objects.create(
            username='serializer_relations_user',
            email='serializer_relations_user@mail.com'
        )
        self.user2 = UserModel.objects.create(
            username='serializer_relations_user2',
            email='serializer_relations_user2@mail.com'
        )
        TestModel = drfs.generate_model('TestModel.json')
        self.m1 = TestModel.objects.create(int_field=100)
        self.m2 = TestModel.objects.create(int_field=200)
        self.test_model_class = drfs.generate_model('TestModelWithRelations_Flat.json')
        self.orig_test_model_definition = self.test_model_class.DRFS_MODEL_DEFINITION

        self.test1 = self.test_model_class.objects.create(belongs_to_field=self.user)
        self.test1.has_many.add(self.m1, self.m2)
        self.test2 = self.test_model_class.objects.create(belongs_to_field=self.user2)
        self.test2.has_many.add(self.m1)
        self.test3 = self.test_model_class.objects.create()
        self.test3.has_many.add(self.m2)
        self.maxDiff = None


    def test_expand_simple(self):
        model = self.test_model_class
        model.DRFS_MODEL_DEFINITION = self.orig_test_model_definition.copy()
        model.DRFS_MODEL_DEFINITION['serializer'] = {
            'expandableFields': {
                'belongs_to_field': {
                    'visible_fields': ['id', 'username']
                }
            }
        }
        serializerClass = drfs.generate_serializer(model)
        serializerClass.Meta.raise_expand_exception = True

        request = self.factory.get('/')

        # invalid expansion
        request.query_params = {'expand': 'bloblob'}
        ser = serializerClass(self.test1, context={'request': request})
        self.assertRaisesMessage(
            exceptions.ValidationError,
            "Query param 'expand' is invalid JSON",
            ser.get_fields
        )

        request.query_params = {'expand': '[]'}
        ser = serializerClass(self.test1, context={'request': request})
        self.assertRaisesMessage(
            exceptions.ValidationError,
            "Query param 'expand' is invalid. Allowed dict only",
            ser.get_fields
        )

        # unknown field
        request.query_params = {'expand': json.dumps({'unknown_field': True})}
        ser = serializerClass(self.test1, context={'request': request})
        self.assertRaisesMessage(
            exceptions.ValidationError,
            "Expand: field 'unknown_field' is not expandable",
            ser.get_fields
        )

        # known field but not in expansion
        request.query_params = {'expand': json.dumps({'has_many': True})}
        ser = serializerClass(self.test1, context={'request': request})
        self.assertRaisesMessage(
            exceptions.ValidationError,
            "Expand: field 'has_many' is not expandable",
            ser.get_fields
        )

        # user1
        request.query_params = {'expand': json.dumps({'belongs_to_field': True})}
        ser = serializerClass(self.test1, context={'request': request})
        self.assertDictEqual(ser.data, {
            "id": 1,
            "belongs_to_field": 1,
            "$belongs_to_field": {
                "id": 1,
                "username": "serializer_relations_user"
            },
            "has_one": None,
            "has_many": [
                1,
                2
            ]
        })

        # no user
        request.query_params = {'expand': json.dumps({'belongs_to_field': True})}
        ser = serializerClass(self.test3, context={'request': request})
        self.assertDictEqual(ser.data, {
            "id": 3,
            "belongs_to_field": None,
            "$belongs_to_field": None,
            "has_one": None,
            "has_many": [
                2
            ]
        })


        # many-to-many
        model.DRFS_MODEL_DEFINITION = self.orig_test_model_definition.copy()
        model.DRFS_MODEL_DEFINITION['serializer'] = {
            'expandableFields': {
                'belongs_to_field': {
                    'visible_fields': ['id', 'username']
                },
                'has_many': {
                    'visible_fields': ['id', 'int_field']
                }
            }
        }
        serializerClass = drfs.generate_serializer(model)
        serializerClass.Meta.raise_expand_exception = True

        request.query_params = {'expand': json.dumps({'belongs_to_field': True, 'has_many': True})}
        ser = serializerClass(self.test1, context={'request': request})
        self.assertDictEqual(ser.data, {
            "id": 1,
            "belongs_to_field": 1,
            "$belongs_to_field": {
                "id": 1,
                "username": "serializer_relations_user"
            },
            "has_one": None,
            "has_many": [1,2],
            "$has_many": [
                {
                    "id": 1,
                    "int_field": 100
                },
                {
                    "id": 2,
                    "int_field": 200
                }
            ]
        })
