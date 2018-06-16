from django.test import TestCase
from django.contrib.auth.models import User as UserModel
from django.db.models.fields.related import ForeignKey, OneToOneField
import drfs, json
from drfs.generators.model import DjangoOrmModelGenerator

FIELD_MAP = DjangoOrmModelGenerator.model_fields_mapping


class Model(TestCase):

    def test_modelgen(self):
        def test_field(field, settings):
            field_class = FIELD_MAP[settings['type']]
            if not isinstance(field, field_class):
                self.fail("Field '"+field.name+"' is not an instance of "+str(field_class))
            if settings.has_key('default'):
                self.assertEqual(field.default, settings['default'])
            if settings.has_key('max'):
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
            field_names,
            [u'id', u'object_field', u'int_field', u'array_field', u'datetime_field', u'string_field', u'bool_field', u'new_field']
        )


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
