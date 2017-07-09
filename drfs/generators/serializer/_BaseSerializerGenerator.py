
from ...models import L10nFile as L10nFileModelClass
from ...serializers.models import L10nFile as L10nFileSerializerClass
from ... import helpers

try:
    from drf_loopback_js_filters.serializers import LoopbackJsSerializerMixin
except:
    class LoopbackJsSerializerMixin(object):
        pass




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
        hidden_fields = kwargs.get('hidden_fields', self.model_definition.get('hidden', None))
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
            modeldef_fields = self.model_definition.get('properties', {}).items() + \
                self.model_definition.get('relations', {}).items()

            for field_name, field_params in modeldef_fields:
                if field_params.get('hidden', False) and field_name in all_fields:
                    self.allowed_fields.remove(field_name)


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

        for k,v in self.serializer_field_mapping.items():
            if isinstance(django_field, k):
                serializer_class = v

        if not serializer_class and params.get('type', None) in self.model_relation_types:
            serializer_class, serializer_args, serializer_kwargs = self.build_relational_serializer(
                django_field,
                params
            )
            if params.get('_serializer', {}).get('read_only', False):
                serializer_kwargs['read_only'] = True

        return serializer_class, serializer_args, serializer_kwargs


    def to_serializer(self):
        if self.model_class == L10nFileModelClass:
            return L10nFileSerializerClass

        fields_serializers = {}
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
            if modeldef_fields.get(field.name, {}).get('_serializer', {}).get('read_only', False):
                read_only_fields.append(field.name)

        meta = {
            'model': self.model_class,
            'fields': self.allowed_fields,
            'read_only_fields': read_only_fields
        }

        class DRFS_Serializer(object):
            class Meta:
                model = meta['model']
                fields = meta['fields']
                read_only_fields = meta['read_only_fields']

        base_class = []
        if self.model_definition.get('serializer', {}).get('base', None):
            base_class = [
                helpers.import_class(c)
                for c in self.model_definition['serializer']['base']
            ]
        elif self.default_serializer_class:
            base_class = [self.default_serializer_class]

        base_class.insert(0, LoopbackJsSerializerMixin)
        base_class.append(DRFS_Serializer)

        _cls = type(self.model_name, tuple(base_class), fields_serializers)
        setattr(_cls, 'DRFS_MODEL_DEFINITION', self.model_definition)
        return _cls
