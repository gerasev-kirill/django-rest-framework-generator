from django.db import models
from django.dispatch import receiver
from django.db.models import fields
from jsonfield import JSONField
from django.apps import apps
from django.conf import settings
from rest_framework import fields as rf_fields
import json

from .serializers import fields as drfs_fields
from .db.fields import ListField
from . import helpers


FIELD_MAP = {
    'string': fields.CharField,
    'int': fields.IntegerField,
    'object': JSONField,
    'date': fields.DateField,
    'datetime': fields.DateTimeField,
    'bool': fields.BooleanField,
    'array': ListField,

    'belongsTo': models.ForeignKey,
    'hasOne': models.OneToOneField,
    'hasMany': models.ManyToManyField,
    'embedsMany': ListField
}

FIELD_SERIALIZER_MAP = {
    'ListField': drfs_fields.ListField,
    'JSONField': drfs_fields.JSONField
}



class Base:
    def transform(self):
        fields = {}
        for field_name, field_params in self.data.items():
            _type = field_params['type']
            func = getattr(self, '_' + _type, None)
            if not func:
                func = getattr(self, '_default')
            fields[field_name] = func(field_params, field_name=field_name)
        return fields


def fixChoices(choices):
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


class Fields(Base):
    def __init__(self, fields, modelname):
        self.modelname = modelname
        self.data = fields

    def _get_field_defaults(self, params):
        kwargs = {}
        if params.has_key('default'):
            kwargs['default'] = params['default']

        if params.has_key('choices'):
            kwargs['choices'] = fixChoices(params['choices'])
        if params.has_key('description'):
            kwargs['help_text'] = params['description']
        if params.has_key('required') and params['required'] == False:
            kwargs['blank'] = True
            kwargs['null'] = True

        if FIELD_MAP.has_key(params['type']):
            return (FIELD_MAP[params['type']], kwargs)
        # regular django field
        try:
            f = helpers.import_class(params['type'])
        except ImportError:
            raise ValueError("No such field type '"+params['type']+"'. Field declared in '"+self.modelname+"' model")
        return (f, kwargs)

    def _default(self, field_params, **kwargs):
        field, kwargs = self._get_field_defaults(field_params)
        return field(**kwargs)

    def _string(self, field_params, **kwargs):
        field, kwargs = self._get_field_defaults(field_params)
        if not field_params.get('required', False):
            kwargs['blank'] = True
        for k,v in field_params.items():
            if k=='max':
                kwargs['max_length'] = v
        return field(**kwargs)

    def _datetime(self, field_params, **kwargs):
        field, kwargs = self._get_field_defaults(field_params)
        for k,v in field_params.items():
            if k=='auto_now_add':
                kwargs['auto_now_add'] = v
        return field(**kwargs)

    def _object(self, field_params, **kwargs):
        return self._default(field_params)

    def _int(self, field_params, **kwargs):
        field, kwargs = self._get_field_defaults(field_params)
        if not field_params.get('required', True):
            kwargs['blank'] = True
            kwargs['null'] = True
        return field(**kwargs)

    def _bool(self, field_params, **kwargs):
        return self._default(field_params)

    def _array(self, field_params, **kwargs):
        return self._default(field_params)


REGISTERED_RECEIVERS = {}
@receiver(models.signals.pre_delete)
def on_delete(sender, instance, **kwargs):
    _meta = getattr(sender, '_meta', {})
    model_name = getattr(_meta, 'object_name', None)
    if model_name not in REGISTERED_RECEIVERS.keys():
        return
    fields = REGISTERED_RECEIVERS[model_name].get('delete_embedsMany', {})
    for fname, embedded_model_class in fields.items():
        ids = getattr(instance, fname, [])
        if ids:
            embedded_model_class.objects.filter(id__in=ids).delete()



def register_on_delete_embedsMany(model_class, fields):
    model_name = model_class._meta.object_name
    if REGISTERED_RECEIVERS.has_key(model_name):
        if REGISTERED_RECEIVERS[model_name].has_key('delete_embedsMany'):
            return
    else:
        REGISTERED_RECEIVERS[model_name] = {}
    REGISTERED_RECEIVERS[model_name]['delete_embedsMany'] = fields



class Relations(Base):
    def __init__(self, relations, model_class=None):
        self.data = relations
        self.model_class = model_class
        self.receivers = {'embedsMany':{}}

    def _get_relation_defaults(self, params, **kwargs):
        kwargs = {"blank":True, "null":True}
        return (FIELD_MAP[params['type']], kwargs)

    def _get_model_class(self, model_path):
        if model_path=='django.contrib.auth.models.User' or model_path=='AUTH_USER_MODEL':
            if getattr(settings, 'AUTH_USER_MODEL', False):
                return settings.AUTH_USER_MODEL
        if '.' not in model_path:
            return model_path
        return helpers.import_class(model_path)


    def _belongsTo(self, relation_params, **kwargs):
        field, kwargs = self._get_relation_defaults(relation_params)
        model = self._get_model_class(relation_params['model'])
        args = (model,)
        for k,v in relation_params.items():
            if k=='on_delete':
                kwargs['on_delete'] = getattr(models, v)
        return field(*args, **kwargs)

    def _hasOne(self, relation_params, **kwargs):
        field, kwargs = self._get_relation_defaults(relation_params)
        model = self._get_model_class(relation_params['model'])
        args = (model,)
        for k,v in relation_params.items():
            if k=='on_delete':
                kwargs['on_delete'] = getattr(models, v)
        return field(*args, **kwargs)

    def _hasMany(self, relation_params, **kwargs):
        field, kwargs = self._get_relation_defaults(relation_params)
        model = self._get_model_class(relation_params['model'])
        args = (model,)
        if 'null' in kwargs.keys():
            del kwargs['null']
        return field(*args, **kwargs)

    def _embedsMany(self, relation_params, field_name=None):
        model = self._get_model_class(relation_params['model'])
        self.receivers['embedsMany'][field_name] = model
        return FIELD_MAP['array'](default=[])

    def register_receivers(self, model_class):
        if self.receivers['embedsMany']:
            register_on_delete_embedsMany(model_class, self.receivers['embedsMany'])



class SerializerFields:
    def __init__(self, django_fields):
        self.data = django_fields

    def __find_serializer(self, django_field):
        ser = None
        if isinstance(django_field, ListField):
            ser = FIELD_SERIALIZER_MAP['ListField']
        elif isinstance(django_field, JSONField):
            ser = FIELD_SERIALIZER_MAP['JSONField']
        return ser

    def get_fields_name(self):
        names = []
        for _f in self.data:
            names.append(_f.name)
        return names

    def transform(self, allowed_fields):
        serializers = {}
        fields = []
        for _f in self.data:
            if _f.name not in allowed_fields:
                continue
            fields.append(_f.name)
            ser = self.__find_serializer(_f)
            if ser:
                serializers[_f.name] = ser(help_text=getattr(_f, 'help_text', ''))
        return {
            'fields': fields,
            'serializers': serializers
        }
