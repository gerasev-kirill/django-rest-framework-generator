from drfs import helpers
from drfs.serializers.rest import BaseModelSerializer


class BaseSerializerGenerator(object):
    serializer_field_mapping = {}
    default_serializer_class = None
    model_relation_types = []

    def __init__(self, model_class, **kwargs):
        self.allowed_fields = []
        self.model_definition = getattr(model_class, 'DRFS_MODEL_DEFINITION', {})
        self.model_name = self.model_definition.get('name', None)
        self.model_class = model_class
        self.model_fields = model_class._meta.get_fields()

        if not self.model_name:
            self.model_name = model_class._meta.object_name
        self.model_name = str(self.model_name)

        all_fields = [
            field.name
            for field in self.model_fields
        ]
        visible_fields = kwargs.get('visible_fields', None)

        hidden_fields = kwargs.get(
            'hidden_fields',
            self.model_definition.get('serializer', {}).get('hidden', None)
        )
        if visible_fields and hidden_fields:
            raise ValueError(
                "You cant use both visible_fields and hidden_fields options with model '"+ self.model_name +"' for serializer"
            )


        if visible_fields:
            for name in all_fields:
                if name in visible_fields:
                    self.allowed_fields.append(name)
        elif hidden_fields:
            for name in all_fields:
                if name not in hidden_fields:
                    self.allowed_fields.append(name)
        else:
            self.allowed_fields = list(all_fields)
            modeldef_fields = list(self.model_definition.get('properties', {}).items()) + \
                list(self.model_definition.get('relations', {}).items())

            for field_name, field_params in modeldef_fields:
                if field_params.get('serializer', {}).get('hidden', False) and field_name in all_fields:
                    self.allowed_fields.remove(field_name)
        # DeprecationError
        # удалить после миграции всех проектов на новые либы
        if 'hidden' in self.model_definition:
            raise ValueError("Property 'hidden' should not be set on root of model definition for '%s' model. Place it as 'serializer.hidden' property" % model_class.__name__)
        for field_name, field_params in list(self.model_definition.get('properties', {}).items()) + list(self.model_definition.get('relations', {}).items()):
            if '_serializer' in field_params:
                raise ValueError("Property '_serializer' for model '%s' is not allowed anymore. Rename it to 'serializer'" % model_class.__name__)
            if 'hidden' in field_params:
                raise ValueError("Property 'hidden' should not be set inside django field property '%s' for '%s' model. Place it inside 'serializer' property for django field definition" % (
                    field_name, model_class.__name__
                ))


    def get_model_class(self, model_path):
        if '.' in model_path and '.json' not in model_path:
            return helpers.import_class(model_path)
        from ... import generate_model
        if '.json' not in model_path:
            model_path = model_path + '.json'
        return generate_model(model_path)


    def build_relational_serializer(self, django_field, params):
        return None, [], {'help_text': getattr(django_field, 'help_text', '')}


    def build_serializer(self, django_field, params=None):
        serializer_class = None
        serializer_args = []
        serializer_kwargs = {
            'help_text': getattr(django_field, 'help_text', '')
        }
        params = params or {}

        if params.get('type', None) in self.model_relation_types:
            build_relational_serializer = getattr(
                self,
                'build_relational_serializer__'+params['type'],
                self.build_relational_serializer
            )
            serializer_class, serializer_args, serializer_kwargs = build_relational_serializer(django_field, params)

        if not serializer_class:
            for k,v in self.serializer_field_mapping.items():
                if django_field.__class__ == k:
                    serializer_class = v

        if params.get('serializer', {}).get('read_only', False):
            serializer_kwargs['read_only'] = True
        return serializer_class, serializer_args, serializer_kwargs


    def to_serializer(self):
        fields_serializers = {}
        serializer_general_params = self.model_definition.get('serializer', None) or self.model_definition.get('viewset', {}).get('serializer', None) or {}
        read_only_fields = []
        modeldef_fields = self.model_definition.get('properties', {}).copy()
        modeldef_fields.update(self.model_definition.get('relations', {}).copy())

        for field in self.model_fields:
            if field.name not in self.allowed_fields:
                continue
            field_params = self.model_definition.get('properties', {}).get(field.name, None) or \
                self.model_definition.get('relations', {}).get(field.name, None)

            serializer_class, serializer_args, serializer_kwargs = self.build_serializer(field, field_params)
            if serializer_class:
                fields_serializers[field.name] = serializer_class(
                    *serializer_args,
                    **serializer_kwargs
                )
            if modeldef_fields.get(field.name, {}).get('serializer', {}).get('read_only', False):
                read_only_fields.append(field.name)

        for fieldName, field_params in serializer_general_params.get('fields', {}).items():
            if field_params.get('read_only', False):
                try:
                    field = self.model_class._meta.get_field(fieldName)
                except:
                    continue
                read_only_fields.append(fieldName)
                if fieldName not in self.allowed_fields:
                    serializer_class, serializer_args, serializer_kwargs = self.build_serializer(field, field_params)
                    if serializer_class:
                        self.allowed_fields.append(fieldName)
                        fields_serializers[field.name] = serializer_class(
                            *serializer_args,
                            **serializer_kwargs
                        )

            if field_params.get('serializer', {}).get('hidden', False) and fieldName in self.allowed_fields:
                self.allowed_fields.remove(fieldName)

        expandable_fields = self.model_definition.get('serializer', {}).get('expandableFields', {}).copy()
        for k in expandable_fields:
            if k not in self.allowed_fields:
                del expandable_fields[k]

        meta = {
            'model': self.model_class,
            'fields': self.allowed_fields,
            'read_only_fields': read_only_fields,
            'expandable_fields': expandable_fields
        }

        class DRFS_Serializer(object):
            class Meta:
                model = meta['model']
                fields = meta['fields']
                read_only_fields = meta['read_only_fields']
                expandable_fields = meta['expandable_fields']

        base_class = []
        if serializer_general_params.get('base', None):
            base_class = [
                helpers.import_class(c)
                for c in self.model_definition['serializer']['base']
            ]
        elif self.default_serializer_class:
            base_class = [self.default_serializer_class]

        base_class.insert(0, BaseModelSerializer)
        base_class.append(DRFS_Serializer)

        _cls = type(self.model_name, tuple(base_class), fields_serializers)
        setattr(_cls, 'DRFS_MODEL_DEFINITION', self.model_definition)
        return _cls
