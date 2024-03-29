from django.db.models import fields as django_fields
from django.db import models as django_models
from django.conf import settings as django_settings
from django.dispatch import receiver

from ._BaseModelGenerator import BaseModelGenerator
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
        'object': drfs_fields.JSONField,
        'date': django_fields.DateField,
        'datetime': django_fields.DateTimeField,
        'time': django_fields.TimeField,
        'bool': django_fields.BooleanField,
        'array': drfs_fields.ListField,

        'GeoPoint': drfs_fields.GeoPoint,

        'belongsTo': django_models.ForeignKey,
        'hasOne': django_models.OneToOneField,
        'hasMany': django_models.ManyToManyField,
        'embedsOne': drfs_fields.EmbeddedOneModel,
        'embedsMany': drfs_fields.EmbeddedManyModel,
        'embedsManyAsObject': drfs_fields.EmbeddedManyAsObjectModel,
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
        if 'verbose_name' in params:
            field_kwargs['verbose_name'] = params['verbose_name']
        if 'required' in params and params['required'] == False:
            field_kwargs['blank'] = True
            field_kwargs['null'] = True
        if params.get('primary', False):
            field_kwargs['primary_key'] = True
        if params.get('unique', False):
            field_kwargs['unique'] = True

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
            if k in ['on_delete', 'onDelete']:
                field_kwargs['on_delete'] = getattr(django_models, v)
        if 'on_delete' not in field_kwargs:
            # Note: on_delete will become a required argument in Django 2.0. In older versions it defaults to CASCADE.
            field_kwargs['on_delete'] = django_models.CASCADE
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
            if k in ['on_delete', 'onDelete']:
                field_kwargs['on_delete'] = getattr(django_models, v)
        if 'on_delete' not in field_kwargs:
            # Note: on_delete will become a required argument in Django 2.0. In older versions it defaults to CASCADE.
            field_kwargs['on_delete'] = django_models.CASCADE
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

        if params.get('on_delete', None) == 'CASCADE' or params.get('onDelete', None) == 'CASCADE':
            REGISTERED_RECEIVERS[self.model_name] = REGISTERED_RECEIVERS.get(self.model_name, {})
            REGISTERED_RECEIVERS[self.model_name]['delete_hasMany'] = \
                REGISTERED_RECEIVERS[self.model_name].get('delete_hasMany', [])

            REGISTERED_RECEIVERS[self.model_name]['delete_hasMany'].append(name)

        return field_class, field_args, field_kwargs


    def build_field__embedsMany(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        field_kwargs['embedded_model_name'] = params['model']
        if 'default' not in field_kwargs:
            field_kwargs['default'] = []
        return field_class, field_args, field_kwargs


    def build_field__embedsManyAsObject(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        field_kwargs['embedded_model_name'] = params['model']
        if 'default' not in field_kwargs:
            field_kwargs['default'] = []
        if params.get('keys', None) and params['keys'].get('autoclean', False):
            field_kwargs['keys'] = params['keys']
        return field_class, field_args, field_kwargs


    def build_field__embedsOne(self, name, params):
        field_class, field_args, field_kwargs = self.build_field(name, params)
        field_kwargs['embedded_model_name'] = params['model']
        if 'default' not in field_kwargs:
            field_kwargs['default'] = {}
        return field_class, field_args, field_kwargs
