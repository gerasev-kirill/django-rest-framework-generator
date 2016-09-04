import django.db
import ast
import json as simplejson
from django.core import exceptions
from django import forms
from jsonfield import JSONField


class ListField(JSONField):
    pass
"""
class ListField(django.db.models.TextField):
    __metaclass__ = django.db.models.Field
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)


    def to_python(self, value):
        if not value:
            value = []
        if isinstance(value, list):
            return value
        return ast.literal_eval(value)


    def get_prep_value(self, value):
        if value is None:
            return value
        return unicode(value)


    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)
"""
