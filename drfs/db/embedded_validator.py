import schema, os, json

def load_embedded_model(name):
    from django.apps import apps
    model_schema = None

    for app in apps.get_app_configs():
        fpath = os.path.join(app.path, 'embedded_models.json', name+'.json')
        if not os.path.isfile(fpath):
            continue
        with open(fpath) as f:
            model_schema = json.load(f)
        break
    return model_schema


def fix_choices(choices):
    if not isinstance(choices[0], tuple) and not isinstance(choices[0], list):
        if isinstance(choices[0], tuple) or isinstance(choices[0], list):
            return tuple([
                tuple(c)
                for c in choices
            ])
        return tuple([
            (c,c)
            for c in choices
        ])
    return tuple(choices)





class EmbeddedValidator:
    errors = {
        'no_such_embedded_model': "Can't find embedded model {model_name} in your apps! Try to create in any your app file embedded_models.json/{model_name}.json"
    }
    types = {
        'string': str,
        'int': int,
        'float': float,
        'number': float,
        'object': dict,
        'array': list
    }

    def __init__(self, model_name, params={}):
        self.model_data = load_embedded_model(model_name)
        if not self.model_data:
            raise ValueError(self.errors['no_such_embedded_model'].format(
                model_name = model_name
            ))

        self.schema = {}
        for name, data in (self.model_data.get('properties', None) or {}).items():
            name, validators = self.build_schema(name, data)
            self.schema[name] = schema.And(*validators)
        for name, data in (self.model_data.get('relations', None) or {}).items():
            name, validators = self.build_schema(name, data)
            self.schema[name] = validators

        self.schema = schema.Schema(self.schema)



    def build_schema(self, field_name, params):
        is_required = True
        validators = []

        if not params.get('required', False):
            is_required = False

        if params['type'] in self.types:
            validators.append(self.types[params['type']])

        field = field_name
        if 'default' in params:
            field = schema.Optional(field, default=params['default'])
        elif not is_required:
            field = schema.Optional(field)

        if params['type'] in ['int', 'float', 'number']:
            if 'min' in params:
                validators.append(lambda x: x >= params['min'])
            if 'max' in params:
                validators.append(lambda x: x <= params['max'])
        if params['type'] in ['string']:
            if 'min' in params:
                validators.append(lambda x: len(x or '') >= params['min'])
            if 'max' in params:
                validators.append(lambda x: len(x or '') <= params['max'])

        if params['type'] == 'object':
            if is_required:
                validators.append(lambda x: isinstance(x, dict))
            else:
                validators.append(lambda x: isinstance(x, dict) or x == None)
        if params['type'] == 'array':
            if is_required:
                validators.append(lambda x: isinstance(x, list))
            else:
                validators.append(lambda x: isinstance(x, list) or x == None)

        if 'choices' in params:
            choices = [
                c[0]
                for c in fix_choices(params['choices'])
            ]
            if is_required:
                validators.append(lambda x: x in choices)
            else:
                validators.append(lambda x: (x in choices) or x == None)


        if params['type'] == 'embedsOne':
            validator = EmbeddedValidator(params['model'], params=params)
            validators = validator.schema

        return field, validators


    def validate_data(self, data):
        if data == None and not self.params.get('required', False):
            return self.params.get('default', None) or None
        return self.schema.validate(data)
