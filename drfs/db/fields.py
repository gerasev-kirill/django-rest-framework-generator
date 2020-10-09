# -*- coding: utf-8 -*-
import django, json, copy
from rest_framework.serializers import CharField
from .validators import EmbeddedValidator


if django.VERSION[0] >= 3 and django.VERSION[1] >= 1:
    from django.db.models import JSONField as BaseJSONField

    '''
        https://docs.djangoproject.com/en/3.1/ref/models/fields/
        If you give the field a default, ensure it’s an immutable object, such as a str,
        or a callable object that returns a fresh mutable object each time,
        such as dict or a function.
        Providing a mutable default object like default={} or default=[] shares the one object between all model instances.
    '''
    def get_default_value(value):
        def get_value():
            return copy.deepcopy(value)
        return get_value


    class JSONField(BaseJSONField):
        def __init__(self, *args, **kwargs):
            if 'default' in kwargs and not callable(kwargs['default']):
                kwargs['default'] = get_default_value(kwargs['default'])
            super(JSONField, self).__init__(*args, **kwargs)


    class BaseEmbedded(JSONField):
        embedded_validator = None
        def __init__(self, *args, **kwargs):
            if 'embedded_model_name' in kwargs:
                self.embedded_model_name = kwargs['embedded_model_name']
                del kwargs['embedded_model_name']
                self.embedded_validator = EmbeddedValidator(self.embedded_model_name)
                kwargs['validators'] = kwargs.get('validators', None) or []
                kwargs['validators'].append(EmbeddedValidator(self.embedded_model_name))
            super(BaseEmbedded, self).__init__(*args, **kwargs)

        def _validate_value(self, value):
            raise NotImplementedError

        def get_prep_value(self, value):
            if value is None:
                return value
            return json.dumps(
                self._validate_value(value),
                cls=self.encoder
            )

else:
    from jsonfield import JSONField

    class BaseEmbedded(JSONField):
        embedded_validator = None
        def __init__(self, *args, **kwargs):
            if 'embedded_model_name' in kwargs:
                self.embedded_model_name = kwargs['embedded_model_name']
                del kwargs['embedded_model_name']
                self.embedded_validator = EmbeddedValidator(self.embedded_model_name)
                kwargs['validators'] = kwargs.get('validators', None) or []
                kwargs['validators'].append(EmbeddedValidator(self.embedded_model_name))
            super(BaseEmbedded, self).__init__(*args, **kwargs)

        def _validate_value(self, value):
            raise NotImplementedError

        def get_db_prep_value(self, value, connection, prepared=False):
            """Convert JSON object to a string"""
            if self.null and value is None:
                return None
            return json.dumps(
                self._validate_value(value),
                **self.dump_kwargs
            )




### -------------------------------------------------------------------
#
#           FIELDS
#
### -------------------------------------------------------------------


class ListField(JSONField):
    pass


class GeoPoint(JSONField):
    pass


class TimeZoneSerializer(CharField):
    pass


class EmbeddedOneModel(BaseEmbedded):
    def _validate_value(self, value):
        if not self.embedded_validator:
            return value
        return self.embedded_validator.validate_data(value)


class EmbeddedManyModel(BaseEmbedded):
    def _validate_value(self, value):
        if not self.embedded_validator:
            return value
        i = 0
        for item in value or []:
            value[i] = self.embedded_validator.validate_data(item)
            i += 1
        return value
