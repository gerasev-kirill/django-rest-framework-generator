from rest_framework.decorators import list_route
from rest_framework.response import Response






class QuerysetExistsModelMixin(object):

    @list_route(methods=['get'])
    def queryset_exists(self, request, *args, **kwargs):
        """
        Check whether a model queryset exists in the data source
        ---
        omit_serializer: true
        type:
          exists:
            required: true
            type: boolean
        parameters:
            - name: filter
              description: Filter defining fields, where, order, skip, and limit. <a target="_blank" href="https://loopback.io/doc/en/lb2/Querying-data.html#using-stringified-json-in-rest-queries">Docs here</a>
              required: false
              type: objects
              paramType: query
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'exists': queryset.exists()
        })
