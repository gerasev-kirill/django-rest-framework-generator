from ..helpers import fix_field_choices, field_choice_description_to_varname




class EmbeddedOpenapiSchemaGenerator:
    def __init__(self, model_name: str, model_data: dict):
        self.model_name = model_name
        self.model_data = model_data
        self.schema = {
            "type": "object",
            "properties": {}
        }
        required = []

        for name, data in (self.model_data.get('properties', None) or {}).items():
            schema = self.build_schema(name, data)
            if not schema:
                continue
            if schema.get('required'):
                required.append(name)
                del schema['required']
            self.schema['properties'][name] = schema

        for name, data in (self.model_data.get('relations', None) or {}).items():
            schema = self.build_schema(name, data)
            if not schema:
                continue
            if schema.get('required'):
                required.append(name)
                del schema['required']
            self.schema['properties'][name] = schema

        if required:
            self.schema['required'] = required
            


    def get_model_schema(self):
        return self.schema


    def build_schema(self, field_name, params):
        if params.get('hidden', None):
            return None

        schema = {
            "type": "object",
            "required": True
        }
        if not params.get('required', False):
            schema['required'] = False
        if not schema['required']:
            del schema['required']
            schema['nullable'] = True

        if params['type'] in ['any', 'object']:
            return schema

        if params['type'] in ['int', 'float', 'number']:
            if params['type'] == 'int':
                schema['type'] = 'integer'
            else:
                schema['type'] = 'number'
            if 'min' in params:
                schema['minimum'] = params['min']
            if 'max' in params:
                schema['maximum'] = params['max']

        if params['type'] in ['string']:
            schema['type'] = 'string'
            if 'min' in params:
                schema['minLength'] = params['min']
            if 'max' in params:
                schema['maxLength'] = params['max']

        if 'choices' in params:
            choices = fix_field_choices(params['choices'])
            # openapi <= 3.1
            schema['enum'] = [
                c[0]
                for c in choices
            ]
            schema['x-enum-varnames'] = [
                field_choice_description_to_varname(c[1])
                for c in choices
            ]
            # openapi > 3.1
            schema['oneOf'] = [
                {
                    'title': choices[i][1], 
                    'const': schema['x-enum-varnames'][i], 
                    'description': choices[i][1]
                }
                for i in range(len(choices))
            ]

        if params['type'] == 'bool':
            schema['type'] = 'boolean'

        if params['type'] == 'GeoPoint':
            schema['$ref'] = self.model_name_to_openapi_ref('GeoPoint')

        if params['type'] == 'embedsOne':
            schema['$ref'] = self.model_name_to_openapi_ref(params['model'])

        if params['type'] == 'embedsMany':
            schema['type'] = 'array'
            schema['items'] = {
                '$ref': self.model_name_to_openapi_ref(params['model'])
            }

        if params['type'] == 'embedsManyAsObject':
            schema['additionalProperties'] = {
                '$ref': self.model_name_to_openapi_ref(params['model'])
            }
        return schema



    def model_name_to_openapi_ref(self, name):
        if name == 'L10nBaseString':
            return '#/components/schemas/node_modules/vue3-bootstrap5/Bootstrap5/interfaces/TranslatableString'
        if name == 'GeoPoint':
            return '#/components/schemas/node_modules/vue3-bootstrap5/Bootstrap5/interfaces/GeoPoint'
        if name in ['VariableDescription', 'L10nUrl', 'SiteRedirection']:
            return "#/components/schemas/embedded/builtin/{name}".format(name=name)
        return "#/components/schemas/embedded/{name}".format(name=name)

