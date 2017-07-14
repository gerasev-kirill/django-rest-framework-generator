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
        parameters:
            - name: where
              description: Criteria to match model instances. <a target="_blank" href="https://loopback.io/doc/en/lb2/Where-filter.html">Docs here</a> and <a target="_blank" href="https://loopback.io/doc/en/lb2/Querying-data.html#using-stringified-json-in-rest-queries">here</a>
              required: false
              type: objects
              paramType: query
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response(queryset.count())
