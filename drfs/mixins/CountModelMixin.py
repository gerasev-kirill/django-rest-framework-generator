from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response






class CountModelMixin(object):

    @list_route(methods=['get'])
    def count(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response({'count':queryset.count()})
