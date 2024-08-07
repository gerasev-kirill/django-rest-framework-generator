from collections import OrderedDict
from decimal import Decimal
from django.db import models

from rest_framework import serializers
from rest_framework.schemas.utils import is_list_view
from rest_framework.schemas.openapi import AutoSchema as BaseAutoSchema


from .helpers import fix_field_choices, field_choice_description_to_varname



def get_or_create_serializer_instance(instance_or_class):
    if isinstance(instance_or_class, (serializers.Serializer, serializers.ListSerializer)):
        return instance_or_class
    return instance_or_class()



class AutoSchema(BaseAutoSchema):

    def get_tags(self, *args, **kwargs):
        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        if model:
            return [model.__name__]
        return super(AutoSchema, self).get_tags(*args, **kwargs)

    def get_operation_id_base(self, *args, **kwargs):
        return ''

    def allows_filters(self, path, method):
        if getattr(self.view, 'filter_backends', None) is None:
            return False
        if not getattr(self.view, 'action', None):
            return method.lower() in ["get", "put", "patch", "delete"]
        method = getattr(self.view, self.view.action, None)
        if method and getattr(method, 'ignore_filter_backend', None):
            return False
        if method and getattr(method, 'schema_api_doc', None) and method.schema_api_doc.get('ignore_filter_backend', None):
            return False
        return True


    def get_response_serializer(self, path, method):
        if getattr(self.view, 'action', None):
            method = getattr(self.view, self.view.action, None)
            if method and getattr(method, 'schema_api_doc', None) and method.schema_api_doc.get('response_serializer', None):
                return get_or_create_serializer_instance(method.schema_api_doc['response_serializer'])
        return super(AutoSchema, self).get_response_serializer(path, method)


    def get_request_serializer(self, path, method):
        if getattr(self.view, 'action', None):
            method = getattr(self.view, self.view.action, None)
            if method and getattr(method, 'schema_api_doc', None) and method.schema_api_doc.get('request_serializer', None):
                return get_or_create_serializer_instance(method.schema_api_doc['request_serializer'])
        return super(AutoSchema, self).get_request_serializer(path, method)



    def get_components(self, path, method):
        """
        Return components with their properties from the serializer.
        """

        if method.lower() == 'delete':
            return {}

        request_serializer = self.get_request_serializer(path, method)
        response_serializer = self.get_response_serializer(path, method)

        if isinstance(request_serializer, serializers.ListSerializer):
            request_serializer = request_serializer.child
        if isinstance(response_serializer, serializers.ListSerializer):
            response_serializer = response_serializer.child

        components = {}

        if isinstance(request_serializer, serializers.Serializer):
            component_name = self.get_component_name(request_serializer)
            content = self.map_serializer(request_serializer)
            components.setdefault(component_name, content)

        if isinstance(response_serializer, serializers.Serializer):
            component_name = self.get_component_name(response_serializer)
            content = self.map_serializer(response_serializer)
            components.setdefault(component_name, content)

        return components



    def get_responses(self, path, method):
        if method == 'DELETE':
            return {
                '204': {
                    'description': ''
                }
            }

        self.response_media_types = self.map_renderers(path, method)

        serializer = self.get_response_serializer(path, method)

        if isinstance(serializer, serializers.ListSerializer):
            item_schema = self.get_reference(serializer.child)
        elif not isinstance(serializer, serializers.Serializer):
            item_schema = {}
        else:
            item_schema = self.get_reference(serializer)

        if is_list_view(path, method, self.view):
            response_schema = {
                'type': 'array',
                'items': item_schema,
            }
            paginator = self.get_paginator()
            if paginator:
                response_schema = paginator.get_paginated_response_schema(response_schema)
        elif isinstance(serializer, serializers.ListSerializer):
            response_schema = {
                'type': 'array',
                'items': item_schema,
            }
        else:
            response_schema = item_schema

        status_code = '201' if method == 'POST' else '200'
        return {
            status_code: {
                'content': {
                    ct: {'schema': response_schema}
                    for ct in self.response_media_types
                },
                # description is a mandatory property,
                # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#responseObject
                # TODO: put something meaningful into it
                'description': ""
            }
        }


    def map_field(self, field):
        if hasattr(field, 'to_openapi_schema'):
            return field.to_openapi_schema()
        
        # Related fields.
        if isinstance(field, serializers.ManyRelatedField):
            child = field.child_relation
            # хак для сериализаторов, у которых не указан queryset
            if not child.queryset and hasattr(field.parent, 'Meta') and hasattr(field.parent.Meta, 'model'):
                model = field.parent.Meta.model
                model_field = model._meta.get_field(field.field_name)
                if model_field and hasattr(model_field, 'related_model'):
                    child._hack_for_schemas = model_field.related_model
            return {
                'type': 'array',
                'items': self.map_field(child)
            }

        if isinstance(field, serializers.PrimaryKeyRelatedField):
            model = getattr(field.queryset, 'model', None) or getattr(field, '_hack_for_schemas', None)
            if model is not None:
                model_field = model._meta.pk
                if isinstance(model_field, (models.AutoField, models.BigAutoField)):
                    return {'type': 'integer'}

        result = super().map_field(field)
        return result



    def map_choicefield(self, field):
        # preserve order and remove duplicates
        choices = [
            [k,v]
            for k,v in field.choices.items()
        ]
        if all(isinstance(choice[0], bool) for choice in choices):
            type = 'boolean'
        elif all(isinstance(choice[0], int) for choice in choices):
            type = 'integer'
        elif all(isinstance(choice[0], (int, float, Decimal)) for choice in choices):  # `number` includes `integer`
            # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.21
            type = 'number'
        elif all(isinstance(choice, str) for choice in choices):
            type = 'string'
        else:
            type = None

        mapping = {
            # The value of `enum` keyword MUST be an array and SHOULD be unique.
            # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.20
            'enum': [
                c[0]
                for c in choices
            ],
            # openapi <= 3.1
            'x-enum-varnames': [
                field_choice_description_to_varname(c[1])
                for c in choices
            ]
        }
        # openapi > 3.1
        mapping['oneOf'] = [
            {
                'title': choices[i][1], 
                'const': mapping['x-enum-varnames'][i], 
                'description': choices[i][1]
            }
            for i in range(len(choices))
        ]

        # If We figured out `type` then and only then we should set it. It must be a string.
        # Ref: https://swagger.io/docs/specification/data-models/data-types/#mixed-type
        # It is optional but it can not be null.
        # Ref: https://tools.ietf.org/html/draft-wright-json-schema-validation-00#section-5.21
        if type:
            mapping['type'] = type
        return mapping