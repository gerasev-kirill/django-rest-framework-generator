from rest_framework import viewsets, filters
from django.db import models

from . import helpers, decorators
from .permissions.django import Everyone as AllowEveryone
from .serializergen import SerializerGenFactory




def getViewsetParams(model_class, kwargs):
    MODEL_GEN = getattr(model_class, 'MODEL_GEN', {})
    viewsetPref = MODEL_GEN.get('viewset', {})
    filter_backends = (filters.DjangoFilterBackend,)

    if 'queryset' in kwargs.keys():
        queryset = kwargs['queryset']
    else:
        queryset = model_class.objects.all()
    if 'serializer_class' in kwargs.keys():
        serializer_class = kwargs['serializer_class']
    else:
        serializer_class = SerializerGenFactory(model_class)
    if 'filter_backends' in kwargs.keys():
        filter_backends = kwargs['filter_backends']
    elif viewsetPref.has_key('filter_backends'):
        filter_backends = []
        for fb in viewsetPref['filter_backends']:
            filter_backends.append(
                helpers.import_class(fb)
            )
    if 'filter_fields' in kwargs.keys():
        filter_fields = kwargs['filter_fields']
    elif viewsetPref.has_key('filter_fields'):
        filter_fields = viewsetPref['filter_fields']
    else:
        items = MODEL_GEN.get('properties', {}).items()
        items += MODEL_GEN.get('relations',{}).items()
        filter_fields = [
            str(k)   for k,v in items
        ]

    return {
        'queryset': queryset,
        'serializer_class': serializer_class,
        'filter_backends': tuple(filter_backends),
        'filter_fields': tuple(filter_fields),
        'permission_classes': [AllowEveryone]
    }



class ViewsetGenFactory(type):
    def __new__(self, model_class, **kwargs):
        MODEL_GEN = getattr(model_class, 'MODEL_GEN', {})
        viewsetPref = MODEL_GEN.get('viewset', {})

        if 'mixins' in kwargs.keys():
            mixins = kwargs['mixins']
        else:
            mixins = []
            for m in viewsetPref.get('mixins', []):
                mixins.append(
                    helpers.import_class(m)
                )
        if 'add_mixin' in kwargs.keys():
            mixins.append(kwargs['add_mixin'])

        if viewsetPref.get('base', None):
            classes = [
                helpers.import_class(c)
                for c in viewsetPref['base']
            ]
        else:
            classes = [
                helpers.import_class('rest_framework.viewsets.ModelViewSet')
            ]
        classes = mixins + classes

        model_name = MODEL_GEN.get(
            'name',
            model_class.__name__
        )
        name = str(model_name+'_ViewSet')
        params = getViewsetParams(model_class, kwargs)
        if not kwargs.get('acl', None):
            model_acl = MODEL_GEN.get('acl', [])
        else:
            model_acl = kwargs.get('acl')
        new_cls = type(name, tuple(classes), params)
        for prop in dir(new_cls):
            if prop in ['list', 'retrieve', 'update', 'update_partial', 'create', 'destroy']:
                setattr(new_cls, prop,
                    decorators.drf_action_decorator(
                        getattr(new_cls, prop),
                        model_acl
                    )
                )
                continue
            func = getattr(new_cls, prop)
            httpmethods = getattr(func, 'bind_to_methods', None)
            if httpmethods:
                print 'DECORATED '+ prop
                setattr(new_cls, prop,
                    decorators.drf_action_decorator(
                        func,
                        model_acl
                    )
                )
        return new_cls
