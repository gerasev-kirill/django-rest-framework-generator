from rest_framework import serializers
from .transform import SerializerFields
from . import helpers





class SerializerGenFactory(type):
    def __new__(self, model_class, **kwargs):
        from .models import L10nFile as L10nFileModelClass
        from .serializers.models import L10nFile as L10nFileSerializerClass
        if model_class == L10nFileModelClass:
            return L10nFileSerializerClass

        _fields = model_class._meta.get_fields()
        definition = getattr(model_class, 'MODEL_GEN', {})


        model_name = str(definition.get('name', None))
        if not model_name:
            model_name = model_class._meta.object_name



        visible_fields = kwargs.get('visible_fields', None)
        hidden_fields = kwargs.get('hidden_fields', definition.get('hidden', []))
        if visible_fields and hidden_fields:
            raise ValueError(
                "You cant use both visible_fields and hidden_fields options with model '"+ model_name +"'"
            )

        s = SerializerFields(_fields)
        all_fields = s.get_fields_name()
        allowed_fields = []
        field_params = {}
        modelgen_fields = definition.get('properties', {})
        modelgen_fields.update(
            definition.get('relations', {})
        )


        if visible_fields:
            for name in s.get_fields_name():
                if name in visible_fields:
                    allowed_fields.append(name)
        elif hidden_fields:
            for name in s.get_fields_name():
                if name not in hidden_fields:
                    allowed_fields.append(name)
        else:
            allowed_fields = all_fields

            for name, params in modelgen_fields.items():
                if params.get('hidden', False) and name in all_fields:
                    allowed_fields.remove(name)

        data = s.transform(allowed_fields)

        class SerializerMeta(serializers.HyperlinkedModelSerializer):
            def __init__(self, *args, **kwargs):
                super(SerializerMeta, self).__init__(*args, **kwargs)
                context = kwargs.get('context', {})
                request = context.get('request', {})
                lb_fields = getattr(request, 'LB_FILTER_FIELDS', {})
                if lb_fields:
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
                model = model_class
                fields = data['fields']

        def generate_embeds_many_serializer(child_model_class, _field_name):
            child_ser = SerializerGenFactory(child_model_class)
            def get_data(self, obj):
                ids = getattr(obj, _field_name, [])
                if not ids:
                    return []
                ser = child_ser(child_model_class.objects.filter(pk__in=ids), many=True)
                return ser.data
            return get_data

        for name, params in modelgen_fields.items():
            if params['type'] == 'embedsMany':
                child_model_class = helpers.import_class(params['model'])
                setattr(
                    SerializerMeta,
                    'get_'+name,
                    generate_embeds_many_serializer(child_model_class, name)
                )
                data['serializers'][name] = serializers.SerializerMethodField()
                continue

            _serializer = params.get('_serializer', None)
            if not _serializer:
                continue
            if _serializer.has_key('returns'):
                r = _serializer['returns']
                field_name = r.replace('property:', '').replace(' ','')
                def wrapper(name, field_name):
                    def method(self, obj):
                        if name and not field_name:
                            obj = getattr(obj, name, None)
                        elif field_name and ',' in field_name and obj:
                            obj = getattr(obj, name, None)
                            if not obj:
                                return {}
                            nested_data = {}
                            for n in field_name.split(','):
                                o = getattr(obj, n, '--#NOVALUE#--')
                                if o!='--#NOVALUE#--':
                                    nested_data[n] = o
                            return nested_data
                        elif field_name and field_name != 'self' and obj:
                            obj = getattr(obj, name, None)
                            obj = getattr(obj, field_name, None)
                        elif ',' in field_name and not obj:
                            return {}
                        return obj
                    return method
                setattr(
                    SerializerMeta,
                    'get_'+name,
                    wrapper(name, field_name)
                )
                data['serializers'][name] = serializers.SerializerMethodField()
            if _serializer.get('read_only', False):
                def method(self, obj):
                    return obj
                setattr(SerializerMeta, 'get_'+name, method)
                data['serializers'][name] = serializers.SerializerMethodField()






        bases = (SerializerMeta,)
        new_cls = type(model_name, bases, data['serializers'])
        return new_cls
