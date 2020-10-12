# -*- coding: utf-8 -*-
import django, json, copy
from rest_framework.serializers import CharField
from .validators import EmbeddedValidator


if django.VERSION >= (3,1,0):
    from django.db.models import JSONField as JSONFieldBase
    from django.core.serializers.json import DjangoJSONEncoder

    '''
        https://docs.djangoproject.com/en/3.1/ref/models/fields/
        If you give the field a default, ensure it’s an immutable object, such as a str,
        or a callable object that returns a fresh mutable object each time,
        such as dict or a function.
        Providing a mutable default object like default={} or default=[] shares the one object between all model instances.
    '''

    class JSONField(JSONFieldBase):
        def __init__(self, *args, **kwargs):
            if 'encoder' not in kwargs:
                kwargs['encoder'] = DjangoJSONEncoder
            self.__default_value = kwargs.get('default', None)
            if self.__default_value is not None and not callable(self.__default_value):
                kwargs['default'] = kwargs['default'].__class__
            super(JSONField, self).__init__(*args, **kwargs)

        def get_default(self):
            """Return the default value for this field."""
            if self.__default_value is not None:
                return copy.deepcopy(self.__default_value)
            return self._get_default()


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
    from jsonfield.fields import JSONFieldBase, models

    class JSONField(JSONFieldBase, models.TextField):
        def __init__(self, *args, encoder=None, decoder=None, **kwargs):
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
