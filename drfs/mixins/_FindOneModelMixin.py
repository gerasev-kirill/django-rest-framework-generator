from rest_framework.response import Response

from django.http import Http404
from drfs.decorators import action




class FindOneModelMixin(object):

    @action(methods=['get'], detail=False)
    def find_one(self, request, *args, **kwargs):
        """
        Returns first instance of the model matched by filter.where from the data source
        """
        queryset = self.filter_queryset(self.get_queryset())
        item = queryset.first()
        if not item:
            raise Http404()

        serializer = self.get_serializer(item)
        return Response(serializer.data)