from django.conf import settings
from rest_framework.settings import api_settings as drf_api_settings
from rest_framework.viewsets import ModelViewSet

from . import helpers, decorators
from .permissions.drf import Everyone as AllowEveryone

REST_FRAMEWORK = getattr(settings, 'REST_FRAMEWORK', {})
REST_FRAMEWORK_HAS_DEFAULT_SCHEMA_CLASS = hasattr(drf_api_settings, 'DEFAULT_SCHEMA_CLASS')




def get_viewset_params(model_class, kwargs):
    DRFS_MODEL_DEFINITION = getattr(model_class, 'DRFS_MODEL_DEFINITION', {})
    viewset_pref = DRFS_MODEL_DEFINITION.get('viewset', {})

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
    elif 'filter_backends' in viewset_pref:
        filter_backends = []
        for fb in viewset_pref['filter_backends']:
            filter_backends.append(
                helpers.import_class(fb)
            )
    if 'filter_fields' in kwargs:
        filter_fields = kwargs['filter_fields']
    elif 'filter_fields' in viewset_pref:
        filter_fields = viewset_pref['filter_fields']
    else:
        items = list(DRFS_MODEL_DEFINITION.get('properties', {}).items())
        items += list(DRFS_MODEL_DEFINITION.get('relations',{}).items())
        filter_fields = [
            str(k)   for k,v in items
        ]

    params = {
        'queryset': queryset,
        'serializer_class': serializer_class,
        'filter_backends': tuple(filter_backends),
        'filter_fields': tuple(filter_fields),
        'permission_classes': [AllowEveryone]
    }
    return params



class ViewsetGenFactory(type):
    def __new__(self, model_class, **kwargs):
        DRFS_MODEL_DEFINITION = getattr(model_class, 'DRFS_MODEL_DEFINITION', {})
        viewset_pref = DRFS_MODEL_DEFINITION.get('viewset', {})
        if kwargs.get('add_mixin', None):
            raise ValueError("Do not pass 'add_mixin' to viewset generator via kwargs! Use 'mixins' instead.")

        mixins = []
        for mixin in kwargs.get('mixins', None) or viewset_pref.get('mixins', None) or []:
            if callable(mixin):
                mixins.append(mixin)
            else:
                mixins.append(helpers.import_class(mixin))

        if viewset_pref.get('base', None):
            classes = [
                helpers.import_class(c)
                for c in viewset_pref['base']
            ]
        else:
            classes = [
                ModelViewSet
            ]
        classes = mixins + classes
        has_schema = False
        for cl in classes:
            if hasattr(cl, 'schema') and not issubclass(cl, ModelViewSet):
                has_schema = True

        model_name = DRFS_MODEL_DEFINITION.get(
            'name',
            model_class.__name__
        )
        name = str(model_name+'_ViewSet')
        params = get_viewset_params(model_class, kwargs)

        if 'acl' in DRFS_MODEL_DEFINITION:
            raise ValueError("Property 'acl' should not be set on root of model definition for '%s' model. Place it inside 'viewset' property" % model_name)
        if kwargs.get('acl', None):
            model_acl = kwargs.get('acl')
        else:
            model_acl = DRFS_MODEL_DEFINITION.get('viewset', {}).get('acl', [])

        new_cls = type(name, tuple(classes), {})

        for class_prop in list(params.keys()):
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
            if hasattr(func, 'mapping') or hasattr(func, 'bind_to_methods'):
                setattr(new_cls, prop,
                    decorators.drf_action_decorator(
                        func,
                        model_acl
                    )
                )
        return new_cls
