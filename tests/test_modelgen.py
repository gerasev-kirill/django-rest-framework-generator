from django.test import TestCase
import drfs, json
from drfs.transform import FIELD_MAP


class Model(TestCase):
    def get_model_json(self):
        with open('./tests/models.json/TestModel.json') as f:
            modelJson = json.load(f)
        return modelJson

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
        modelJson = self.get_model_json()
        opts = modelClass._meta

        for field in opts.get_fields():
            if field.name == 'id':
                continue
            test_field(
                field,
                modelJson['properties'][field.name]
            )

    def test_modelgen_fail(self):
        modelClass = drfs.generate_model('TestModelInvalidJson.json')
