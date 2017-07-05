from rest_framework import serializers as rest_serializers
from rest_framework import relations as rest_relations
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings as django_settings
from django.db.models.fields.reverse_related import ManyToManyRel

from ._BaseSerializerGenerator import BaseSerializerGenerator
from ..field_definition import DjangoFieldDefinition

from ...serializers import fields as drfs_field_serializers
from ...db import fields as drfs_fields
from ... import helpers



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
        drfs_fields.JSONField: drfs_field_serializers.JSONField
    }
    default_serializer_class = rest_serializers.ModelSerializer
    model_relation_types = ['belongsTo', 'hasOne', 'hasMany', 'embedsMany']

    def get_model_class(self, model_path):
        if model_path=='django.contrib.auth.models.User' or model_path=='AUTH_USER_MODEL':
            return helpers.import_class(django_settings.AUTH_USER_MODEL)
        return super(DjangoRestSerializerGenerator, self).get_model_class(model_path)


    def django_relation_field_to_rest_serializer(self, django_field, field_params):
        serializer_params = field_params.get('_serializer', None)
        serializer = DjangoFieldDefinition(
            help_text=getattr(django_field, 'help_text', '')
        )
        if not serializer_params or field_params.get('type', None) not in self.model_relation_types:
            return serializer
        kwargs = {
            'visible_fields': serializer_params.get('visible_fields', []),
            'hidden_fields': serializer_params.get('hidden_fields', [])
        }
        if kwargs['visible_fields'] or kwargs['hidden_fields']:
            model_class = getattr(django_field, 'related_model', None)
            if not model_class:
                if not field_params.get('model', None):
                    raise ValueError("Expected 'model' property for relation field '"+\
                        django_field.name+"' in model definition '"+self.model_name+"'")
                model_class = self.get_model_class(field_params['model'])

            remote_field = getattr(django_field, 'remote_field', None)
            generator = self.__class__(model_class, **kwargs)
            serializer.field_class = generator.to_serializer()
            serializer.kwargs['many'] = isinstance(remote_field, ManyToManyRel)

        return serializer

    def to_serializer(self):
        serializer_class = super(DjangoRestSerializerGenerator, self).to_serializer()
        relations = self.model_definition.get('relations', {})

        def build_relational_field(sself, field_name, relation_info):
            field_params = relations.get(field_name, {})
            field_class, field_kwargs = super(serializer_class, sself).build_relational_field(
                field_name,
                relation_info
            )
            if field_params.get('_serializer', {}).get('ignore_object_doesnt_exist', False) and \
                field_class == rest_relations.PrimaryKeyRelatedField:
                return SoftPrimaryKeyRelatedField, field_kwargs
            return field_class, field_kwargs

        setattr(serializer_class, 'build_relational_field', build_relational_field)
        return serializer_class
