from django.db import models
from django.db.models import fields
from jsonfield import JSONField
from django.apps import apps
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

    'belongsTo': models.ForeignKey
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
            func = getattr(self, '_' + _type)
            fields[field_name] = func(field_params)
        return fields


class Fields(Base):
    def __init__(self, fields):
        self.data = fields

    def _get_field_defaults(self, params):
        kwargs = {}
        if params.has_key('default'):
            kwargs['default'] = params['default']
        return (FIELD_MAP[params['type']], kwargs)

    def __default(self, field_params):
        field, kwargs = self._get_field_defaults(field_params)
        return field(**kwargs)

    def _string(self, field_params):
        field, kwargs = self._get_field_defaults(field_params)
        kwargs['blank'] = True
        for k,v in field_params.items():
            if k=='max':
                kwargs['max_length'] = v
        return field(**kwargs)

    def _datetime(self, field_params):
        field, kwargs = self._get_field_defaults(field_params)
        for k,v in field_params.items():
            if k=='auto_now_add':
                kwargs['auto_now_add'] = v
        return field(**kwargs)

    def _object(self, field_params):
        return self.__default(field_params)

    def _int(self, field_params):
        return self.__default(field_params)

    def _bool(self, field_params):
        return self.__default(field_params)

    def _array(self, field_params):
        return self.__default(field_params)



class Relations(Base):
    def __init__(self, relations):
        self.data = relations

    def _get_relation_defaults(self, params):
        kwargs = {}
        return (FIELD_MAP[params['type']], kwargs)


    def _belongsTo(self, relation_params):
        field, kwargs = self._get_relation_defaults(relation_params)
        model = helpers.import_class(relation_params['model'])
        args = (model,)
        for k,v in relation_params.items():
            if k=='on_delete':
                kwargs['on_delete'] = getattr(models, v)
        return field(*args, **kwargs)



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
                serializers[_f.name] = ser()
        return {
            'fields': fields,
            'serializers': serializers
        }
