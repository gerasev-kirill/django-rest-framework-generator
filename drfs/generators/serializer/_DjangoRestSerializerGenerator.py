from rest_framework import serializers as rest_serializers
from rest_framework import relations as rest_relations
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings as django_settings
from django.db.models.fields.reverse_related import ManyToManyRel

from ._BaseSerializerGenerator import BaseSerializerGenerator

from ...serializers import fields as drfs_field_serializers
from ...db import fields as drfs_fields
from ... import helpers

try:
    from timezone_field import TimeZoneField
except ImportError:
    TimeZoneField = None


class SoftPrimaryKeyRelatedField(rest_relations.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            return self.get_queryset().get(pk=data)
        except ObjectDoesNotExist:
            return None
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)




class DjangoRestSerializerGenerator(BaseSerializerGenerator):
    serializer_field_mapping = {
        drfs_fields.ListField: drfs_field_serializers.ListField,
        drfs_fields.JSONField: drfs_field_serializers.JSONField,
        drfs_fields.EmbeddedOneModel: drfs_field_serializers.EmbeddedOneModel
    }
    if TimeZoneField:
        serializer_field_mapping[TimeZoneField] = drfs_fields.TimeZoneSerializer
    default_serializer_class = rest_serializers.ModelSerializer
    model_relation_types = ['belongsTo', 'hasOne', 'hasMany', 'embedsOne', 'embedsMany', 'embedsManyAsObject']


    def get_model_class(self, model_path):
        if model_path=='django.contrib.auth.models.User' or model_path=='AUTH_USER_MODEL':
            return helpers.import_class(django_settings.AUTH_USER_MODEL)
        return super(DjangoRestSerializerGenerator, self).get_model_class(model_path)


    def build_relational_serializer__embedsMany(self, django_field, params):
        serializer_kwargs = {
            'help_text': getattr(django_field, 'help_text', ''),
            'embedded_model_name': params['model'],
            'embedded_params': params
        }
        if 'default' in params:
            serializer_kwargs['default'] = params['default']
        if not params.get('required', True):
            serializer_kwargs['required'] = False
            serializer_kwargs['allow_null'] = True
        return drfs_field_serializers.EmbeddedManyModel, [], serializer_kwargs


    def build_relational_serializer__embedsManyAsObject(self, django_field, params):
        serializer_kwargs = {
            'help_text': getattr(django_field, 'help_text', ''),
            'embedded_model_name': params['model'],
            'embedded_params': params
        }
        if 'default' in params:
            serializer_kwargs['default'] = params['default']
        if not params.get('required', True):
            serializer_kwargs['required'] = False
            serializer_kwargs['allow_null'] = True
        return drfs_field_serializers.EmbeddedManyAsObjectModel, [], serializer_kwargs


    def build_relational_serializer__embedsOne(self, django_field, params):
        serializer_kwargs = {
            'help_text': getattr(django_field, 'help_text', ''),
            'embedded_model_name': params['model'],
            'embedded_params': params
        }
        if 'default' in params:
            serializer_kwargs['default'] = params['default']
        if not params.get('required', True):
            serializer_kwargs['required'] = False
            serializer_kwargs['allow_null'] = True
        return drfs_field_serializers.EmbeddedOneModel, [], serializer_kwargs


    def build_relational_serializer(self, django_field, params):
        _params = params.get('serializer', None)
        if not _params or params.get('type', None) not in self.model_relation_types:
            return None, [], {}

        serializer_class = None
        serializer_args = []
        serializer_kwargs = {
            'help_text': getattr(django_field, 'help_text', '')
        }
        if not params.get('required', True):
            serializer_kwargs['required'] = False
            serializer_kwargs['allow_null'] = True

        generator_kwargs = {
            'visible_fields': _params.get('visible_fields', []),
            'hidden_fields': _params.get('hidden_fields', [])
        }
        if generator_kwargs['visible_fields'] or generator_kwargs['hidden_fields']:
            model_class = getattr(django_field, 'related_model', None)
            if not model_class:
                if not params.get('model', None):
                    raise ValueError("Expected 'model' property for relation field '"+\
                        django_field.name+"' in model definition '"+self.model_name+"'")
                model_class = self.get_model_class(params['model'])

            remote_field = getattr(django_field, 'remote_field', None)
            generator = self.__class__(model_class, **generator_kwargs)
            serializer_class = generator.to_serializer()
            serializer_kwargs['many'] = isinstance(remote_field, ManyToManyRel)

        return serializer_class, serializer_args, serializer_kwargs

    def build_serializer(self, django_field, params=None):
        serializer_class, serializer_args, serializer_kwargs = super(DjangoRestSerializerGenerator, self).build_serializer(django_field, params)
        params = params or {}
        if params.get('type', None) == 'object' and (not params.get('required', True) or params.get('read_only', False)):
            serializer_class = drfs_field_serializers.JSONField
            serializer_kwargs['required'] = params.get('required', True)
            serializer_kwargs['read_only'] = params.get('read_only', False)
            if serializer_kwargs['read_only']:
                serializer_kwargs['required'] = False
            if not serializer_kwargs['required']:
                serializer_kwargs['allow_null'] = True
        if params.get('type', None) == 'array' and (not params.get('required', True) or params.get('read_only', False)):
            serializer_class = drfs_field_serializers.ListField
            serializer_kwargs['required'] = params.get('required', True)
            serializer_kwargs['read_only'] = params.get('read_only', False)
            if serializer_kwargs['read_only']:
                serializer_kwargs['required'] = False
            if not serializer_kwargs['required']:
                serializer_kwargs['allow_null'] = True
        if params.get('type', None) == 'GeoPoint':
            serializer_class = drfs_field_serializers.GeoPoint
            serializer_kwargs['required'] = params.get('required', True)
            serializer_kwargs['read_only'] = params.get('read_only', False)
            if serializer_kwargs['read_only']:
                serializer_kwargs['required'] = False
            if not serializer_kwargs['required']:
                serializer_kwargs['allow_null'] = True
        return serializer_class, serializer_args, serializer_kwargs

    def to_serializer(self):
        _cls = super(DjangoRestSerializerGenerator, self).to_serializer()
        relations = self.model_definition.get('relations', {})

        def build_relational_field(_self, field_name, relation_info):
            field_params = relations.get(field_name, {})
            field_class, field_kwargs = super(_cls, _self).build_relational_field(
                field_name,
                relation_info
            )
            if field_params.get('serializer', {}).get('ignore_object_doesnt_exist', False) and \
                field_class == rest_relations.PrimaryKeyRelatedField:
                return SoftPrimaryKeyRelatedField, field_kwargs
            return field_class, field_kwargs

        setattr(_cls, 'build_relational_field', build_relational_field)
        return _cls
