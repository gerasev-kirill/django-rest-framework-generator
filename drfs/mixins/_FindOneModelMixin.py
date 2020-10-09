from rest_framework.response import Response

from django.http import Http404
from drfs.decorators import action




class FindOneModelMixin(object):

    @action(methods=['get'], detail=False)
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
            serializer = self.get_serializer(queryset[0])
            return Response(serializer.data)
        except IndexError:
            raise Http404()
