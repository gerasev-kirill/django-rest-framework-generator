from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response






class CountModelMixin(object):

    @list_route(methods=['get'])
    def count(self, request, *args, **kwargs):
        """
        Count instances of the model matched by where from the data source
        ---
        omit_serializer: true
        type:
          count:
            required: true
            type: number
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response({'count':queryset.count()})
