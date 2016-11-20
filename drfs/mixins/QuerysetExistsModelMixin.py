from rest_framework.decorators import list_route
from rest_framework.response import Response






class QuerysetExistsModelMixin(object):

    @list_route(methods=['get'])
    def queryset_exists(self, request, *args, **kwargs):
        """
        Check whether a model instance exists in the data source
        ---
        omit_serializer: true
        type:
          exists:
            required: true
            type: boolean
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'exists': queryset.exists()
        })
