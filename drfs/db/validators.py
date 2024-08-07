import schema, os, json, six
from django.core.exceptions import ValidationError

from ..helpers import fix_field_choices, load_embedded_model


FLOAT_TYPES = tuple([float] + list(six.integer_types))





class EmbeddedValidator:
    errors = {
        'no_such_embedded_model': "Can't find embedded model {model_name} in your apps! Try to create in any your app file embedded_models.json/{model_name}.json"
    }
    types = {
        'string': six.string_types,
        'int': six.integer_types,
        'float': FLOAT_TYPES,
        'number': float,
        'object': dict,
        'array': list,
        'bool': bool,
        'GeoPoint': dict
    }

    def __init__(self, model_name, params={}):
        self.model_name = model_name
        self.model_data = load_embedded_model(model_name)
        if not self.model_data:
            raise ValueError(self.errors['no_such_embedded_model'].format(
                model_name=model_name
            ))

        self.schema = {}
        self.options = {
            'deleteKeyIfValueIn': {},
            'autocleanIdModelKeys': {}
        }

        for name, data in (self.model_data.get('properties', None) or {}).items():
            if data.get('deleteKeyIfValueIn', None):
                self.options['deleteKeyIfValueIn'][name] = data['deleteKeyIfValueIn']
            name, validators = self.build_schema(name, data)
            self.schema[name] = schema.And(*validators)

        for name, data in (self.model_data.get('relations', None) or {}).items():
            if data.get('deleteKeyIfValueIn', None):
                self.options['deleteKeyIfValueIn'][name] = data['deleteKeyIfValueIn']
            if data.get('type', None) == 'embedsManyAsObject' and data.get('key', {}).get('autoclean', False) and data['key'].get('type', None) == 'model':
                self.options['autocleanIdModelKeys'][name] = data['key'].get('model', None)

            self.model_data['relations'][name]['model_data'] = load_embedded_model(data['model'])
            name, validators = self.build_schema(name, data)
            self.schema[name] = validators

        self.schema = schema.Schema(self.schema)
        self.params = params



    def build_schema(self, field_name, params):
        is_required = True
        validators = []

        if not params.get('required', False):
            is_required = False

        if params['type'] != 'any' and params['type'] in self.types:
            def validate_by_type(value):
                if not is_required and value == None:
                    return True
                return isinstance(value, self.types[params['type']])
            validators.append(validate_by_type)

        field = field_name
        if 'default' in params and params['default'] != None:
            field = schema.Optional(field, default=params['default'])
        elif not is_required:
            field = schema.Optional(field)
            if validators:
                validators = [
                    lambda x: isinstance(x, self.types[params['type']]) or x == None
                ]

        if params['type'] in ['int', 'float', 'number']:
            def validate_by_size(validationType):
                def validate(value):
                    if not is_required and value == None:
                        return True
                    if validationType == 'min':
                        return value >= params[validationType]
                    if validationType == 'max':
                        return value <= params[validationType]
                    return True
                validate.__name__ = 'validate_by_size_' + validationType
                return validate
            if 'min' in params:
                validators.append(validate_by_size('min'))
            if 'max' in params:
                validators.append(validate_by_size('max'))

        if params['type'] in ['string']:
            if 'min' in params:
                validators.append(schema.And(
                    lambda x: len(x or '') >= params['min'],
                    error="Field '{field_name}' value is too small. Required {min} chars".format(
                        field_name=field_name,
                        min=params['min']
                    )
                ))
            if 'max' in params:
                validators.append(schema.And(
                    lambda x: len(x or '') <= params['max'],
                    error="Field '{field_name}' value is too long. Allowed max {max} chars".format(
                        field_name=field_name,
                        max=params['max']
                    )
                ))

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
                for c in fix_field_choices(params['choices'])
            ]
            def validate_choices_for_array(value):
                value = value or []
                for v in value:
                    if v not in choices:
                        return False
                return True

            if params['type'] == 'array':
                validators.append(schema.And(
                    validate_choices_for_array,
                    error="Key '{field_name}' value not in choices: {choices}".format(
                        field_name=field_name,
                        choices=choices
                    )
                ))
            else:
                if is_required:
                    validators.append(schema.And(
                        lambda x: x in choices,
                        error="Key '{field_name}' value not in choices: {choices}".format(
                            field_name=field_name,
                            choices=choices
                        )
                    ))
                else:
                    validators.append(schema.And(
                        lambda x: (x in choices) or x == None,
                        error="Key '{field_name}' value not in choices: {choices}".format(
                            field_name=field_name,
                            choices=choices
                        )
                    ))

        if params['type'] == 'embedsOne':
            validator = EmbeddedValidator(params['model'], params=params)
            validators = validator.schema

        if params['type'] == 'embedsMany':
            validator = EmbeddedValidator(params['model'], params=params)
            def embeds_many_validate(value):
                if not is_required and value == None:
                    return None
                if not isinstance(value, (list, dict)):
                    return False
                if isinstance(value, list):
                    for v in value:
                        validator.validate_data(v)
                elif isinstance(value, dict):
                    try:
                        validator.validate_data(value)
                    except Exception as e:
                        # print 'invalid', params['type'], field_name, params['model'], str(e)
                        raise schema.SchemaError("Invalid field '%s': %s" % (field_name, str(e)))
                return True
            # не изменять нижнее поведение!
            validators = [schema.And(embeds_many_validate)]

        if params['type'] == 'embedsManyAsObject':
            validator = EmbeddedValidator(params['model'], params=params)
            def embeds_many_as_object_validate(value):
                if not is_required and value == None:
                    return None
                if not isinstance(value, dict):
                    return False
                for key in value:
                    try:
                        validator.validate_data(value[key])
                    except Exception as e:
                        # print 'invalid', params['type'], field_name, params['model'], str(e)
                        raise schema.SchemaError("Invalid property '%s' in embedsManyAsObject '%s': %s" % (key, field_name, str(e)))
                return True
            # не изменять нижнее поведение!
            validators = schema.And(embeds_many_as_object_validate)

        return field, validators


    def clean_data(self, data):
        if not data:
            return data
        if self.options['deleteKeyIfValueIn']:
            for k in list(data.keys()):
                if data[k] in self.options['deleteKeyIfValueIn'].get(k, []):
                    del data[k]
        for name in self.options['autocleanIdModelKeys']:
            for k in data:
                data[k] = self.clean_id_model_keys_in_data(data[k], model_name=self.options['autocleanIdModelKeys'][name])
        return data


    def clean_id_model_keys_in_data(self, data, model_name=None):
        if not model_name or not isinstance(data, dict):
            return data
        from drfs import get_model

        modelClass = get_model(model_name)
        ids = []
        for key in data.keys():
            try:
                ids.append(int(key))
            except ValueError:
                pass
        known_ids = [
            str(id)
            for id in modelClass.objects.filter(id__in=ids).values_list('id', flat=True)
        ]
        for key in list(data.keys()):
            if key not in known_ids:
                del data[key]
        return data


    def validate_data(self, data):
        if data == None and not self.params.get('required', False):
            return self.params.get('default', None) or None
        try:
            return self.clean_data(self.schema.validate(data))
        except Exception as e:
            raise ValidationError(str(e))

    def __call__(self, data):
        if data == None and not self.params.get('required', False):
            return True
        try:
            self.schema.validate(data)
        except Exception as e:
            raise ValidationError(str(e))
        return True

    def deconstruct(self):
        return 'drfs.db.validators.EmbeddedValidator', [self.model_name], {}
