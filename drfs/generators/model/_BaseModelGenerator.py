from ... import helpers
from django_model_changes import ChangesMixin





class BaseModelGenerator(object):
    model_fields_mapping = {}
    default_model_class = None


    def __init__(self, model_definition, module_name, **kwargs):
        model_name = model_definition.get('name', None)
        if not model_name:
            raise "DRFS - generators: Please provide model name field 'name' in  model definition"
        self.model_definition = model_definition
        self.model_name = str(model_name)
        self.module_name = str(module_name)


    def get_model_class(self, model_path):
        if '.' not in model_path:
            return model_path
        return helpers.import_class(model_path)


    def build_field(self, name, params):
        if self.model_fields_mapping.has_key(params['type']):
            field_class = self.model_fields_mapping[params['type']]
        else:
            try:
                field_class = helpers.import_class(params['type'])
            except ImportError:
                raise ValueError("DRFS - generators: No such field type '"+params['type']+"'. Field declared in '"+self.model_name+"' model")

        return field_class, [], {}


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

            convert_func = getattr(self, 'build_field__'+ field_params['type'], None)
            convert_func = convert_func or self.build_field
            field_class, field_args, field_kwargs = convert_func(field_name, field_params)

            fields[field_name] = field_class(
                *field_args,
                **field_kwargs
            )


        base_class = helpers.import_class(
            self.model_definition.get('base', self.default_model_class)
        )
        model_cls = type(self.model_name, (ChangesMixin, base_class), fields)
        setattr(model_cls, 'DRFS_MODEL_DEFINITION', self.model_definition)
        return model_cls
