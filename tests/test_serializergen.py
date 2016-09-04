from django.test import TestCase
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey
import drfs, json
from drfs.transform import FIELD_MAP


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
        self.assertEqual(
            opts.fields,
            ['id'] + modelJson['properties'].keys()
        )


    def test_serializergen_with_django_model(self):
        serializerClass = drfs.generate_serializer(UserModel)
        opts = serializerClass.Meta
        self.assertEqual(
            opts.model,
            UserModel
        )
        self.assertEqual(
            opts.fields,
            [u'id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined', 'groups', 'user_permissions']
        )


    def test_visible_fields(self):
        serializerClass = drfs.generate_serializer(
            'TestModel.json',
            visible_fields = ['int_field', 'string_field']
        )
        opts = serializerClass.Meta
        self.assertEqual(
            opts.fields,
            ['int_field', 'string_field']
        )


    def test_hidden_fields(self):
        serializerClass = drfs.generate_serializer(
            'TestModel.json',
            hidden_fields = ['int_field', 'string_field']
        )
        opts = serializerClass.Meta
        self.assertEqual(
            opts.fields,
            [u'id', u'object_field', u'array_field', u'datetime_field', u'bool_field']
        )


    def test_visible_and_hidden_fields(self):
        self.assertRaisesMessage(
            ValueError,
            "You cant use both visible_fields and hidden_fields options with model 'TestModel'",
            drfs.generate_serializer,
            'TestModel.json',
            hidden_fields = ['int_field', 'string_field'],
            visible_fields = ['int_field']
        )


    def test_hidden_fields_in_json_model(self):
        serializerClass = drfs.generate_serializer('TestModelSerializerHiddenFields.json')
        opts = serializerClass.Meta
        self.assertEqual(
            opts.fields,
            [u'id', u'array_field', u'datetime_field', u'bool_field']
        )
