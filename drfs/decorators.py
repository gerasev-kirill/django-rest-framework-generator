from .permissions.acl_resolver import PermissionResolver
from rest_framework import exceptions

Resolver = PermissionResolver()


DEFAULT_DOC_STRINGS = {
    "list": """
    Find all instances of the model matched by filter from the data source
    ---
    parameters:
        - name: filter
          description: Filter defining fields, where, order, skip, and limit. <a target="_blank" href="https://loopback.io/doc/en/lb2/Querying-data.html#using-stringified-json-in-rest-queries">Docs here</a>
          required: false
          type: objects
          paramType: query
    """,
    "create": """
    Create a new instance of the model and persist it into the data source
    ---
    """,
    "retrieve": """
    Find a model instance by id from the data source
    ---
    parameters:
        - name: pk
          description: Model id
          required: true
          type: string
          paramType: query
        - name: filter
          description: Filter defining fields. <a target="_blank" href="https://loopback.io/doc/en/lb2/Querying-data.html#using-stringified-json-in-rest-queries">Docs here</a>
          required: false
          type: objects
          paramType: query
    """,
    "update": """
    Update attributes for a model instance and persist it into the data source
    ---
    parameters:
        - name: pk
          description: Model id
          required: true
          type: string
          paramType: query
    """,
    "partial_update": """
    Partial update attributes for a model instance and persist it into the data source
    ---
    parameters:
        - name: pk
          description: Model id
          required: true
          type: string
          paramType: query
    """,
    "destroy": """
    Delete a model instance by id from the data source
    . Returns 204 on success, 404 if object doesn't exists
    ---
    type:
    omit_serializer: true
    responseMessages:
        - code: 204
          message: Request was successful
    parameters:
        - name: pk
          description: Model id
          required: true
          type: string
          paramType: query
    """
}


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
        if lookup_url_kwarg in kwargs and kwargs[lookup_url_kwarg] != '-':
            resolver_kwargs['obj'] = self.get_object()

        resolved_permission = Resolver.resolve_permission(**resolver_kwargs)
        if resolved_permission == 'DENY':
            raise exceptions.PermissionDenied(detail="DRFS: Permission Denied")
        return func(self, *args, **kwargs)


    if getattr(func, 'bind_to_methods', None):
        wrapper.bind_to_methods = func.bind_to_methods
        wrapper.detail = func.detail
        wrapper.kwargs = func.kwargs
    # swagger documentation
    if func.__doc__:
        wrapper.__doc__ = func.__doc__
    else:
        wrapper.__doc__ = DEFAULT_DOC_STRINGS.get(func.__name__, "")
    return wrapper
