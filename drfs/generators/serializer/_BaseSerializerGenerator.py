
from ..field_definition import DjangoFieldDefinition
from ...models import L10nFile as L10nFileModelClass
from ...serializers.models import L10nFile as L10nFileSerializerClass
from ... import helpers






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


    def django_relation_field_to_rest_serializer(self, django_field, field_params):
        serializer = DjangoFieldDefinition(
            help_text=getattr(django_field, 'help_text', '')
        )
        return serializer

    def django_field_to_rest_serializer(self, django_field, field_params):
        serializer = DjangoFieldDefinition(
            help_text=getattr(django_field, 'help_text', '')
        )
        field_params = field_params or {}

        for k,v in self.serializer_field_mapping.items():
            if isinstance(django_field, k):
                serializer.field_class = v

        if not serializer.field_class and field_params.get('type', None) in self.model_relation_types:
            return self.django_relation_field_to_rest_serializer(django_field, field_params)
        return serializer


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
            #if field.related_model:
            #    print '=============='
            #    print field.__dict__
            #    print ''
            field_params = self.model_definition.get('properties', {}).get(field.name, None) or \
                self.model_definition.get('relations', {}).get(field.name, None)

            serializer = self.django_field_to_rest_serializer(field, field_params)
            if serializer.field_class:
                fields_serializers[field.name] = serializer.field_class(
                    *serializer.args,
                    **serializer.kwargs
                )
            if modeldef_fields.get(field.name, {}).get('_serializer', {}).get('read_only', False):
                read_only_fields.append(field.name)

        meta = {
            'model': self.model_class,
            'fields': self.allowed_fields,
            'read_only_fields': read_only_fields
        }

        class DRFS_Serializer(object):
            def __init__(self, *args, **kwargs):
                super(DRFS_Serializer, self).__init__(*args, **kwargs)
                context = kwargs.get('context', {})
                request = context.get('request', {})
                lb_fields = getattr(request, 'LB_FILTER_FIELDS', None)

                if lb_fields:
                    if type(lb_fields) != type({}):
                        raise TypeError("LB_FILTER_FIELDS in request context should be 'dict'. Got '"+str(type(lb_fields))+"'")

                    existing = self.fields.keys()
                    if lb_fields.get('only', None):
                        for f in existing:
                            if f not in lb_fields['only']:
                                self.fields.pop(f)
                    elif lb_fields.get('defer', None):
                        for f in lb_fields['defer']:
                            if f in existing:
                                self.fields.pop(f)

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
        base_class.append(DRFS_Serializer)

        serializer_class = type(self.model_name, tuple(base_class), fields_serializers)
        setattr(serializer_class, 'DRFS_MODEL_DEFINITION', self.model_definition)
        return serializer_class
