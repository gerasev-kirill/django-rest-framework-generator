from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from django.http import Http404




class FindOneModelMixin(object):

    @list_route(methods=['get'])
    def find_one(self, request, *args, **kwargs):
        """
        Returns first instance of the model matched by filter.where from the data source
        ---
        parameters:
            - name: filter
              description: Filter defining fields, where, order, skip, and limit. <a target="_blank" href="https://loopback.io/doc/en/lb2/Querying-data.html#using-stringified-json-in-rest-queries">Docs here</a>
              required: false
              type: objects
              paramType: query
        """
        queryset = self.filter_queryset(self.get_queryset())
        try:
            serializer = self.serializer_class(queryset[0])
            return Response(serializer.data)
        except IndexError:
            raise Http404()
