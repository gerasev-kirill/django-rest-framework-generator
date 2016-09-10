from rest_framework.decorators import list_route
from rest_framework.response import Response






class QuerysetExistsModelMixin(object):

    @list_route(methods=['get'], url_path='querysetExists')
    def queryset_exists(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({
            'exists': queryset.exists()
        })
