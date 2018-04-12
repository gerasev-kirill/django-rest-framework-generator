from rest_framework import viewsets
from django.db import models
from django.conf import settings

from . import helpers, decorators
from .permissions.drf import Everyone as AllowEveryone

REST_FRAMEWORK = getattr(settings, 'REST_FRAMEWORK', {})




def getViewsetParams(model_class, kwargs):
    DRFS_MODEL_DEFINITION = getattr(model_class, 'DRFS_MODEL_DEFINITION', {})
    viewsetPref = DRFS_MODEL_DEFINITION.get('viewset', {})

    filter_backends = [
        helpers.import_class(m)
        for m in REST_FRAMEWORK.get('DEFAULT_FILTER_BACKENDS', [])
    ]

    if 'queryset' in kwargs:
        queryset = kwargs['queryset']
    else:
        queryset = model_class.objects.all()
    if 'serializer_class' in kwargs:
        serializer_class = kwargs['serializer_class']
    else:
        from . import generate_serializer
        serializer_class = generate_serializer(model_class)
    if 'filter_backends' in kwargs:
        filter_backends = kwargs['filter_backends']
    elif 'filter_backends' in viewsetPref:
        filter_backends = []
        for fb in viewsetPref['filter_backends']:
            filter_backends.append(
                helpers.import_class(fb)
            )
    if 'filter_fields' in kwargs:
        filter_fields = kwargs['filter_fields']
    elif 'filter_fields' in viewsetPref:
        filter_fields = viewsetPref['filter_fields']
    else:
        items = list(DRFS_MODEL_DEFINITION.get('properties', {}).items())
        items += list(DRFS_MODEL_DEFINITION.get('relations',{}).items())
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
        DRFS_MODEL_DEFINITION = getattr(model_class, 'DRFS_MODEL_DEFINITION', {})
        viewsetPref = DRFS_MODEL_DEFINITION.get('viewset', {})

        if 'mixins' in kwargs:
            mixins = kwargs['mixins']
        else:
            mixins = []
            for m in viewsetPref.get('mixins', []):
                mixins.append(
                    helpers.import_class(m)
                )
        if 'add_mixin' in kwargs:
            if isinstance(kwargs['add_mixin'], (str, unicode)):
                mixins.append(
                    helpers.import_class(kwargs['add_mixin'])
                )
            else:
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

        model_name = DRFS_MODEL_DEFINITION.get(
            'name',
            model_class.__name__
        )
        name = str(model_name+'_ViewSet')
        params = getViewsetParams(model_class, kwargs)
        if not kwargs.get('acl', None):
            model_acl = DRFS_MODEL_DEFINITION.get('acl', [])
        else:
            model_acl = kwargs.get('acl')
        new_cls = type(name, tuple(classes), {})

        # params.items - RuntimeError: dictionary changed size during iteration
        for class_prop, generated_value in list(params.items()):
            if getattr(new_cls, class_prop, None):
                del params[class_prop]

        new_cls = type(name, (new_cls,), params)

        for prop in dir(new_cls):
            if prop in ['list', 'retrieve', 'update', 'partial_update', 'create', 'destroy']:
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
                setattr(new_cls, prop,
                    decorators.drf_action_decorator(
                        func,
                        model_acl
                    )
                )
        return new_cls
