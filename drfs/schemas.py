from rest_framework.schemas.openapi import AutoSchema as BaseAutoSchema




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
                return method.schema_api_doc['response_serializer']()
        return super(AutoSchema, self).get_response_serializer(path, method)

    def get_request_serializer(self, path, method):
        if getattr(self.view, 'action', None):
            method = getattr(self.view, self.view.action, None)
            if method and getattr(method, 'schema_api_doc', None) and method.schema_api_doc.get('request_serializer', None):
                return method.schema_api_doc['request_serializer']()
        return super(AutoSchema, self).get_request_serializer(path, method)
