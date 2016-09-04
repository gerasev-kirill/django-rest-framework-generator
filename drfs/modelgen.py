from django.db import models

from . import helpers
from .transform import Fields, Relations




class ModelGenFactory(type):
    def __new__(self, definition, module_name, **kwargs):
        f = Fields(definition.get('properties', {}), definition.get('name', 'NonameModel'))
        fields = f.transform()

        r = Relations(definition.get('relations', {}))
        relations = r.transform()


        name = str(definition['name'])
        base_class = helpers.import_class(
            definition['base']
        )
        bases = (base_class,)
        fields.update(relations)
        fields['__module__'] = module_name
        new_cls = type(name, bases, fields)
        setattr(new_cls, 'MODEL_GEN', definition)
        return new_cls
