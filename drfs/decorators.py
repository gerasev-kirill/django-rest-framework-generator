from functools import wraps
from rest_framework import exceptions
from django.conf import settings
from .permissions.acl_resolver import PermissionResolver
from . import helpers


Resolver = PermissionResolver()
class MethodMapper(dict):
    """
    Enables mapping HTTP methods to different ViewSet methods for a single,
    logical action.
    Example usage:
        class MyViewSet(ViewSet):
            @action(detail=False)
            def example(self, request, **kwargs):
                ...
            @example.mapping.post
            def create_example(self, request, **kwargs):
                ...
    """

    def __init__(self, action, methods):
        self.action = action
        for method in methods:
            self[method] = self.action.__name__

    def _map(self, method, func):
        assert method not in self, (
            "Method '%s' has already been mapped to '.%s'." % (method, self[method]))
        assert func.__name__ != self.action.__name__, (
            "Method mapping does not behave like the property decorator. You "
            "cannot use the same method name for each mapping declaration.")

        self[method] = func.__name__
        return func

    def get(self, func):
        return self._map('get', func)

    def post(self, func):
        return self._map('post', func)

    def put(self, func):
        return self._map('put', func)

    def patch(self, func):
        return self._map('patch', func)

    def delete(self, func):
        return self._map('delete', func)

    def head(self, func):
        return self._map('head', func)

    def options(self, func):
        return self._map('options', func)

    def trace(self, func):
        return self._map('trace', func)


def drf_ignore_filter_backend(model_name=None):
    def wrapper(func):
        if model_name:
            setattr(func, 'ignore_filter_backend', model_name)
        else:
            setattr(func, 'ignore_filter_backend', True)
        return func
    return wrapper



def drf_action_decorator(func, model_acl):

    @wraps(func)
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
        if lookup_url_kwarg in kwargs and kwargs[lookup_url_kwarg] != '-':
            resolver_kwargs['obj'] = self.get_object()

        resolved_permission = Resolver.resolve_permission(**resolver_kwargs)
        if resolved_permission == 'DENY':
            detail = "DRFS: Permission Denied by acl"
            if settings.DEBUG:
                if not self.request.user.is_authenticated:
                    detail += " (user not authenticated)"
                else:
                    detail += " (for user %s)" % self.request.user.username
            raise exceptions.PermissionDenied(detail=detail)
        return func(self, *args, **kwargs)


    if getattr(func, 'bind_to_methods', None) and not hasattr(func, 'mapping'):
        # DEPRECATED drf <= 3.8
        #wrapper.bind_to_methods = func.bind_to_methods
        methods = [
            method.lower()
            for method in func.bind_to_methods or ['get']
        ]
        wrapper.url_path = func.kwargs.pop('url_path', None) or func.__name__
        wrapper.url_name = func.kwargs.pop('url_name', None) or func.__name__.replace('_', '-')
        wrapper.mapping = MethodMapper(func, methods)
        wrapper.kwargs = func.kwargs
        wrapper.detail = func.detail

    for prop in dir(func):
        if prop.startswith('ignore_'):
            setattr(wrapper, prop, getattr(func, prop))
    return wrapper



if helpers.rest_framework_version >= (3,8,0):
    from rest_framework.decorators import action
else:
    # DEPRECATED
    from rest_framework.decorators import list_route, detail_route



    def action(methods=None, detail=None, **kwargs):
        methods = ['get'] if (methods is None) else methods
        methods = [method.lower() for method in methods]

        assert detail is not None, (
            "@action() missing required argument: 'detail'"
        )
        def decorator(func):
            if detail:
                decorated = detail_route(methods, **kwargs)(func)
            else:
                decorated = list_route(methods, **kwargs)(func)
            decorated.url_path = kwargs.pop('url_path', None) or func.__name__
            decorated.url_name = kwargs.pop('url_name', None) or func.__name__.replace('_', '-')
            decorated.mapping = MethodMapper(func, methods)
            decorated.kwargs = kwargs
            return decorated
        return decorator
