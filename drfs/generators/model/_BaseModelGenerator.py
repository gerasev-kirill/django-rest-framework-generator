from ... import helpers
from ..field_definition import DjangoFieldDefinition






class BaseModelGenerator(object):
    default_fields_map = {}
    default_model_class = None


    def __init__(self, model_definition, module_name, **kwargs):
        model_name = model_definition.get('name', None)
        if not model_name:
            raise "DRFS - generators: Please provide model name field 'name' in  model definition"
        self.model_definition = model_definition
        self.model_name = str(model_name)
        self.module_name = str(module_name)


    def field_definition_to_django(self, field_name, field_params):
        field = DjangoFieldDefinition()

        if self.default_fields_map.has_key(field_params['type']):
            field.field_class = self.default_fields_map[field_params['type']]
        else:
            try:
                field.field_class = helpers.import_class(field_params['type'])
            except ImportError:
                raise ValueError("DRFS - generators: No such field type '"+field_params['type']+"'. Field declared in '"+self.model_name+"' model")

        return field



    def to_django_model(self):
        fields = {
            '__module__': self.module_name
        }
        fields_definition = self.model_definition.get('properties', {}).items() + \
            self.model_definition.get('relations', {}).items()

        for field_name, field_params in fields_definition:
            if type(field_params) != type({}):
                raise Exception("DRFS - generators: Expect 'field_params' to be dict. Got '" + str(type(field_params)) + "'")
            if not field_params.get('type', None):
                raise Exception("DRFS - generators: No 'field' property in field_params definition for field generation")
            convert_func = getattr(self, field_params['type'] + '_field_definition_to_django', None)
            convert_func = convert_func or self.field_definition_to_django

            field = convert_func(field_name, field_params)
            fields[field_name] = field.field_class(
                *field.args,
                **field.kwargs
            )


        base_class = helpers.import_class(
            self.model_definition.get('base', self.default_model_class)
        )
        model_cls = type(self.model_name, (base_class,), fields)
        setattr(model_cls, 'DRFS_MODEL_DEFINITION', self.model_definition)
        return model_cls
