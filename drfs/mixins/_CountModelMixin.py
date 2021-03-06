from rest_framework.response import Response

from drfs.decorators import action





class CountModelMixin(object):

    @action(methods=['get'], detail=False)
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
        return Response({'count':queryset.count()})
