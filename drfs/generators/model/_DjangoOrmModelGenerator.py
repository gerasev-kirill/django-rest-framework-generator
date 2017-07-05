
from django.db.models import fields as django_fields
from django.db import models as django_models
from django.conf import settings as django_settings
from django.dispatch import receiver
from jsonfield import JSONField

from _BaseModelGenerator import BaseModelGenerator
from ... import helpers
from ...db import fields as drfs_fields


REGISTERED_RECEIVERS = {}
@receiver(django_models.signals.pre_delete)
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





def fix_choices(choices):
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



class DjangoOrmModelGenerator(BaseModelGenerator):
    default_fields_map = {
        'string': django_fields.CharField,
        'int': django_fields.IntegerField,
        'object': JSONField,
        'date': django_fields.DateField,
        'datetime': django_fields.DateTimeField,
        'bool': django_fields.BooleanField,
        'array': drfs_fields.ListField,

        'belongsTo': django_models.ForeignKey,
        'hasOne': django_models.OneToOneField,
        'hasMany': django_models.ManyToManyField,
        'embedsMany': drfs_fields.ListField
    }


    def field_definition_to_django(self, field_name, field_params):
        field = super(DjangoOrmModelGenerator, self).field_definition_to_django(field_name, field_params)

        if field_params.has_key('default'):
            field.kwargs['default'] = field_params['default']
        if field_params.has_key('choices'):
            field.kwargs['choices'] = fix_choices(field_params['choices'])
        if field_params.has_key('description'):
            field.kwargs['help_text'] = field_params['description']
        if field_params.has_key('required') and field_params['required'] == False:
            field.kwargs['blank'] = True
            field.kwargs['null'] = True

        return field

    def _get_model_class(self, model_path):
        if model_path=='django.contrib.auth.models.User' or model_path=='AUTH_USER_MODEL':
            if getattr(django_settings, 'AUTH_USER_MODEL', False):
                return django_settings.AUTH_USER_MODEL
        if '.' not in model_path:
            return model_path
        return helpers.import_class(model_path)





    def string_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)

        if not field_params.get('required', False):
            field.kwargs['blank'] = True
        for k,v in field_params.items():
            if k=='max':
                field.kwargs['max_length'] = int(v)
        return field


    def datetime_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)

        for k,v in field_params.items():
            if k=='auto_now_add':
                field.kwargs['auto_now_add'] = v
        return field


    def int_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)

        if not field_params.get('required', True):
            field.kwargs['blank'] = True
            field.kwargs['null'] = True
        return field


    def belongsTo_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)
        if not field.kwargs.has_key('blank'):
            field.kwargs['blank'] = True
        if not field.kwargs.has_key('null'):
            field.kwargs['null'] = True

        to_model = self._get_model_class(field_params['model'])
        field.args = (to_model,)

        for k,v in field_params.items():
            if k=='on_delete':
                field.kwargs['on_delete'] = getattr(django_models, v)
        return field


    def hasOne_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)
        if not field.kwargs.has_key('blank'):
            field.kwargs['blank'] = True
        if not field.kwargs.has_key('null'):
            field.kwargs['null'] = True

        to_model = self._get_model_class(field_params['model'])
        field.args = (to_model,)

        for k,v in field_params.items():
            if k=='on_delete':
                field.kwargs['on_delete'] = getattr(django_models, v)
        return field


    def hasMany_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)
        if not field.kwargs.has_key('blank'):
            field.kwargs['blank'] = True
        if field.kwargs.has_key('null'):
            del field.kwargs['null']

        to_model = self._get_model_class(field_params['model'])
        field.args = (to_model,)

        return field


    def embedsMany_field_definition_to_django(self, field_name, field_params):
        field = self.field_definition_to_django(field_name, field_params)
        if not field.kwargs.has_key('default'):
            field.kwargs['default'] = []

        to_model = self._get_model_class(field_params['model'])
        REGISTERED_RECEIVERS[self.model_name] = REGISTERED_RECEIVERS.get(self.model_name, {})
        REGISTERED_RECEIVERS[self.model_name]['delete_embedsMany'] = \
            REGISTERED_RECEIVERS[self.model_name].get('delete_embedsMany', {})

        REGISTERED_RECEIVERS[self.model_name]['delete_embedsMany'][field_name] = to_model
        return field
