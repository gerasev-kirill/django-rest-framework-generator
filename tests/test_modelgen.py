from django.test import TestCase
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey, OneToOneField
import drfs, json
from drfs.generators.model import DjangoOrmModelGenerator
from django.core.exceptions import ValidationError

FIELD_MAP = DjangoOrmModelGenerator.model_fields_mapping


class Model(TestCase):

    def test_modelgen(self):
        def test_field(field, settings):
            field_class = FIELD_MAP[settings['type']]
            if not isinstance(field, field_class):
                self.fail("Field '"+field.name+"' is not an instance of "+str(field_class))
            if 'default' in settings:
                # JSONField support for django >= 3.1
                dvalue = field.default
                if callable(dvalue):
                    dvalue = dvalue()
                self.assertEqual(dvalue, settings['default'])
            if 'max' in settings:
                if settings['type'] in ['string']:
                    self.assertEqual(field.max_length, settings['max'])
            if settings['type'] == 'datetime':
                self.assertEqual(
                    field.auto_now_add,
                    settings['auto_now_add']
                )

        modelClass = drfs.generate_model('TestModel.json')
        with open('./tests/models.json/TestModel.json') as f:
            modelJson = json.load(f)
        opts = modelClass._meta

        hidden = [
            "id",
            "TestModelWithRelations_Flat_by_hasOne",
            "TestModelWithRelations_Flat_by_hasMany",
            "TestModelWithRelations_Nested_by_hasOne",
            "TestModelWithRelations_Nested_by_hasMany"
        ]
        for field in opts.get_fields():
            if field.name in hidden:
                continue
            test_field(
                field,
                modelJson['properties'][field.name]
            )

        # test mixin for model
        instance = modelClass.objects.create(string_field="test")
        self.assertEqual(
            instance.string_field,
            'test'
        )
        instance.save(my_prop="world!")
        self.assertEqual(
            instance.string_field,
            'world!'
        )
        self.assertEqual(
            instance.say_hello(),
            "hello %s" % instance.id
        )

    def test_abstract(self):
        TestModelAbstract = drfs.generate_model('TestModelAbstract.json')
        self.assertEqual(
            TestModelAbstract._meta.abstract,
            True
        )
        with open('./tests/models.json/TestModelFromAbstract.json') as f:
            modelJson = json.load(f)
        gen = DjangoOrmModelGenerator(modelJson, 'tests')
        TestModelFromAbstract = gen.to_django_model()

        opts = TestModelFromAbstract._meta
        field_names = [
            f.name
            for f in opts.get_fields()
        ]

        self.assertEqual(
            TestModelFromAbstract._meta.abstract,
            False
        )
        self.assertEqual(
            sorted(field_names), [
            'array_field', 'bool_field', 'datetime_field', 'id', 'int_field',
            'new_field', 'object_field', 'string_field'
        ])


    def test_no_such_file(self):
        self.assertRaisesMessage(
            OSError,
            "No such file or directory: 'NoSuchModel.json'",
            drfs.generate_model,
            'NoSuchModel.json'
        )


    def test_modelgen_field_invalid_type(self):
        self.assertRaisesMessage(
            ValueError,
            "No such field type 'invalid_type'. Field declared in 'TestModelInvalidFieldType' model",
            drfs.generate_model,
            'TestModelInvalidFieldType.json'
        )


    def test_relations_belongs_to(self):
        modelClass = drfs.generate_model('TestModelRalationBelongsTo.json')
        opts = modelClass._meta
        belongs_to_field = opts.get_field('belongs_to_field')
        if not isinstance(belongs_to_field, ForeignKey):
            self.fail(
                "Field 'belongs_to_field' in model 'TestModelRalationBelongsTo' not instance of ForeignKey"
            )
        remote_field = belongs_to_field.remote_field
        self.assertEqual(
            remote_field.model,
            UserModel
        )

    def test_relations_has_one(self):
        modelClass = drfs.generate_model('TestModelRalationHasOne.json')
        opts = modelClass._meta
        has_one_field = opts.get_field('has_one_field')
        if not isinstance(has_one_field, OneToOneField):
            self.fail(
                "Field 'has_one_field' in model 'TestModelRalationHasOne' not instance of OneToOneField"
            )
        remote_field = has_one_field.remote_field
        self.assertEqual(
            remote_field.model,
            UserModel
        )


class Model2(TestCase):
    def test_relations_has_one_drfs(self):
        modelClass = drfs.generate_model('TestModel2.json')
        modelClass = drfs.generate_model('ModelWithRefToTestModel.json')
        opts = modelClass._meta
        has_one_field = opts.get_field('has_one_field')

    def test_relations_embedsManyAsObject(self):
        from drfs.db.fields import EmbeddedManyAsObjectModel
        modelClass = drfs.generate_model('TestModelWithEmbeddedManyAsObject.json')

        field = modelClass._meta.get_field('many_embedded_as_object')
        self.assertTrue(isinstance(field, EmbeddedManyAsObjectModel))

        instance = modelClass.objects.create(many_embedded_as_object={
            '1': {
                'estring': 'test'
            }
        })
        self.assertEqual(
            instance.many_embedded_as_object['1']['estring'],
            'test'
        )
        # autoset
        self.assertEqual(
            instance.many_embedded_as_object['1']['eint'],
            90
        )

        # nested embedded
        instance = modelClass.objects.create(nested_many_embedded_as_object={
            '1': {
                'estring': 'test',
                'one_embedded2': {
                    "eint2": 100
                }
            }
        })
        self.assertDictEqual(
            instance.nested_many_embedded_as_object,
            {'1': {'estring': 'test', 'one_embedded2': {'eint2': 100}, 'eint': 90}}
        )

        # autoclean for model keys
        instance = modelClass.objects.create(many_embedded_as_object_with_model_key={
            '1': {
                'estring': 'test',
                'one_embedded2': {
                    "eint2": 100
                }
            },
            '2': {
                'estring': 'test',
                'one_embedded2': {
                    "eint2": 100
                }
            }
        })
        # none will be saved
        self.assertDictEqual(instance.many_embedded_as_object_with_model_key, {})

        # create object with id == 2
        TestModel = drfs.generate_model('TestModel.json')
        TestModel.objects.create(id=2)

        instance = modelClass.objects.create(many_embedded_as_object_with_model_key={
            '1': {
                'estring': 'test',
                'one_embedded2': {
                    "eint2": 100
                }
            },
            '2': {
                'estring': 'test',
                'one_embedded2': {
                    "eint2": 100
                }
            }
        })
        self.assertDictEqual(
            instance.many_embedded_as_object_with_model_key,
            {
                '2': {
                    'estring': 'test',
                    'eint': 90,
                    'one_embedded2': {
                        "eint2": 100
                    }
                }
            }
        )

        # errors
        self.assertRaisesMessage(
            ValidationError,
            "Wrong keys 'notExists' in {'estring': 'test', 'notExists': 'invalid'}",
            modelClass.objects.create,
            many_embedded_as_object={
                '1': {
                    'estring': 'test',
                    'notExists': 'invalid'
                }
            }
        )

        self.assertRaisesMessage(
            ValidationError,
            "2 should be instance of 'dict'",
            modelClass.objects.create,
            many_embedded_as_object={},
            nested_many_embedded_as_object={
                '1': 2
            }
        )

        self.assertRaisesMessage(
            ValidationError,
            "Wrong keys \'blabla\' in {\'blabla\': 100}",
            modelClass.objects.create,
            many_embedded_as_object={},
            nested_many_embedded_as_object={
                '1': {
                    'blabla': 100
                }
            }
        )
