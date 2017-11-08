
from django.db.models import fields as django_fields
from django.db import models as django_models
from django.conf import settings as django_settings
from django.dispatch import receiver
from jsonfield import JSONField

from ._BaseModelGenerator import BaseModelGenerator
from ... import helpers
from ...db import fields as drfs_fields


REGISTERED_RECEIVERS = {}
@receiver(django_models.signals.pre_delete)
def on_delete(sender, instance, **kwargs):
    _meta = getattr(sender, '_meta', {})
    model_name = getattr(_meta, 'object_name', None)
    if model_name not in REGISTERED_RECEIVERS:
        return
    field_names = REGISTERED_RECEIVERS[model_name].get('delete_hasMany', [])
    for name in field_names:
        field_set = getattr(instance, name)
        field_set.all().delete()





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
    model_fields_mapping = {
        'string': django_fields.CharField,
        'int': django_fields.IntegerField,
        'float': django_fields.FloatField,
        'number': django_fields.FloatField,
        'object': JSONField,
        'date': django_fields.DateField,
        'datetime': django_fields.DateTimeField,
        'time': django_fields.TimeField,
        'bool': django_fields.BooleanField,
        'array': drfs_fields.ListField,

        'GeoPoint': drfs_fields.GeoPoint,

        'belongsTo': django_models.ForeignKey,
        'hasOne': django_models.OneToOneField,
        'hasMany': django_models.ManyToManyField,
        'embedsMany': drfs_fields.ListField
    }

    def get_model_class(self, model_path):
        if model_path in ['django.contrib.auth.models.User', 'AUTH_USER_MODEL']:
            if getattr(django_settings, 'AUTH_USER_MODEL', False):
                return django_settings.AUTH_USER_MODEL
        return super(DjangoOrmModelGenerator, self).get_model_class(model_path)


    def build_field(self, name, params):
        field_class, field_args, field_kwargs = super(DjangoOrmModelGenerator, self).build_field(name, params)

        if 'default' in params:
            field_kwargs['default'] = params['default']
        if 'choices' in params:
            field_kwargs['choices'] = fix_choices(params['choices'])
        if 'description' in params:
            field_kwargs['help_text'] = params['description']
        if 'required' in params and params['required'] == False:
            field_kwargs['blank'] = True
            field_kwargs['null'] = True

        return field_class, field_args, field_kwargs




    def build_field__string(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)

        if not params.get('required', False):
            field_kwargs['blank'] = True
        for k,v in params.items():
            if k=='max':
                field_kwargs['max_length'] = int(v)
        return field_class, field_args, field_kwargs


    def build_field__datetime(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)

        for k,v in params.items():
            if k=='auto_now_add':
                field_kwargs['auto_now_add'] = v
        return field_class, field_args, field_kwargs


    def build_field__int(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)

        if not params.get('required', True):
            field_kwargs['blank'] = True
            field_kwargs['null'] = True
        return field_class, field_args, field_kwargs


    def build_field__belongsTo(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        if 'blank' not in field_kwargs:
            field_kwargs['blank'] = True
        if 'null' not in field_kwargs:
            field_kwargs['null'] = True
        if params.get('relationName', None):
            field_kwargs['related_name'] = params['relationName']

        to_model = self.get_model_class(params['model'])
        field_args = (to_model,)

        for k,v in params.items():
            if k=='on_delete':
                field_kwargs['on_delete'] = getattr(django_models, v)
        return field_class, field_args, field_kwargs


    def build_field__hasOne(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        if 'blank' not in field_kwargs:
            field_kwargs['blank'] = True
        if 'null' not in field_kwargs:
            field_kwargs['null'] = True
        if params.get('relationName', None):
            field_kwargs['related_name'] = params['relationName']

        to_model = self.get_model_class(params['model'])
        field_args = (to_model,)

        for k,v in params.items():
            if k=='on_delete':
                field_kwargs['on_delete'] = getattr(django_models, v)
        return field_class, field_args, field_kwargs


    def build_field__hasMany(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        if 'blank' not in field_kwargs:
            field_kwargs['blank'] = True
        if 'null' in field_kwargs:
            del field_kwargs['null']
        if params.get('relationName', None):
            field_kwargs['related_name'] = params['relationName']

        to_model = self.get_model_class(params['model'])
        field_args = (to_model,)

        if params.get('on_delete', None) == 'CASCADE':
            REGISTERED_RECEIVERS[self.model_name] = REGISTERED_RECEIVERS.get(self.model_name, {})
            REGISTERED_RECEIVERS[self.model_name]['delete_hasMany'] = \
                REGISTERED_RECEIVERS[self.model_name].get('delete_hasMany', [])

            REGISTERED_RECEIVERS[self.model_name]['delete_hasMany'].append(name)

        return field_class, field_args, field_kwargs


    def build_field__embedsMany(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        if 'default' not in field_kwargs:
            field_kwargs['default'] = []

        to_model = self.get_model_class(params['model'])
        REGISTERED_RECEIVERS[self.model_name] = REGISTERED_RECEIVERS.get(self.model_name, {})
        REGISTERED_RECEIVERS[self.model_name]['delete_hasMany'] = \
            REGISTERED_RECEIVERS[self.model_name].get('delete_hasMany', {})

        REGISTERED_RECEIVERS[self.model_name]['delete_hasMany'][name] = to_model
        return field_class, field_args, field_kwargs
