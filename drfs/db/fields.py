# -*- coding: utf-8 -*-
import django, json, copy
from django.conf import settings
from django.db import models
from rest_framework.serializers import CharField
from .validators import EmbeddedValidator


if django.VERSION >= (3,1,0) and getattr(settings, 'DRF_GENERATOR_USE_NATIVE_JSON_FIELD', False):
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
            self._is_default_callable = kwargs.get('default', None) is not None and callable(kwargs.get('default', None))
            super(JSONField, self).__init__(*args, **kwargs)

        def _check_default(self):
            return []

        def get_default(self):
            """Return the default value for this field."""
            if not self._is_default_callable:
                value = self._get_default()
                if isinstance(value, dict) and not value:
                    return {}
                if isinstance(value, list) and not value:
                    return []
                return copy.deepcopy(value)
            return self._get_default()

        def get_prep_value(self, value):
            if value is None:
                return value
            return json.dumps(value, cls=self.encoder, ensure_ascii=False)


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
    try:
        from jsonfield.fields import JSONFieldBase

        class JSONField(JSONFieldBase, models.TextField):
            def __init__(self, *args, encoder=None, decoder=None, **kwargs):
                super(JSONField, self).__init__(*args, **kwargs)

    except ImportError:
        from jsonfield.fields import JSONFieldMixin as JSONFieldBase
        from .forms import JSONFormField

        class JSONField(JSONFieldBase, models.TextField):
            def __init__(self, *args, encoder=None, decoder=None, **kwargs):
                super(JSONField, self).__init__(*args, **kwargs)


            def formfield(self, **kwargs):
                kwargs['form_class'] = JSONFormField
                if hasattr(self, 'embedded_validator'):
                    kwargs['embedded_model_data'] = self.embedded_validator.model_data
                return super().formfield(**kwargs)


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
            if hasattr(self, 'encoder_kwargs'):
                self.encoder_kwargs['ensure_ascii'] = False
            else:
                self.dump_kwargs['ensure_ascii'] = False

        def _validate_value(self, value):
            raise NotImplementedError

        def get_db_prep_value(self, value, connection, prepared=False):
            """Convert JSON object to a string"""
            if self.null and value is None:
                return None
            return super(BaseEmbedded, self).get_db_prep_value(
                self._validate_value(value),
                connection,
                prepared=prepared
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


class EmbeddedManyAsObjectModel(BaseEmbedded):
    def __init__(self, *args, **kwargs):
        self.embedded_keys = kwargs.pop('keys', None) or {'autoclean': False}
        super(EmbeddedManyAsObjectModel, self).__init__(*args, **kwargs)

    def _validate_value(self, value):
        if not self.embedded_validator or not value:
            return value

        for key in value:
            value[key] = self.embedded_validator.validate_data(value[key])

        if self.embedded_keys.get('autoclean', False) and self.embedded_keys.get('model', None) and self.embedded_keys.get('type', None) == 'model':
            value = self.embedded_validator.clean_id_model_keys_in_data(
                value,
                model_name=self.embedded_keys['model']
            )

        return value
