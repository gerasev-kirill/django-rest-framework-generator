from .permissions.acl import PermissionResolver
from rest_framework import exceptions

Resolver = PermissionResolver()






def drf_action_decorator(func, model_acl):
    def wrapper(self, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        resolver_kwargs = {
            'property_func': func.__name__,
            'drf': {
                'kwargs': kwargs,
                'args': args,
            },
            'request': self.request,
            'model_acl': model_acl
        }
        if lookup_url_kwarg in kwargs and kwargs[lookup_url_kwarg]!='-':
            resolver_kwargs['obj'] = self.get_object()

        resolved_permission = Resolver.resolve_permission(**resolver_kwargs)
        if resolved_permission == 'DENY':
            raise exceptions.PermissionDenied(detail="DRFS: you don't have permission")
        return func(self, *args, **kwargs)
    if getattr(func, 'bind_to_methods', None):
        wrapper.bind_to_methods = func.bind_to_methods
        wrapper.detail = func.detail
        wrapper.kwargs = func.kwargs
    return wrapper
